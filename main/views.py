from os import name
from sqlite3 import Row
from django.shortcuts import render
import requests
import pandas as pd
import io
from django.http import JsonResponse
import numpy as np
from .models import StockData
from datetime import datetime,timedelta
import yfinance as yf
from django.core.cache import cache
import logging
from django.utils.timezone import now

# import yfinance as yf

# Create your views here.

def test():
    return "hello"

def home(request):
    return render(request, 'home.html')

logger = logging.getLogger(__name__)
import urllib.parse

def fetch_nse_data(request):
    print("Fetching NSE Data Function Called")

    # 1️⃣ Check if companies are already in the database and updated within 24 hours
    last_entry = StockData.objects.order_by('-timestamp').first()
    
    if last_entry and last_entry.timestamp > now() - timedelta(hours=24):
        # print("Serving company data from database, not API")
        company_list = [{'name': entry.company_name, 'symbol': entry.symbol} for entry in StockData.objects.all()]
        # print(f"Company List from DB: {company_list[:50]}")  # Debugging the list
        return JsonResponse({"success": True, "data": company_list})

    # 2️⃣ If database is empty or outdated, fetch fresh data from NSE API
    try:
        print("Fetching fresh data from NSE API")
        nse_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(nse_url, headers=headers)
        response.raise_for_status()

        df_nse = pd.read_csv(io.BytesIO(response.content))
       

        # Ensure required columns exist
        if "SYMBOL" not in df_nse.columns or "NAME OF COMPANY" not in df_nse.columns:
            return JsonResponse({"success": False, "error": "Missing required columns in CSV file."})

        # 3️⃣ Process and store in the database - save only company_name and symbol
        StockData.objects.all().delete()  # Clear old data
        # print("Old data cleared.")

        company_list = []
        for _, row in df_nse.iterrows():
            name = row["NAME OF COMPANY"]
            symbol = row["SYMBOL"]
            
            # Ensure proper encoding for special characters like & in symbol
            symbol = urllib.parse.quote(symbol)  # Encoding symbols with special characters
            
            # Debug log to check how symbols are being processed
            print(f"Inserting {name} with symbol {symbol}")
            
            company_list.append(StockData(company_name=name, symbol=symbol))

        # Bulk insert companies into the database
        StockData.objects.bulk_create(company_list)
        # print(f"{len(company_list)} companies added to the database.")

        # Retrieve data from the database again after insert
        company_list = [{'name': entry.company_name, 'symbol': entry.symbol} for entry in StockData.objects.all()]
        # print(f"Fetched company data: {company_list[:2]}")  # Debugging the list

        return JsonResponse({"success": True, "data": company_list})

    except Exception as e:
        logger.error(f"Error fetching NSE data: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})




CACHE_TIMEOUT = 3600  # 1 hour

def fetch_kpi_data(request):
    symbol = request.GET.get('symbol')
    print(symbol)
    if not symbol:
        return JsonResponse({"success": False, "error": "Symbol not provided."}, status=400)

    symbol = urllib.parse.unquote(symbol)
    print(f"Symbol after decoding: {symbol}")

    if "M&M" and "M&MFIN" in symbol:
        print("Handling M&M case directly.")
        symbol = "M&M" and "M&MFIN"
    else:
        pass
        # Replace '&' with 'and' for other cases
        # symbol = symbol.replace("&", "and")
        # print(f"Symbol after replacing '&' with 'and': {symbol}")

    # Convert to uppercase and remove spaces
    symbol = symbol.upper().replace(" ", "")
    print(f"Symbol after converting to uppercase and removing spaces: {symbol}")    
    
    
  
    
    
    if not symbol.endswith('.NS') and symbol != "NIFTY":
        symbol = f"{symbol}.NS"

    # Check cache
    cached_data = cache.get(f"kpi_data_{symbol}")
    if cached_data:
        return JsonResponse({"success": True, **cached_data})

    # Fetch stock data from Yahoo Finance
    stock = yf.Ticker(symbol)
    stock_history = stock.history(period="1y")
    print(f"Data for {symbol}: {stock_history}")

    if stock_history.empty:
        return JsonResponse({'success': False, 'error': f"No data found for {symbol}."})

    # Fetch fundamental data
    company_info = stock.info

    # Print all stock info for debugging
    print(f"Stock Info for {symbol}: {company_info}")

    # Prepare response data
    response_data = {}



     # Calculate RSI (Relative Strength Index)
    delta = stock_history['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    response_data["rsi"] = round(rsi.iloc[-1], 2) if not rsi.empty else None

    # Calculate Bollinger Bands
    sma = stock_history['Close'].rolling(window=20).mean()
    std = stock_history['Close'].rolling(window=20).std()
    upper_band = sma + (std * 2)
    lower_band = sma - (std * 2)
    response_data["bollinger"] = f"Upper: {round(upper_band.iloc[-1], 2)}, Lower: {round(lower_band.iloc[-1], 2)}" if not upper_band.empty else None

    # Current Stock Price
    try:
        current_stock_price = stock.history(period="1d")['Close'].iloc[-1]
        response_data["current_stock_price"] = round(current_stock_price, 2) if current_stock_price else None
    except IndexError:
        response_data["current_stock_price"] = None

    # 52-week High & Low
    high_52_week = stock_history['High'].max()
    low_52_week = stock_history['Low'].min()
    response_data["high_52_week"] = round(high_52_week, 2) if pd.notna(high_52_week) else None
    response_data["low_52_week"] = round(low_52_week, 2) if pd.notna(low_52_week) else None

    # Market Cap
    market_cap = company_info.get("marketCap", 0) / 10**7  # Convert to Crore
    response_data["market_cap"] = f"{market_cap:,.2f} Cr" if market_cap else "N/A"

    # Ensure current stock price is valid
    if current_stock_price and high_52_week and low_52_week:
        high_diff_percentage = ((high_52_week - current_stock_price) / high_52_week) * 100
        low_diff_percentage = ((current_stock_price - low_52_week) / low_52_week) * 100
    else:
        high_diff_percentage = None
        low_diff_percentage = None

    response_data["high_diff_percentage"] = round(high_diff_percentage, 2) if high_diff_percentage is not None else None
    response_data["low_diff_percentage"] = round(low_diff_percentage, 2) if low_diff_percentage is not None else None


    # # Volume
    # try:
    #     # Fetch the current volume and 52-week average volume
    #     current_volume = stock_history['Volume'].iloc[-1] if not stock_history['Volume'].empty else None
    #     average_volume_52_week = stock_history['Volume'].mean() if not stock_history['Volume'].empty else None
       

    #     # print(f"Current Volume: {current_volume}, Average Volume: {average_volume_52_week}")
    
    #     if current_volume is not None and average_volume_52_week is not None and average_volume_52_week != 0:
    #         # New logic for volume calculation
    #         current_volume = int(current_volume)
    #         average_volume_52_week = int(average_volume_52_week)

    #         # Calculate the percentage difference
    #         percentage_difference = ((current_volume - average_volume_52_week) / average_volume_52_week) * 100 if average_volume_52_week != 0 else 0
    #         response_data["current_volume"] = current_volume
    #         response_data["average_volume_52_week"] = average_volume_52_week
    #         response_data["percentage_difference"] = round(percentage_difference, 2)

    #     else:
    #         response_data["percentage_difference"] = None
    #         response_data["average_volume_52_week"] = 'N/A'
    # except Exception as e:
    #     print(f"Error calculating volume traded for {symbol}: {e}")
    #     response_data["percentage_difference"] = None



    # CAGR (5 years)
    try:
        start_price_5y = stock.history(period="5y")['Close'].iloc[0]
        end_price_5y = stock.history(period="5y")['Close'].iloc[-1]
        cagr_5y = ((end_price_5y / start_price_5y) ** (1 / 5) - 1) * 100
        response_data["cagr_5y"] = round(cagr_5y, 2)
    except:
        response_data["cagr_5y"] = None

  

    try:
        three_years_ago = stock_history.index[-1] - pd.DateOffset(years=3)
        stock_data_3y = stock_history.loc[stock_history.index >= three_years_ago]
        
        if stock_data_3y.empty:
            response_data["cagr_3y"] = None
        else:
            start_price_3y = stock_data_3y['Close'].iloc[0]  # Price 3 years ago
            end_price_3y = stock_data_3y['Close'].iloc[-1]  # Most recent price
            cagr_3y = ((end_price_3y / start_price_3y) ** (1 / 3) - 1) * 100
            response_data["cagr_3y"] = round(cagr_3y, 2)
    except:
        response_data["cagr_3y"] = None

    # Volatility Calculation
    historical_data = stock.history(period="1mo")['Close']
    volatility = historical_data.pct_change().std() * (252 ** 0.5) if not historical_data.empty else None
    response_data["volatility"] = round(volatility, 4) if volatility is not None else None

    # Dividend Yield
    dividend_yield = company_info.get("dividendYield", 0)
    response_data["dividend_yield"] = round(dividend_yield*100, 4) if dividend_yield else None

    # PE Ratio
    pe_ratio = company_info.get("trailingPE", 0)
    response_data["pe_ratio"] = round(pe_ratio, 2) if pe_ratio else None

    #volume
    average_volume_52_week = company_info.get(  'averageVolume',0)
    response_data["average_volume_52_week"] = round(average_volume_52_week,3) if average_volume_52_week else None

    #roe
    roe = company_info.get( 'returnOnEquity',0)
    response_data["roe"] = round(roe*100,2) if roe else None


    # Moving Averages and MACD
    try:
        moving_average_50 = stock_history['Close'].rolling(window=50).mean().iloc[-1]
        moving_average_200 = stock_history['Close'].rolling(window=200).mean().iloc[-1]

        response_data["moving_average_50"] = round(moving_average_50, 2) if pd.notna(moving_average_50) else None
        response_data["moving_average_200"] = round(moving_average_200, 2) if pd.notna(moving_average_200) else None

        # MACD Calculation
        short_ema = stock_history['Close'].ewm(span=12, adjust=False).mean()
        long_ema = stock_history['Close'].ewm(span=26, adjust=False).mean()
        macd = short_ema - long_ema
        signal = macd.ewm(span=9, adjust=False).mean()

        response_data["macd"] = round(macd.iloc[-1], 4) if not macd.empty else None
        response_data["macd_signal"] = round(signal.iloc[-1], 4) if not signal.empty else None
    except Exception as e:
        print(f"Error calculating moving averages or MACD for {symbol}: {e}")
        response_data["moving_average_50"] = None
        response_data["moving_average_200"] = None
        response_data["macd"] = None
        response_data["macd_signal"] = None

    # Cache response
    cache.set(f"kpi_data_{symbol}", response_data, CACHE_TIMEOUT)

    # print(response_data)  # Debugging the response data

    return JsonResponse({"success": True, **response_data})


# def fetch_nse_data(request):
#     print("Fetching NSE Data Function Called")
    

#     # 1️⃣ Check if companies are already in the database and updated within 24 hours
#     last_entry = StockData.objects.order_by('-timestamp').first()
    
#     if last_entry and last_entry.timestamp > now() - timedelta(hours=24):
#         # print("Serving company data from database, not API")
#         company_list = [{'name': entry.company_name, 'symbol': entry.symbol} for entry in StockData.objects.all()]
#         # print(f"Company List from DB: {company_list[:50]}")  # Debugging the list
#         return JsonResponse({"success": True, "data": company_list})

#     # 2️⃣ If database is empty or outdated, fetch fresh data from NSE API
#     try:
#         print("Fetching fresh data from NSE API")
#         nse_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
#         headers = {'User-Agent': 'Mozilla/5.0'}

#         response = requests.get(nse_url, headers=headers)
#         response.raise_for_status()

#         df_nse = pd.read_csv(io.BytesIO(response.content))

#         # Ensure required columns exist
#         if "SYMBOL" not in df_nse.columns or "NAME OF COMPANY" not in df_nse.columns:
#             return JsonResponse({"success": False, "error": "Missing required columns in CSV file."})

#         # 3️⃣ Process and store in the database - save only company_name and symbol
#         StockData.objects.all().delete()  # Clear old data
#         # print("Old data cleared.")

#         company_list = []
#         for _, row in df_nse.iterrows():
#             name = row["NAME OF COMPANY"]
#             symbol = row["SYMBOL"]
#             company_list.append(StockData(company_name=name, symbol=symbol))

#         # Bulk insert companies into the database
#         StockData.objects.bulk_create(company_list)
#         # print(f"{len(company_list)} companies added to the database.")

#         # Retrieve data from the database again after insert
#         company_list = [{'name': entry.company_name, 'symbol': entry.symbol} for entry in StockData.objects.all()]
#         # print(f"Fetched company data: {company_list[:2]}")  # Debugging the list

#         return JsonResponse({"success": True, "data": company_list})

#     except Exception as e:
#         logger.error(f"Error fetching NSE data: {str(e)}")
#         return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})



# def fetch_kpi_data(request):
#     print("symbol==>",)
#     symbol_ = request.GET.get('symbol')

#     stock = yf.Ticker(symbol_)
#     company_info = stock.info
#     market_cap = company_info.get("marketCap", 0) / 10**7

#     return JsonResponse({"success": True,"market_cap":market_cap})