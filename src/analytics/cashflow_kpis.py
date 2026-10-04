def free_cash_flow(operating_activity, investing_activity):
    return (operating_activity or 0) + (investing_activity or 0)

def cfo_quality_score(cfo_pat_ratios):
    # cfo_pat_ratios is a list of (cfo / pat) for the last 5 years
    if not cfo_pat_ratios:
        return None, "INSUFFICIENT"
    
    avg_ratio = sum(cfo_pat_ratios) / len(cfo_pat_ratios)
    if avg_ratio > 1.0:
        return avg_ratio, "High Quality"
    elif 0.5 <= avg_ratio <= 1.0:
        return avg_ratio, "Moderate"
    else:
        return avg_ratio, "Accrual Risk"

def capex_intensity(investing_activity, sales):
    if not sales or sales == 0:
        return None, None
    
    intensity = (abs(investing_activity or 0) / sales) * 100
    if intensity < 3:
        label = "Asset Light"
    elif 3 <= intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
        
    return intensity, label

def fcf_conversion_rate(fcf, operating_profit):
    if not operating_profit or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100

def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio=None):
    cfo_sign = '+' if (cfo or 0) > 0 else '-'
    cfi_sign = '+' if (cfi or 0) > 0 else '-'
    cff_sign = '+' if (cff or 0) > 0 else '-'
    
    pattern = (cfo_sign, cfi_sign, cff_sign)
    
    if pattern == ('+', '-', '-'):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return pattern, "Shareholder Returns"
        else:
            return pattern, "Reinvestor"
    elif pattern == ('+', '+', '-'):
        return pattern, "Liquidating Assets"
    elif pattern == ('-', '+', '+'):
        return pattern, "Distress Signal"
    elif pattern == ('-', '-', '+'):
        return pattern, "Growth Funded by Debt"
    elif pattern == ('+', '+', '+'):
        return pattern, "Cash Accumulator"
    elif pattern == ('-', '-', '-'):
        return pattern, "Pre-Revenue"
    elif pattern == ('+', '-', '+'):
        return pattern, "Mixed"
    else:
        return pattern, "Unknown"
