#!/usr/bin/env python3
"""
Validate which TW stocks are available on yfinance

Tests all potential TW stock symbols and returns only those that work.
"""

import yfinance as yf
import pandas as pd
from tqdm import tqdm

# Common TW stock suffixes for yfinance
SUFFIX = '.TW'

# Test list - major TW stocks
TEST_STOCKS = [
    # Technology
    '2330', '2317', '2454', '2308', '2357', '2353', '2395', '2382',
    '2385', '2399', '2408', '2421', '2379', '2377', '2376', '2367',
    '2368', '2313', '2325', '2337', '2344', '2341', '2345', '2409',
    '2387', '2360', '2366', '2369', '2371', '2373', '2375', '2380',
    '2381', '2383', '2384', '2386', '2388', '2389', '2390', '2391',
    '2392', '2393', '2394', '2396', '2397', '2398', '2400', '2401',
    '2402', '2403', '2404', '2405', '2406', '2412', '2413', '2414',
    '2415', '2416', '2417', '2418', '2419', '2420',
    
    # Finance
    '2800', '2801', '2802', '2803', '2804', '2805', '2806', '2807',
    '2808', '2809', '2810', '2811', '2812', '2813', '2814', '2815',
    '2816', '2817', '2818', '2819', '2820', '2880', '2881', '2882',
    '2883', '2884', '2885', '2886', '2887', '2888', '2889', '2890',
    '2891', '2892',
    
    # Traditional
    '1101', '1102', '1103', '1104',
    '1201', '1203', '1204', '1216',
    '1301', '1303', '1304', '1305', '1306', '1307', '1308', '1309',
    '1401', '1402', '1403', '1404', '1405',
    '1501', '1502', '1503', '1504', '1505',
    '1601', '1602', '1603', '1604', '1605',
    '1701', '1702', '1703', '1704', '1705',
    '1801', '1802', '1803', '1804', '1805',
    '1901', '1902', '1903', '1904', '1905',
    '2001', '2002', '2003', '2004', '2005',
    '2006', '2007', '2008', '2009', '2010',
    '2011', '2012', '2013', '2014', '2015',
    '2016', '2017', '2018', '2019', '2020',
    '2021', '2022', '2023', '2024', '2025',
    '2026', '2027', '2028', '2029', '2030',
    
    # Retail
    '2901', '2903', '2904', '2905', '2906', '2907', '2908', '2910',
    '2911', '2912', '2913', '2915', '2916', '2917', '2918', '2919',
    '2920', '2921', '2922', '2923', '2924', '2925', '2926', '2927',
    '2928', '2929', '2930', '2931', '2932', '2933', '2934', '2935',
    '2936', '2937', '2938', '2939', '2940', '2941', '2942', '2943',
    '2944', '2945', '2946', '2947', '2948', '2949', '2950', '2951',
    '2952', '2953', '2954', '2955', '2956', '2957', '2958', '2959',
    '2960', '2961', '2962', '2963', '2964', '2965', '2966', '2967',
    '2968', '2969', '2970', '2971', '2972', '2973', '2974', '2975',
    '2976', '2977', '2978', '2979', '2980', '2981', '2982', '2983',
    '2984', '2985', '2986', '2987', '2988', '2989', '2990', '2991',
    
    # ETFs
    '0050', '006208', '00888', '00900', '00919',
]

def validate_stock(symbol):
    """Test if a stock symbol is valid on yfinance."""
    try:
        ticker = yf.Ticker(f"{symbol}{SUFFIX}")
        df = ticker.history(period='1mo')
        
        if not df.empty and len(df) > 0:
            # Check if we got actual data (not all NaN)
            if df['Close'].notna().any():
                return True
        return False
    except:
        return False

def main():
    print("Validating Taiwan stocks on yfinance...")
    print(f"Testing {len(TEST_STOCKS)} symbols...\n")
    
    valid_stocks = {}
    invalid_symbols = []
    
    for symbol in tqdm(TEST_STOCKS, desc="Validating"):
        if validate_stock(symbol):
            # Get the name
            try:
                ticker = yf.Ticker(f"{symbol}{SUFFIX}")
                info = ticker.info
                name = info.get('shortName', info.get('longName', 'Unknown'))
                valid_stocks[symbol] = name
            except:
                valid_stocks[symbol] = 'Unknown'
        else:
            invalid_symbols.append(symbol)
    
    print(f"\n{'='*60}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Valid stocks: {len(valid_stocks)}")
    print(f"Invalid symbols: {len(invalid_symbols)}")
    
    print(f"\n{'='*60}")
    print("VALID STOCKS (yfinance compatible)")
    print(f"{'='*60}")
    for symbol, name in sorted(valid_stocks.items()):
        print(f"{symbol}: {name}")
    
    if invalid_symbols:
        print(f"\n{'='*60}")
        print("INVALID SYMBOLS (not found on yfinance)")
        print(f"{'='*60}")
        print(", ".join(invalid_symbols[:20]) + ("..." if len(invalid_symbols) > 20 else ""))
    
    # Save to file
    with open('valid_stocks.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(valid_stocks, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to: valid_stocks.json")
    
    return valid_stocks

if __name__ == "__main__":
    main()
