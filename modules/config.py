
 (15 Strategies)
# -------------------------
STRATEGIES = {
    "Premium Stoch": ["Overview","VWAP AA","VWAP","Volume Delta","Stoch RSI","SMI","RSI(SMI)","RAINBOW_RSI"],
    "LS Copy": ["Overview","NVT","RoC Bands","RoC","BBWP","PSO","RSI","RAINBOW_RSI"],
    "PositionFlow": ["Overview","VWAP","Chart VWAP","MACZ VWAP","MFI","Fisher Transform","RAINBOW_RSI"],
    "RenkoVol": ["Overview","GR-MMAs","Pi Cycle","Keltner & Bollinger","RSI Ichimoku","RWI","BBWP","Trend Master","VWAP-RSI","ASO"],
    "10h WWV Chart": ["Overview","BTC Log Regression","GR-MMAs","PiCycle","%R MA","RSI","Chaikin Oscillator","Ultimate HODL Wave","PVT","BBWP"],
    "Premium Osc Volatility": ["Overview","AO v2","ATR","RSI(ATR)","RSI","Stoch RSI"],
    "RSI Strategy": ["Overview","Supertrend","CM_Ultimate","FibZia","EVWMA_LB","RSI(63)","%R MA","WT_X","RAR [LuxAlgo]","RAINBOW_RSI","Coppock Curve","OBV","Global Liquidity Index"],
    "WeisWaveVol": ["Overview","Bitcoin Rainbow Wave","CVD Candles","Volume Delta","RSI(Volume Delta)","CMF","RAINBOW_RSI"],
    "PremiumACC": ["Overview","GC","PiCycle Top Indicator","EMA Ribbon","RCI3 Lines","TDIGM","CVD Ichimoku","RSI(OSC)","RSI","Crypto Fear & Greed Index","BBWP"],
    "VolPress": ["Overview","Alligator","GR-MMAs","CVO","WWV","RWI","MACD","TSI","Wick Delta Buy/Sell Pressure","Elasticity","WT_LB"],
    "Volatility": ["Overview","Symmetrical STD Channel","4 SMA","Golden Ratio Fib","RECON ATR","BBWP","SMI","Stoch RSI","CA_Fisher","RSI","RSI line"],
    "ACC/DIST": ["Overview","5 SMMA","Demand Index","BTC Transaction Fees","Ratings","BBWP","MVRV Z-Score"],
    "LuxAlgo": ["Overview","Symmetrical STD Channel","Ultimate RSI","RWI"],
    "Point and Figure": ["Overview","RW Monte Carlo","CM SuperGuppy","AOv2","BBWP","SNAB_RSI_EMA","CM_Williams_Vix_Fix","ASO","RAINBOW_RSI"],
    "Rational Strategy LT": ["Overview","MMBs","GR-Multiple MAs","SAR","Support and Resistance","Coppock Curve","Stoch RSI","BBPower","%R MA","TRIX"],
}


 - SIMPLIFIED
# -------------------------
SIGNAL_CONFIG = {
    "timeframes": {
        "short": {"name": "Short Term", "duration": "1-7 days", "color": "#FF6B6B"},
        "medium": {"name": "Medium Term", "duration": "1-4 weeks", "color": "#4ECDC4"},
        "long": {"name": "Long Term", "duration": "1-6 months", "color": "#45B7D1"}
    },
    "assets": [
        "BTC/USD", "ETH/USD", "ADA/USD", "DOT/USD", "LINK/USD",
        "LTC/USD", "BCH/USD", "XRP/USD", "XLM/USD", "EOS/USD",
        "BNB/USD", "SOL/USD", "MATIC/USD", "AVAX/USD", "ATOM/USD"
    ],
    "signal_types": ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"],
    "confidence_levels": ["Low", "Medium", "High", "Very High"]
}



# -------------------------
class Config:
    APP_NAME = "TradingAnalysis Pro"
    VERSION = "2.1.0"
    SUPPORT_EMAIL = "support@tradinganalysis.com"
    BUSINESS_NAME = "TradingAnalysis Inc."

    # Updated Subscription Plans
    PLANS = {
        "trial": {
            "name": "7-Day Trial",
            "price": 0,
            "duration": 7,
            "strategies": 3,
            "max_sessions": 1
        },
        "premium": {
            "name": "Premium Plan",
            "price": 19,
            "duration": 30,
            "strategies": 15,
            "max_sessions": 3
        },
        "premium_3month": {
            "name": "3-Month Premium",
            "price": 49,
            "duration": 90,
            "strategies": 15,
            "max_sessions": 3
        },
        "premium_6month": {
            "name": "6-Month Premium",
            "price": 97,
            "duration": 180,
            "strategies": 15,
            "max_sessions": 3
        },
        "premium_12month": {
            "name": "12-Month Premium",
            "price": 179,
            "duration": 365,
            "strategies": 15,
            "max_sessions": 3
        }
    }

    # Ko-Fi Payment Links (replace with your actual Ko-Fi shop links)
    KOFI_PREMIUM_MONTHLY_LINK = "https://ko-fi.com/s/39c3423f1d"
    KOFI_PREMIUM_QUARTERLY_LINK = "https://ko-fi.com/s/9b73dfca2a"
    KOFI_PREMIUM_SEMI_ANNUAL_LINK = "https://ko-fi.com/s/419cbf74f9"
    KOFI_PREMIUM_ANNUAL_LINK = "https://ko-fi.com/s/bba601fa2b"

