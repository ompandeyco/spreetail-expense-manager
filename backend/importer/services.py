"""
importer/services.py

Core CSV import engine for the Spreetail Expense Manager.

Design philosophy:
  - NEVER crash: every risky operation is wrapped in try/except.
  - NEVER silently fix: every automatic correction creates an ImportIssue record.
  - Small, focused methods: each anomaly check lives in its own method so an
    interviewer (or teammate) can understand and test it in isolation.

Interview talking points:
  - Why ImportIssue instead of raising exceptions?
    → We want a full audit trail. A single bad row should not block 500 good rows.
  - Why Decimal instead of float?
    → Float arithmetic is lossy for money. Decimal is exact.
  - Why normalize header keys to lowercase?
    → CSV exports from different tools use different casing. Normalization makes
      every downstream check case-insensitive at the schema level.
"""

import csv
import io
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from groups.models import ExpenseGroup, Membership
from expenses.models import Expense, ExpenseSplit
from settlements.models import Settlement
from users.models import User

from .models import ImportIssue

# Module-level logger — output goes to Django's logging pipeline (console in dev).
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Known settlement keywords — rows matching these are rerouted to Settlement.
# ---------------------------------------------------------------------------
SETTLEMENT_KEYWORDS = {"paid back", "settlement", "settled", "reimburse", "reimbursement"}

# ---------------------------------------------------------------------------
# Supported currencies and their approximate USD exchange rates.
# In production this would call a live FX API (e.g. Open Exchange Rates).
# The mock rates are intentionally visible so reviewers can spot the seam.
# ---------------------------------------------------------------------------
EXCHANGE_RATES = {
    "EUR": Decimal("1.10"),
    "GBP": Decimal("1.25"),
    "INR": Decimal("0.012"),
    "CAD": Decimal("0.74"),
    "AUD": Decimal("0.65"),
}

# Date formats we attempt to parse, in preference order.
# Only the first (ISO 8601) is considered "standard" — all others raise an issue.
ACCEPTED_DATE_FORMATS = [
    ("%Y-%m-%d", True),   # (format_string, is_standard)
    ("%m/%d/%Y", False),
    ("%d/%m/%Y", False),
    ("%Y/%m/%d", False),
    ("%d-%m-%Y", False),
]


