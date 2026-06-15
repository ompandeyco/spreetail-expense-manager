import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from users.models import User
from groups.models import ExpenseGroup, Membership
from expenses.models import Expense
from settlements.models import Settlement
from .models import ImportIssue

class ImportService:
    """
    Handles parsing, validating, and importing expenses from CSV.
    Design decisions:
    - Never crash: We use try/except extensively and default values.
    - Never silently fix: All modifications (like case fixing or formatting) spawn an ImportIssue.
    - Modular checks: Each anomaly rule is isolated into helper methods for easier interviewing and testing.
    """

    def __init__(self, file_obj, group_id, uploaded_by):
        self.file_obj = file_obj
        self.group_id = group_id
        self.uploaded_by = uploaded_by
        self.group = ExpenseGroup.objects.filter(id=group_id).first()
        
        self.total_rows = 0
        self.imported_count = 0
        self.issues_report = []

    def process(self):
        # Read the file directly into memory since CSVs for expenses are typically small
        decoded_file = self.file_obj.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded_file))
        
        for row_number, row in enumerate(reader, start=1):
            self.total_rows += 1
            # Lowercase keys to handle header case inconsistencies
            row = {k.strip().lower(): v for k, v in row.items() if k}
            self.process_row(row, row_number)
            
        return {
            "total_rows": self.total_rows,
            "imported": self.imported_count,
            "issues": self.issues_report
        }

    def process_row(self, row, row_number):
        issues = []
        
        # 1. Parse and validate base fields
        date_obj = self.validate_date(row.get('date'), row_number, issues)
        amount_val = self.validate_amount(row.get('amount'), row_number, issues)
        payer_user = self.validate_payer(row.get('payer'), row_number, issues)
        currency = self.validate_currency(row.get('currency'), row_number, issues)
        description = row.get('description', '').strip()
        
        # If core fields are unparseable, skip saving Expense
        if not all([date_obj, payer_user, description]) or amount_val is None:
            self.record_issue(row_number, "Missing required fields", str(row), "Provide valid date, payer, amount, and description", "failed")
            return
            
        # 6. USD currency conversion
        exchange_rate = Decimal('1.0')
        converted_amount = amount_val
        if currency != 'USD':
            exchange_rate = self.get_exchange_rate(currency)
            converted_amount = amount_val * exchange_rate
            self.record_issue(row_number, "Currency Conversion", str(amount_val), f"Converted {currency} to USD at rate {exchange_rate}", "info", issues)

        # 9. Settlement written as expense
        if self.is_settlement(description):
            self.handle_settlement(row, row_number, payer_user, amount_val, issues)
            return

        # 7. & 8. Negative and Zero amounts
        if amount_val < 0:
            self.record_issue(row_number, "Negative Amount", str(amount_val), "Treating as refund, preserving record", "info", issues)
        elif amount_val == 0:
            self.record_issue(row_number, "Zero Amount", "0", "Flagged for manual review", "pending", issues)
            self.save_issues(issues)
            return

        # 1. & 2. Duplicates
        if self.check_duplicates(description, amount_val, date_obj, payer_user, row_number, issues):
            self.save_issues(issues)
            return
            
        # 13. Expense date outside membership period
        self.check_membership_dates(payer_user, date_obj, row_number, issues)

        # 12. Percentage split validation
        if not self.validate_splits(row.get('splits'), row_number, issues):
            self.save_issues(issues)
            return

        # Create Expense if no blocking errors
        has_blocking = any(i['status'] in ['failed', 'pending'] for i in issues)
        if not has_blocking and self.group:
            Expense.objects.create(
                group=self.group,
                description=description,
                paid_by=payer_user,
                amount=amount_val,
                currency=currency,
                exchange_rate=exchange_rate,
                converted_amount=converted_amount,
                expense_date=date_obj,
                status='active'
            )
            self.imported_count += 1
            
        # Save all generated issues for this row to DB and report list
        self.save_issues(issues)

    def record_issue(self, row_number, issue_type, original_value, action, status, issues_list=None):
        issue_data = {
            "row": row_number,
            "problem": issue_type,
            "action": action,
            "original_value": str(original_value)[:200],  # truncate if too long
            "status": status
        }
        if issues_list is not None:
            issues_list.append(issue_data)
        else:
            self.save_issues([issue_data])

    # --- Anomaly Detectors & Validators ---

    def validate_date(self, date_str, row_num, issues):
        if not date_str:
            self.record_issue(row_num, "Missing Date", "", "Row rejected", "failed", issues)
            return None
            
        # 10. Invalid or multiple date formats
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt).date()
                if fmt != '%Y-%m-%d':
                    self.record_issue(row_num, "Non-standard Date Format", date_str, f"Standardized to YYYY-MM-DD", "info", issues)
                return dt
            except ValueError:
                continue
                
        self.record_issue(row_num, "Invalid Date Format", date_str, "Row rejected", "failed", issues)
        return None

    def validate_amount(self, amount_str, row_num, issues):
        if not amount_str:
            self.record_issue(row_num, "Missing Amount", "", "Row rejected", "failed", issues)
            return None
            
        # 3. Amount formatting problems
        clean_amount = amount_str.replace('"', '')
        if ',' in clean_amount or '$' in clean_amount or '€' in clean_amount:
            clean_amount = clean_amount.replace(',', '').replace('$', '').replace('€', '').strip()
            self.record_issue(row_num, "Amount Formatting", amount_str, f"Cleaned symbols, parsed as {clean_amount}", "info", issues)
            
        try:
            return Decimal(clean_amount)
        except InvalidOperation:
            self.record_issue(row_num, "Invalid Amount", amount_str, "Could not convert to number", "failed", issues)
            return None

    def validate_payer(self, payer_str, row_num, issues):
        # 4. Missing payer
        if not payer_str:
            self.record_issue(row_num, "Missing Payer", "", "Row rejected", "failed", issues)
            return None
            
        payer_str = payer_str.strip()
        user = User.objects.filter(username=payer_str).first()
        if user:
            return user
            
        # 11. User name inconsistencies
        user_case = User.objects.filter(username__iexact=payer_str).first()
        if user_case:
            self.record_issue(row_num, "User Name Case Mismatch", payer_str, f"Auto-matched to {user_case.username}", "info", issues)
            return user_case
            
        user_partial = User.objects.filter(username__icontains=payer_str).first()
        if user_partial:
            self.record_issue(row_num, "Partial User Name Match", payer_str, f"Fuzzy matched to {user_partial.username}", "pending", issues)
            return user_partial
            
        self.record_issue(row_num, "Payer Not Found", payer_str, "Ensure user exists", "failed", issues)
        return None

    def validate_currency(self, currency_str, row_num, issues):
        # 5. Missing currency
        if not currency_str:
            self.record_issue(row_num, "Missing Currency", "", "Defaulted to USD", "info", issues)
            return 'USD'
        return currency_str.strip().upper()

    def is_settlement(self, description):
        desc = description.lower()
        return any(phrase in desc for phrase in ['paid back', 'settlement', 'settled'])

    def handle_settlement(self, row, row_num, payer_user, amount_val, issues):
        # 9. Create Settlement instead
        # Assuming the uploaded_by is the receiver if not specified in CSV
        to_user = self.uploaded_by
        self.record_issue(row_num, "Interpreted as Settlement", row.get('description'), "Created Settlement record instead of Expense", "info", issues)
        
        Settlement.objects.create(
            from_user=payer_user,
            to_user=to_user,
            amount=abs(amount_val)
        )
        self.imported_count += 1
        self.save_issues(issues)

    def check_duplicates(self, description, amount, date_obj, payer_user, row_num, issues):
        if not self.group: return False
        
        possible_dupes = Expense.objects.filter(
            group=self.group,
            expense_date=date_obj,
            paid_by=payer_user
        )
        
        for exp in possible_dupes:
            desc1 = description.lower()
            desc2 = exp.description.lower()
            # Simple similarity: substring match
            if desc1 in desc2 or desc2 in desc1:
                if exp.amount == amount:
                    self.record_issue(row_num, "Duplicate Expense", description, "Exact duplicate skipped", "failed", issues)
                    return True
                else:
                    self.record_issue(row_num, "Conflicting Duplicate", f"Amt: {amount}", f"Similar to '{exp.description}' but different amount. Flagged for review.", "pending", issues)
                    return True
        return False

    def check_membership_dates(self, user, date_obj, row_num, issues):
        if not self.group or not user: return
        membership = Membership.objects.filter(group=self.group, user=user).first()
        if membership:
            if membership.joined_at.date() > date_obj:
                self.record_issue(row_num, "Date Outside Membership", str(date_obj), "Expense date is before user joined. Flagged.", "pending", issues)
            if membership.left_at and membership.left_at.date() < date_obj:
                self.record_issue(row_num, "Date Outside Membership", str(date_obj), "Expense date is after user left. Flagged.", "pending", issues)

    def validate_splits(self, splits_str, row_num, issues):
        # 12. Percentage split validation
        if not splits_str: 
            return True
        if 'percentage' in splits_str.lower() or '%' in splits_str:
            numbers = [int(n) for n in re.findall(r'\d+', splits_str)]
            if numbers and sum(numbers) != 100:
                self.record_issue(row_num, "Invalid Percentage Split", splits_str, "Percentages do not sum to 100", "failed", issues)
                return False
        return True

    def get_exchange_rate(self, currency):
        # Mock configurable exchange rates for simplicity
        rates = {'EUR': Decimal('1.10'), 'GBP': Decimal('1.25'), 'INR': Decimal('0.012')}
        return rates.get(currency, Decimal('1.0'))

    def save_issues(self, issues):
        for i in issues:
            ImportIssue.objects.create(
                row_number=i['row'],
                issue_type=i['problem'],
                original_value=i['original_value'],
                suggested_action=i['action'],
                status=i['status']
            )
            # Remove full status from final output format as per requirement, but keep it in DB
            self.issues_report.append({
                "row": i['row'],
                "problem": i['problem'],
                "action": i['action']
            })
