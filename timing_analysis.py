"""
Timing analysis module for FinCompass plugin.
Contains functions for analyzing optimal sell timing based on AetherOne analysis results.
"""

def analyze_timing_for_symbol(symbol: str, min_hold_minutes: int, max_hold_minutes: int, enhanced_rates: list, hotbits_service) -> dict:
    """
    Analyze optimal sell timing for a specific symbol based on its analysis results.
    
    Args:
        symbol: The cryptocurrency symbol to analyze timing for
        min_hold_minutes: Minimum hold time in minutes
        max_hold_minutes: Maximum hold time in minutes
        enhanced_rates: The analysis results from the main analyze() function
        hotbits_service: HotbitsService instance for randomness
    
    Returns:
        dict: Contains optimal_hold_minutes and timing_score
    """
    # Find the selected symbol in the enhanced rates
    symbol_rate = None
    for rate in enhanced_rates:
        if rate.signature == symbol:
            symbol_rate = rate
            break
    
    if not symbol_rate:
        # Fallback to middle of range if symbol not found
        return {
            'optimal_hold_minutes': (min_hold_minutes + max_hold_minutes) // 2,
            'timing_score': 0
        }
    
    # Extract analysis data
    energetic_value = getattr(symbol_rate, 'energetic_value', 0)
    gv = getattr(symbol_rate, 'gv', 500)  # Default middle GV if not set
    
    # Calculate timing factors
    # Higher energetic value = sell sooner to lock in gains (favor min_hold_minutes)
    # Lower GV = hold longer for potential growth (favor max_hold_minutes)
    
    # Normalize energetic value (typically 0-1000+) to 0-1 scale
    value_factor = min(energetic_value / 1000.0, 1.0)
    
    # Normalize GV (typically 0-1000+) to 0-1 scale, then invert (lower GV = higher factor)
    gv_factor = 1.0 - min(gv / 1000.0, 1.0)
    
    # Add randomness using hotbits (0-1 scale)
    random_factor = hotbits_service.getInt(0, 1000) / 1000.0
    
    # Weight the factors (you can adjust these weights)
    timing_score = (value_factor * 0.4) + (gv_factor * 0.4) + (random_factor * 0.2)
    
    # Map timing_score (0-1) to the hold time range
    # timing_score closer to 0 = longer hold time (max_hold_minutes)
    # timing_score closer to 1 = shorter hold time (min_hold_minutes)
    hold_range = max_hold_minutes - min_hold_minutes
    optimal_hold_minutes = max_hold_minutes - int(timing_score * hold_range)
    
    # Ensure within bounds
    optimal_hold_minutes = max(min_hold_minutes, min(optimal_hold_minutes, max_hold_minutes))
    
    return {
        'optimal_hold_minutes': optimal_hold_minutes,
        'timing_score': timing_score,
        'factors': {
            'energetic_value': energetic_value,
            'gv': gv,
            'value_factor': value_factor,
            'gv_factor': gv_factor,
            'random_factor': random_factor
        }
    }