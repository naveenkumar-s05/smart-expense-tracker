"""
Financial calculations service.
"""
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import math


class FinancialError(ValueError):
    pass


def money_round(amount):
    # Reject booleans
    if isinstance(amount, bool):
        raise FinancialError("Invalid monetary value.")
    
    # Check for NaN/infinity
    if isinstance(amount, float):
        if math.isnan(amount) or math.isinf(amount):
            raise FinancialError("Invalid monetary value.")
    
    try:
        # Convert via string to avoid float precision issues
        if isinstance(amount, Decimal):
            d = amount
        else:
            d = Decimal(str(amount))
    except Exception:
        raise FinancialError("Invalid monetary value.")
    
    if not d.is_finite():
        raise FinancialError("Invalid monetary value.")
    
    # Quantize to 2 decimal places with ROUND_HALF_UP
    rounded = d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    # Return as float for compatibility, but calculated accurately
    return float(rounded)


def calculate_sum(amounts):
    if amounts is None:
        raise FinancialError("Invalid monetary values.")
    
    try:
        # Check if empty
        if len(amounts) == 0:
            return 0.0
    except TypeError:
        raise FinancialError("Invalid monetary values.")
    
    total = Decimal('0')
    for a in amounts:
        if isinstance(a, bool):
            raise FinancialError("Invalid monetary value.")
        if isinstance(a, float):
            if math.isnan(a) or math.isinf(a):
                raise FinancialError("Invalid monetary value.")
        # For strings, also check precision
        if isinstance(a, str):
            s = a.strip()
            if 'e' in s.lower() or s == '':
                raise FinancialError("Invalid monetary value.")
            if '.' in s:
                dec_part = s.split('.')[-1]
                if len(dec_part) > 2:
                    raise FinancialError("Invalid monetary value.")
        try:
            if isinstance(a, Decimal):
                d = a
            else:
                d = Decimal(str(a))
        except Exception:
            raise FinancialError("Invalid monetary value.")
        if not d.is_finite():
            raise FinancialError("Invalid monetary value.")
        # Also enforce positive as per monetary context? amount must be > 0 in expenses, but sum of values - just validate format
        total += d
    
    rounded = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)
