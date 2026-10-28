import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime


class ValidationError(ValueError):
    pass


def validate_amount(amount):
    # Reject booleans explicitly
    if isinstance(amount, bool):
        raise ValidationError("Amount must be a valid number.")
    
    # Check for float NaN/infinity
    if isinstance(amount, float):
        if math.isnan(amount) or math.isinf(amount):
            raise ValidationError("Amount must be a valid number.")
        # Check decimal precision of float representation
        # Look for decimals beyond 2
        s_precise = f"{amount:.10f}".rstrip('0')
        if '.' in s_precise:
            dpart = s_precise.split('.')[-1]
            if len(dpart) > 2:
                raise ValidationError("Amount must have no more than two decimal places.")
    
    # Check decimal string precision
    if isinstance(amount, str):
        s = amount.strip()
        if s == '':
            raise ValidationError("Amount must be a valid number.")
        if 'e' in s.lower():
            raise ValidationError("Amount must be a valid number.")
        if '.' in s:
            decimal_part = s.split('.')[-1]
            if len(decimal_part) > 2:
                raise ValidationError("Amount must have no more than two decimal places.")
    
    # Convert using Decimal for precision
    try:
        if isinstance(amount, Decimal):
            d = amount
        else:
            d = Decimal(str(amount))
    except Exception:
        raise ValidationError("Amount must be a valid number.")
    
    if not d.is_finite():
        raise ValidationError("Amount must be a valid number.")
    
    if d <= 0:
        raise ValidationError("Amount must be greater than zero.")
    
    if d > Decimal('999999.99'):
        raise ValidationError("Amount exceeds the maximum allowed value.")
    
    rounded = d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)


def validate_category(category):
    if not isinstance(category, str):
        raise ValidationError("Category must be text.")
    category_clean = category.strip()
    if not category_clean:
        raise ValidationError("Category cannot be empty.")
    if len(category_clean) > 50:
        raise ValidationError("Category cannot exceed 50 characters.")
    return category_clean.title()


def validate_description(description):
    if description is None:
        return ""
    if not isinstance(description, str):
        raise ValidationError("Description must be text.")
    description_clean = description.strip()
    if len(description_clean) > 500:
        raise ValidationError("Description cannot exceed 500 characters.")
    return description_clean


def validate_expense_date(expense_date):
    if not isinstance(expense_date, str):
        raise ValidationError("Date must use YYYY-MM-DD format.")
    expense_date_clean = expense_date.strip()
    try:
        parsed_date = datetime.strptime(expense_date_clean, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date must be a valid date in YYYY-MM-DD format.")
    if parsed_date.isoformat() != expense_date_clean:
        raise ValidationError("Date must use the exact YYYY-MM-DD format.")
    return expense_date_clean


def validate_expense_id(expense_id):
    if isinstance(expense_id, bool):
        raise ValidationError("Expense ID must be a positive integer.")
    if not isinstance(expense_id, int) or isinstance(expense_id, bool):
        raise ValidationError("Expense ID must be a positive integer.")
    if expense_id <= 0:
        raise ValidationError("Expense ID must be greater than zero.")
    return expense_id


def validate_year_month(year, month):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValidationError("Year must be an integer.")
    if not 1 <= year <= 9999:
        raise ValidationError("Year must be between 1 and 9999.")
    if isinstance(month, bool) or not isinstance(month, int):
        raise ValidationError("Month must be an integer.")
    if not 1 <= month <= 12:
        raise ValidationError("Month must be between 1 and 12.")
    return f"{year:04d}-{month:02d}"


def validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValidationError("Limit must be an integer.")
    if limit < 0:
        raise ValidationError("Limit cannot be negative.")
    if limit > 10000:
        raise ValidationError("Limit cannot exceed 10000.")
    return limit
