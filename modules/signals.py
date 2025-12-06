

# -------------------------
def load_signals_data():
    """Load trading signals from Supabase"""
    return supabase_get_trading_signals()

def save_signals_data(signals):
    """Save trading signals to Supabase"""
    return supabase_save_trading_signals(signals)