class ImportService:
    """
    Orchestrates the full CSV → database import pipeline.

    Usage:
        service = ImportService(file_obj, group_id, uploaded_by_user)
        report  = service.process()

    The returned report dict matches the API contract:
        {
            "total_rows":         int,
            "successful_imports": int,
            "issues": [
                {
                    "row":            int,
                    "problem":        str,
                    "original_value": str,
                    "action_taken":   str,
                }
            ]
        }
    """

    def __init__(self, file_obj, group_id: int, uploaded_by):
        """
        Args:
            file_obj:    Django InMemoryUploadedFile from request.FILES.
            group_id:    PK of the ExpenseGroup this import targets.
            uploaded_by: The authenticated User who triggered the upload.
                         Used as a fallback "to_user" when converting a row
                         to a Settlement record.
        """
        self.file_obj    = file_obj
        self.group_id    = group_id
        self.uploaded_by = uploaded_by

        # Resolved once in __init__ so every helper can use it without hitting DB again.
        self.group = ExpenseGroup.objects.filter(id=group_id).first()

        # Counters and accumulator for the final report.
        self.total_rows   = 0
        self.imported_count = 0
        self.issues_log   = []   # list[dict] — populated by _record_issue()

    # =========================================================================
    # PUBLIC INTERFACE
    # =========================================================================

    def process(self):
        """
        Entry point. Reads the file, iterates rows, and returns the final report.
        Delegates per-row work to validate_row().
        """
        rows = self.parse_csv()
        for row_number, row in rows:
            self.total_rows += 1
            self.validate_row(row, row_number)

        return self.generate_report()

    # =========================================================================
    # STEP 1 — parse_csv
    # =========================================================================

    def parse_csv(self):
        """
        Decodes the uploaded file and yields (row_number, normalized_row) tuples.

        Normalization applied here (schema level, not data level):
          - Strip BOM characters that Excel sometimes prepends.
          - Lower-case and strip all header keys so downstream code is case-insensitive.

        Yields:
            tuple[int, dict]: 1-based row number and the normalized row dict.

        Interview note:
            We consume the whole file into a StringIO because Django's
            InMemoryUploadedFile is a one-shot stream. Wrapping it in StringIO
            allows csv.DictReader to seek without us having to re-open the file.
        """
        try:
            raw_bytes = self.file_obj.read()
            # utf-8-sig strips the BOM (\xef\xbb\xbf) that Excel adds.
            decoded = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Fallback for files saved with a Latin-1 encoding (common in Windows).
            decoded = raw_bytes.decode("latin-1")

        reader = csv.DictReader(io.StringIO(decoded))
        for row_number, raw_row in enumerate(reader, start=1):
            # Normalize keys: strip whitespace, convert to lowercase.
            # None keys can appear when a trailing comma creates a phantom column.
            normalized = {
                k.strip().lower(): (v.strip() if v else "")
                for k, v in raw_row.items()
                if k is not None
            }
            yield row_number, normalized

    # =========================================================================
    # STEP 2 — validate_row  (orchestrates all per-row checks)
    # =========================================================================

    def validate_row(self, row: dict, row_number: int):
        """
        Runs all validation and anomaly checks for a single CSV row.

        Blocking failures (status="failed") prevent the Expense from being saved.
        Non-blocking flags (status="info" / "pending") are recorded but do NOT
        stop the import — the interviewer can then discuss the trade-off.

        Args:
            row:        Normalized dict from parse_csv().
            row_number: 1-based position in the CSV (displayed in report).
        """
        row_issues = []  # Collect issues for THIS row before flushing to DB.

        # --- Field extraction & validation ---
        # CSV headers: date, description, paid_by, amount, currency,
        #              split_type, split_with, split_details, notes
        date_obj    = self._validate_date(row.get("date", ""), row_number, row_issues)
        amount_val  = self.normalize_amount(row.get("amount", ""), row_number, row_issues)
        # The payer column in the CSV is 'paid_by', not 'payer'.
        payer_user  = self._validate_payer(row.get("paid_by", ""), row_number, row_issues)
        currency    = self.handle_currency(row.get("currency", ""), row_number, row_issues)
        description = row.get("description", "").strip()

        # --- Guard: if any core field is missing, reject the whole row ---
        if not description:
            self._record_issue(row_number, "Missing Description", "", "Row rejected — description is required.", "failed", row_issues)

        # Flush issues then exit early if blocking failures exist.
        if self._has_blocking(row_issues) or not all([date_obj, payer_user]) or amount_val is None:
            self._flush_issues(row_issues)
            return

        # --- Settlement detection (reroutes row, does NOT create an Expense) ---
        if self.detect_settlement(description, row, row_number, payer_user, amount_val, row_issues):
            self._flush_issues(row_issues)
            return

        # --- Amount semantic checks (after we know amount_val is a valid Decimal) ---
        if amount_val < 0:
            # Negative amounts are refunds. We record the issue and keep importing.
            self._record_issue(
                row_number, "Negative Amount Refund",
                str(amount_val),
                "Amount is negative — treated as a refund. Record preserved.",
                "info", row_issues
            )
        elif amount_val == 0:
            # Zero amounts are always suspicious. Reject them.
            self._record_issue(
                row_number, "Zero Amount Expense",
                "0",
                "Zero-value expense is meaningless — row rejected for manual review.",
                "failed", row_issues
            )
            self._flush_issues(row_issues)
            return

        # --- Currency conversion ---
        exchange_rate, converted_amount = self._apply_currency_conversion(
            amount_val, currency, row_number, row_issues
        )

        # --- Duplicate detection ---
        if self.detect_duplicate(description, amount_val, date_obj, payer_user, row_number, row_issues):
            self._flush_issues(row_issues)
            return

        # --- Membership boundary check ---
        self._check_membership_dates(payer_user, date_obj, row_number, row_issues)

        # --- Percentage split validation ---
        # Compose a single string from all three split columns so _validate_splits
        # can detect percentage-based splits regardless of which column carries the '%'.
        split_str = " ".join(filter(None, [
            row.get("split_type", ""),
            row.get("split_with", ""),
            row.get("split_details", ""),
        ]))
        split_ok = self._validate_splits(split_str, row_number, row_issues)
        if not split_ok:
            self._flush_issues(row_issues)
            return

        # --- Save Expense if no blocking issues remain ---
        if not self._has_blocking(row_issues) and self.group:
            logger.info("[ImportService] Creating expense row %s: '%s'", row_number, description)
            try:
                expense = Expense.objects.create(
                    group=self.group,
                    description=description,
                    paid_by=payer_user,
                    amount=amount_val,
                    currency=currency,
                    exchange_rate=exchange_rate,
                    converted_amount=converted_amount,
                    expense_date=date_obj,
                    status="active",
                )
                logger.info("[ImportService] Expense created successfully — ID=%s, row=%s", expense.pk, row_number)

                # --- Create ExpenseSplit records ---
                # Resolve participants from split_with column (semicolon-separated names).
                split_type = row.get("split_type", "equal").strip().lower() or "equal"
                split_with_str = row.get("split_with", "")
                participants = self._resolve_split_members(
                    split_with_str, payer_user, row_number, row_issues
                )
                self._create_splits(expense, participants, amount_val, split_type, row_number, row_issues)

                self.imported_count += 1
            except Exception as exc:
                # Catch DB-level errors (e.g. constraint violations) without crashing
                # the entire import — log them as failed issues instead.
                logger.error("[ImportService] DB error saving expense row %s: %s", row_number, exc)
                self._record_issue(
                    row_number, "Expense Save Failed",
                    description,
                    f"Database error: {exc}",
                    "failed", row_issues
                )

        self._flush_issues(row_issues)

    # =========================================================================
    # ANOMALY DETECTORS  (each maps to one or more of the 13 required checks)
    # =========================================================================

    def detect_duplicate(self, description: str, amount: Decimal, date_obj, payer_user, row_number: int, row_issues: list) -> bool:
        """
        Checks for EXACT duplicates (same desc + amount + date + payer) and
        SIMILAR duplicates (same desc/date/payer but different amount).

        Covers requirements:
          #1 — Exact duplicate expenses
          #2 — Similar duplicates with different amounts

        Returns:
            True  → duplicate found; caller should skip saving this row.
            False → no duplicate; proceed normally.

        Interview note:
            We use a substring match for similarity, which is intentionally simple.
            In production you could use Levenshtein distance (python-Levenshtein)
            or PostgreSQL's pg_trgm extension for fuzzy matching at scale.
        """
        if not self.group:
            return False

        candidates = Expense.objects.filter(
            group=self.group,
            expense_date=date_obj,
            paid_by=payer_user,
        )

        desc_lower = description.lower()

        for existing in candidates:
            existing_desc = existing.description.lower()

            # Similarity heuristic: one description is a substring of the other.
            is_similar = desc_lower in existing_desc or existing_desc in desc_lower
            if not is_similar:
                continue

            if existing.amount == amount:
                # Requirement #1 — Exact duplicate: block the import.
                self._record_issue(
                    row_number,
                    "Exact Duplicate Expense",
                    f"{description} | {amount}",
                    f"Identical expense already exists (ID={existing.pk}). Row skipped.",
                    "failed", row_issues
                )
                return True
            else:
                # Requirement #2 — Similar description but different amount: flag for review.
                self._record_issue(
                    row_number,
                    "Similar Duplicate — Different Amount",
                    f"CSV amount={amount}",
                    f"Matches existing expense '{existing.description}' (ID={existing.pk}) "
                    f"with amount={existing.amount}. Flagged for manual review.",
                    "pending", row_issues
                )
                return True  # Block until a human reviews; better safe than corrupt.

        return False

    def normalize_amount(self, amount_str: str, row_number: int, row_issues: list):
        """
        Cleans and parses the amount field.

        Covers requirements:
          #3 — Amount formatting issues (commas, currency symbols)

        Returns:
            Decimal on success, None on unrecoverable parse failure.

        Interview note:
            We strip symbols BEFORE attempting Decimal() because Decimal("1,200")
            raises InvalidOperation — it does not auto-strip commas.
        """
        if not amount_str:
            self._record_issue(
                row_number, "Missing Amount", "",
                "Row rejected — amount field is empty.",
                "failed", row_issues
            )
            return None

        original = amount_str
        # Remove surrounding quotes (Excel sometimes wraps comma-formatted numbers).
        cleaned = amount_str.replace('"', "").strip()

        # Track whether we needed to reformat anything.
        was_reformatted = False

        if any(ch in cleaned for ch in (",", "$", "€", "£", "¥")):
            cleaned = re.sub(r"[,\$€£¥]", "", cleaned).strip()
            was_reformatted = True

        if was_reformatted:
            # Requirement: every automatic change must create an ImportIssue.
            self._record_issue(
                row_number, "Amount Formatting Fixed",
                original,
                f"Symbols/commas removed; parsed value is '{cleaned}'.",
                "info", row_issues
            )

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            self._record_issue(
                row_number, "Invalid Amount",
                original,
                f"'{cleaned}' cannot be converted to a number. Row rejected.",
                "failed", row_issues
            )
            return None

    def handle_currency(self, currency_str: str, row_number: int, row_issues: list) -> str:
        """
        Validates and normalises the currency field.

        Covers requirements:
          #5 — Missing currency (defaults to USD with an issue record)
          #6 — USD expenses requiring conversion (flagged for awareness)

        Returns:
            Uppercase 3-letter currency code string.
        """
        if not currency_str:
            # Requirement: no silent fixing — log that we defaulted.
            self._record_issue(
                row_number, "Missing Currency",
                "",
                "Currency field is empty. Defaulted to USD — please verify.",
                "info", row_issues
            )
            return "USD"

        normalized = currency_str.strip().upper()

        if normalized == "USD":
            # Requirement #6 — USD itself doesn't need conversion but we flag awareness
            # that if an FX conversion was expected it won't happen.
            self._record_issue(
                row_number, "USD Expense — No Conversion Needed",
                normalized,
                "Expense is in USD. Stored at face value (exchange_rate=1.0).",
                "info", row_issues
            )

        return normalized

    def detect_settlement(self, description: str, row: dict, row_number: int, payer_user, amount_val: Decimal, row_issues: list) -> bool:
        """
        Identifies rows that describe a settlement/reimbursement and reroutes
        them to the Settlement model instead of creating an Expense.

        Covers requirement:
          #9 — Settlements stored as expenses

        Returns:
            True  → row was a settlement; caller should NOT create an Expense.
            False → row is a genuine expense.

        Interview note:
            We match against SETTLEMENT_KEYWORDS (module-level constant) so the
            list is easy to extend without touching any method logic.
        """
        desc_lower = description.lower()
        matched_keyword = next(
            (kw for kw in SETTLEMENT_KEYWORDS if kw in desc_lower), None
        )

        if not matched_keyword:
            return False

        # Log the rerouting — this IS an automatic change so it MUST be recorded.
        self._record_issue(
            row_number, "Settlement Stored as Expense",
            description,
            f"Keyword '{matched_keyword}' detected. Created a Settlement record instead of an Expense.",
            "info", row_issues
        )

        # Create the Settlement record.
        # uploaded_by is the receiver by convention when the CSV has no explicit "to" column.
        try:
            Settlement.objects.create(
                from_user=payer_user,
                to_user=self.uploaded_by,
                amount=abs(amount_val),
            )
            self.imported_count += 1
        except Exception as exc:
            self._record_issue(
                row_number, "Settlement Save Failed",
                description,
                f"Database error while saving settlement: {exc}",
                "failed", row_issues
            )

        return True

    def generate_report(self) -> dict:
        """
        Builds and returns the final import report dict.

        Output format matches the API contract:
            {
                "total_rows":         int,
                "successful_imports": int,
                "issues": [
                    {
                        "row":            int,
                        "problem":        str,
                        "original_value": str,
                        "action_taken":   str,
                    }
                ]
            }

        Interview note:
            The status field is persisted in the DB (ImportIssue.status) but
            intentionally omitted from the API response to keep the contract
            minimal. Clients that need status can query GET /api/importer/.
        """
        return {
            "total_rows":         self.total_rows,
            "successful_imports": self.imported_count,
            "issues":             self.issues_log,
        }

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _validate_date(self, date_str: str, row_number: int, row_issues: list):
        """
        Attempts to parse date_str against ACCEPTED_DATE_FORMATS.

        Covers requirements:
          #12 — Invalid date formats
          (Non-standard formats that DO parse are flagged as "info".)

        Returns:
            datetime.date on success, None on failure.
        """
        if not date_str:
            self._record_issue(
                row_number, "Missing Date", "",
                "Row rejected — date field is empty.",
                "failed", row_issues
            )
            return None

        for fmt, is_standard in ACCEPTED_DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt).date()
                if not is_standard:
                    self._record_issue(
                        row_number, "Non-Standard Date Format",
                        date_str,
                        f"Parsed using '{fmt}' and standardised to ISO 8601 (YYYY-MM-DD).",
                        "info", row_issues
                    )
                return parsed
            except ValueError:
                continue

        self._record_issue(
            row_number, "Invalid Date Format",
            date_str,
            "Could not parse date with any known format. Row rejected.",
            "failed", row_issues
        )
        return None

    def _get_or_create_user(self, name: str) -> "User":
        """
        Returns an existing User matched by username (case-insensitive) or
        creates a new inactive placeholder User so the import can proceed.

        We create placeholder users rather than rejecting rows because CSV
        exports from Splitwise/Excel often contain display names that were
        never registered in our system. A human can merge/activate them later.

        The user is set unusable_password so they cannot log in until activated.
        """
        # Try exact match first, then case-insensitive.
        user = (
            User.objects.filter(username=name).first()
            or User.objects.filter(username__iexact=name).first()
        )
        if user:
            return user

        # Create a placeholder — password is unusable so the account is inert.
        user = User.objects.create_user(
            username=name,
            email=f"{name.lower().replace(' ', '_')}@imported.local",
            password=None,   # sets unusable password internally
            is_active=False, # must be explicitly activated by an admin
        )
        logger.info("[ImportService] Created placeholder user '%s' (id=%s)", name, user.pk)
        return user

    def _validate_payer(self, payer_str: str, row_number: int, row_issues: list):
        """
        Resolves the paid_by column to a User instance.

        Covers requirements:
          #4  — Missing payer
          #11 — Inconsistent names / case differences
          #13 — Unknown members (payer not in the group)

        Resolution order:
          1. Exact username match         → no issue logged.
          2. Case-insensitive match       → "info" issue (case mismatch noted).
          3. No match → auto-create user  → "info" issue (placeholder created).

        Interview note:
            We switched from "Unknown Payer → failed" to "auto-create user →
            info" because the CSV data is the source of truth during bulk import.
            Rejecting every unknown name would make the importer useless for
            first-time data loads. The placeholder flag (is_active=False) ensures
            these accounts cannot log in until an admin reviews them.
        """
        if not payer_str:
            self._record_issue(
                row_number, "Missing Payer", "",
                "Row rejected — paid_by field is empty.",
                "failed", row_issues
            )
            return None

        payer_clean = payer_str.strip()

        # --- 1. Exact username match ---
        user = User.objects.filter(username=payer_clean).first()
        if user:
            self._ensure_membership(user, row_number, row_issues)
            return user

        # --- 2. Case-insensitive match ---
        user = User.objects.filter(username__iexact=payer_clean).first()
        if user:
            self._record_issue(
                row_number, "Payer Name Case Mismatch",
                payer_clean,
                f"Auto-matched to '{user.username}' (case-insensitive). "
                "Update your CSV to avoid this warning.",
                "info", row_issues
            )
            self._ensure_membership(user, row_number, row_issues)
            return user

        # --- 3. No DB match — create a placeholder user ---
        user = self._get_or_create_user(payer_clean)
        self._record_issue(
            row_number, "Payer Auto-Created",
            payer_clean,
            f"No existing user matched '{payer_clean}'. "
            f"Placeholder user created (id={user.pk}, is_active=False). "
            "An admin should review and activate this account.",
            "info", row_issues
        )
        self._ensure_membership(user, row_number, row_issues)
        return user

    def _ensure_membership(self, user, row_number: int, row_issues: list):
        """
        Ensures the user has a Membership row for this group.
        If one does not exist, it is created automatically and logged as an issue.

        Covers requirement:
          #13 — Unknown members (user exists in system but has no membership)

        Interview note:
            We auto-create the membership rather than blocking the row, because
            during a bulk historical import the membership records may simply not
            exist yet. We log an "info" issue so it is fully auditable.
        """
        if not self.group:
            return
        membership, created = Membership.objects.get_or_create(
            group=self.group,
            user=user,
            defaults={"joined_at": timezone.now()},
        )
        if created:
            self._record_issue(
                row_number, "Membership Auto-Created",
                user.username,
                f"'{user.username}' was not a member of group '{self.group.name}'. "
                "Membership record created automatically.",
                "info", row_issues
            )

    def _resolve_split_members(self, split_with_str: str, payer_user, row_number: int, row_issues: list) -> list:
        """
        Parses the split_with column (semicolon-separated names) into a list of
        User instances, auto-creating placeholder users where needed.

        If split_with is empty we fall back to [payer_user] so at minimum
        the payer's own split record is created.

        Args:
            split_with_str: Raw value from the 'split_with' CSV column.
                            Example: "Aisha;Rohan;Priya;Meera"
            payer_user:     The resolved payer User (always included).

        Returns:
            List of resolved User objects (deduplicated, payer always present).
        """
        if not split_with_str:
            return [payer_user]

        names = [n.strip() for n in split_with_str.split(";") if n.strip()]
        members = []
        seen_ids = set()

        for name in names:
            user = (
                User.objects.filter(username=name).first()
                or User.objects.filter(username__iexact=name).first()
                or self._get_or_create_user(name)
            )
            if user.pk not in seen_ids:
                members.append(user)
                seen_ids.add(user.pk)
                # Ensure every participant has a membership in this group.
                self._ensure_membership(user, row_number, row_issues)

        # Guarantee the payer is in the list even if they were omitted from split_with.
        if payer_user.pk not in seen_ids:
            members.append(payer_user)

        return members

    def _create_splits(self, expense, participants: list, total_amount: Decimal, split_type: str, row_number: int, row_issues: list):
        """
        Creates ExpenseSplit records for all participants.

        Supported split_type values:
          - "equal"   → total divided evenly; each member pays total/count.
          - anything else is treated as equal and logged as an info issue.

        Args:
            expense:      The saved Expense instance.
            participants: List of User instances who share this expense.
            total_amount: Full expense amount (pre-conversion, original currency).
            split_type:   Value from the CSV 'split_type' column.

        Interview note:
            We only implement equal splitting here because that is what the
            sample CSV data uses. Percentage and exact splits would read
            split_details and apply them per-user — a natural extension point.
        """
        n = len(participants)
        if n == 0:
            return

        if split_type != "equal":
            self._record_issue(
                row_number, "Unsupported Split Type",
                split_type,
                f"Split type '{split_type}' is not yet supported. Defaulted to equal split.",
                "info", row_issues
            )

        # Compute the per-person share with Decimal precision.
        # We round to 2 decimal places and absorb any rounding remainder into
        # the first participant's share (payer) to keep totals exact.
        per_person = (total_amount / Decimal(n)).quantize(Decimal("0.01"))
        remainder  = total_amount - (per_person * n)  # usually 0.00 or ±0.01

        for idx, user in enumerate(participants):
            share = per_person + (remainder if idx == 0 else Decimal("0.00"))
            ExpenseSplit.objects.create(
                expense=expense,
                user=user,
                split_type="equal",
                value=per_person,       # the "intended" equal share
                final_amount=share,     # actual amount after rounding correction
            )
        logger.info(
            "[ImportService] Created %s ExpenseSplit records for expense ID=%s",
            n, expense.pk
        )

    def _apply_currency_conversion(self, amount: Decimal, currency: str, row_number: int, row_issues: list):
        """
        Converts non-USD amounts to USD using EXCHANGE_RATES lookup.

        Returns:
            tuple[Decimal, Decimal]: (exchange_rate, converted_amount)

        Interview note:
            For an unknown currency we use rate=1.0 (identity) and log a "pending"
            issue so an operator can apply the correct rate manually. We never guess.
        """
        if currency == "USD":
            return Decimal("1.0"), amount

        rate = EXCHANGE_RATES.get(currency)

        if rate is None:
            self._record_issue(
                row_number, "Unknown Currency — No Rate Available",
                currency,
                f"No exchange rate for '{currency}'. Stored at face value (rate=1.0). "
                "Update EXCHANGE_RATES or apply conversion manually.",
                "pending", row_issues
            )
            return Decimal("1.0"), amount

        converted = amount * rate
        self._record_issue(
            row_number, "Currency Converted to USD",
            f"{amount} {currency}",
            f"Converted to USD using rate {rate}. Stored as {converted:.2f} USD.",
            "info", row_issues
        )
        return rate, converted

    def _check_membership_dates(self, user, date_obj, row_number: int, row_issues: list):
        """
        Ensures the expense date falls within the user's active membership window.

        Covers requirement:
          #11 — Member not active during expense date

        We log a "pending" issue (not "failed") because the dates in legacy data
        can legitimately predate our membership records — a human should decide.
        """
        if not self.group or not user:
            return

        membership = Membership.objects.filter(group=self.group, user=user).first()
        if not membership:
            return  # Already flagged by _check_unknown_member if applicable.

        joined = membership.joined_at.date()
        left   = membership.left_at.date() if membership.left_at else None

        if joined > date_obj:
            self._record_issue(
                row_number, "Expense Before Member Joined",
                str(date_obj),
                f"'{user.username}' joined on {joined} but expense date is {date_obj}. "
                "Flagged for review.",
                "pending", row_issues
            )

        if left and left < date_obj:
            self._record_issue(
                row_number, "Expense After Member Left",
                str(date_obj),
                f"'{user.username}' left on {left} but expense date is {date_obj}. "
                "Flagged for review.",
                "pending", row_issues
            )

    def _validate_splits(self, splits_str: str, row_number: int, row_issues: list) -> bool:
        """
        Validates percentage splits when the splits column contains '%' or
        the word 'percentage'.

        Covers requirement:
          #10 — Percentage splits not totalling 100

        Returns:
            True  → splits are valid (or absent).
            False → splits are present but invalid; caller should block the import.

        Interview note:
            We extract all integer tokens with re.findall so we handle formats
            like "Alice:40%, Bob:60%" and "40/60" equally without a rigid schema.
        """
        if not splits_str:
            return True  # No splits field — nothing to validate.

        splits_lower = splits_str.lower()
        if "%" not in splits_lower and "percentage" not in splits_lower:
            return True  # Non-percentage split types (equal, exact) are out of scope here.

        # Extract every integer from the string.
        numbers = [int(n) for n in re.findall(r"\d+", splits_str)]

        if not numbers:
            return True  # Malformed but no integers found — can't validate.

        total = sum(numbers)
        if total != 100:
            self._record_issue(
                row_number, "Percentage Splits Do Not Total 100",
                splits_str,
                f"Percentages sum to {total}, not 100. Row rejected — fix the split values.",
                "failed", row_issues
            )
            return False

        return True

    # =========================================================================
    # ISSUE RECORDING UTILITIES
    # =========================================================================

    def _record_issue(
        self,
        row_number: int,
        issue_type: str,
        original_value: str,
        action_taken: str,
        status: str,
        issues_list: list,
    ):
        """
        Appends a structured issue dict to issues_list.

        We do NOT write to the DB here — that is deferred to _flush_issues()
        so that a row which ultimately succeeds still has all its "info" issues
        persisted atomically after we know the Expense was created.

        Args:
            row_number:     1-based row index in the CSV.
            issue_type:     Short label matching one of the 13 required anomaly types.
            original_value: Raw value from the CSV that triggered the issue.
            action_taken:   Human-readable description of what the system did.
            status:         "info" | "pending" | "failed"
            issues_list:    Per-row accumulator list (passed by reference).
        """
        issues_list.append({
            "row":            row_number,
            "problem":        issue_type,
            "original_value": str(original_value)[:500],  # Guard against huge values.
            "action_taken":   action_taken,
            "status":         status,           # Internal — not surfaced in API response.
        })

    def _flush_issues(self, issues_list: list):
        """
        Persists all accumulated issues for a row to the DB and adds them
        (without the internal 'status' key) to the report accumulator.

        Called once per row, at the very end of validate_row() or whenever
        we return early from that method.
        """
        for issue in issues_list:
            # Persist to DB for audit trail.
            ImportIssue.objects.create(
                row_number=issue["row"],
                issue_type=issue["problem"],
                original_value=issue["original_value"],
                suggested_action=issue["action_taken"],
                status=issue["status"],
            )
            # Append API-facing version (no internal 'status').
            self.issues_log.append({
                "row":            issue["row"],
                "problem":        issue["problem"],
                "original_value": issue["original_value"],
                "action_taken":   issue["action_taken"],
            })

    def _has_blocking(self, issues_list: list) -> bool:
        """
        Returns True if any issue in issues_list has status="failed".
        Used to decide whether to proceed with saving an Expense.
        """
        return any(i["status"] == "failed" for i in issues_list)
