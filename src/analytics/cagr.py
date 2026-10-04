def calculate_cagr(start_value, end_value, periods):
    if periods <= 0:
        return None, "INSUFFICIENT"
        
    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"
        
    if start_value == 0:
        return None, "ZERO_BASE"
        
    if start_value > 0 and end_value > 0:
        cagr = ((end_value / start_value) ** (1 / periods) - 1) * 100
        return cagr, "NORMAL"
        
    if start_value > 0 and end_value <= 0:
        return None, "DECLINE_TO_LOSS"
        
    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"
        
    if start_value < 0 and end_value <= 0:
        return None, "BOTH_NEGATIVE"
        
    return None, "UNKNOWN"

def compute_all_cagrs(data_series, years=[3, 5, 10]):
    # data_series should be a dictionary mapping year to value, or a sorted list of (year, value)
    results = {}
    if not data_series:
        for y in years:
            results[f'{y}yr'] = (None, "INSUFFICIENT")
        return results
        
    sorted_years = sorted(data_series.keys())
    latest_year = sorted_years[-1]
    latest_value = data_series[latest_year]
    
    for y in years:
        target_year = latest_year - y
        if target_year in data_series:
            start_value = data_series[target_year]
            cagr_val, flag = calculate_cagr(start_value, latest_value, y)
            results[f'{y}yr'] = (cagr_val, flag)
        else:
            results[f'{y}yr'] = (None, "INSUFFICIENT")
            
    return results
