from sqlite3 import Row
from django.shortcuts import render
import requests
import pandas as pd
import io
from django.http import JsonResponse
import numpy as np

# import yfinance as yf

# Create your views here.

def test():
    return "hello"

def home(request):
    return render(request, 'home.html')



from .models import StockData
from datetime import datetime
import yfinance as yf

def fetch_stock_data(request):
    symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        symbol = symbol.upper()

        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # First, try to fetch data from the database
        stock_data = StockData.objects.filter(symbol=symbol).order_by('-timestamp').first()

        # If the stock data doesn't exist in the database, fetch it from Yahoo Finance
        if not stock_data:
            stock = yf.Ticker(symbol)
            stock_history = stock.history(period="1y")

            if stock_history.empty:
                return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

            current_price = stock_history['Close'].iloc[-1]
            high_52_week = stock_history['High'].max()
            low_52_week = stock_history['Low'].min()

            stock_data = StockData(
                symbol=symbol,
                current_price=current_price,
                high_52_week=high_52_week,
                low_52_week=low_52_week,
                timestamp=datetime.now()  # Save the timestamp
            )
            stock_data.save()  # Save the data to the database

        # Prepare the response data
        response_data = {
            'success': True,
            'current_price': round(stock_data.current_price, 2),
            'high_52_week': round(stock_data.high_52_week, 2),
            'low_52_week': round(stock_data.low_52_week, 2),
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})


def fetch_market_cap(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({"success": False, "error": "Symbol not provided."}, status=400)

    if not symbol.endswith('.NS'):
        symbol = f"{symbol}.NS"

    try:
        # Fetch stock data from database
        stock_data = StockData.objects.filter(symbol=symbol).first()

        if not stock_data:
            return JsonResponse({'success': False, 'error': f"Stock data for {symbol} not found."}, status=404)

        # Fetch market cap from Yahoo Finance if not in database
        if not stock_data.market_cap:
            company = yf.Ticker(symbol)
            market_cap = company.info.get("marketCap")
            if market_cap is None:
                return JsonResponse({"success": False, "error": "Market capitalization not available."}, status=404)

            stock_data.market_cap = market_cap / 10**7  # Convert to Crore
            stock_data.save()  # Save the market cap to database

        formatted_market_cap = f"{stock_data.market_cap:,.2f} Cr"

        return JsonResponse({"success": True, "market_cap": formatted_market_cap})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def fetch_stock_price_inr(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        symbol = symbol.upper()

        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # Check if stock data exists in the database
        stock_data = StockData.objects.filter(symbol=symbol).first()

        if not stock_data:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}"})

        # If price is not available, fetch it from Yahoo Finance
        if not stock_data.current_price:
            stock = yf.Ticker(symbol)
            stock_history = stock.history(period="1d")
            if stock_history.empty:
                return JsonResponse({'success': False, 'error': "Error fetching stock price."})
            stock_data.current_price = stock_history['Close'].iloc[-1]
            stock_data.save()

        return JsonResponse({'success': True, 'price': round(stock_data.current_price, 2)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching stock price: {str(e)}"})



def fetch_nse_data(request):
    """
    Fetches equity data from NSE and returns a list of objects with 'name' and 'symbol'.
    If the symbol is provided, it fetches from the database.
    """
    symbol = request.GET.get('symbol')  # Get the symbol from query parameters

    if not symbol:
        # Try fetching the entire list of companies when no symbol is provided
        try:
            # Fetch data from the external NSE data source
            nse_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
            headers = {'User-Agent': 'Mozilla/5.0'}

            # Fetch the data from NSE CSV
            with requests.Session() as session:
                session.headers.update(headers)
                response = session.get(nse_url)
                response.raise_for_status()  # Raise error if status is not OK

            # Load CSV content into a pandas DataFrame
            df_nse = pd.read_csv(io.BytesIO(response.content))

            # Ensure the required columns exist
            if "SYMBOL" not in df_nse.columns or "NAME OF COMPANY" not in df_nse.columns:
                return JsonResponse({"success": False, "error": "Missing required columns in CSV file."})

            # Create a list of dictionaries
            company_list = [{"name": row["NAME OF COMPANY"], "symbol": row["SYMBOL"]} for _, row in df_nse.iterrows()]
            company_dict = {company["name"]: company["symbol"] for company in company_list}

            # Log the fetched companies data
            # print("Fetched companies data:", company_dict)  # Log the data being returned

            return JsonResponse({"success": True, "data": company_dict}, safe=False)

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})

    # If symbol is provided, fetch from the database
    try:
        # Fetch from the database if the symbol exists
        stock_data = StockData.objects.filter(symbol=symbol.upper()).first()

        if not stock_data:
            return JsonResponse({'success': False, 'error': 'Symbol not found in the database'})

        # If symbol is found in the database, return the relevant stock data
        return JsonResponse({
            'success': True,
            'data': {
                'symbol': stock_data.symbol,
                'current_price': stock_data.current_price,
                'high_52_week': stock_data.high_52_week,
                'low_52_week': stock_data.low_52_week,
                'market_cap': stock_data.market_cap,
                'volume': stock_data.volume,
                'average_volume_52_week': stock_data.average_volume_52_week,
                'cagr_5y': stock_data.cagr_5y,
                'cagr_3y': stock_data.cagr_3y,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})


def fetch_cagr_data(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        # Ensure symbol is uppercase and append ".NS" for Indian stocks if not already present
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # Check the database for stored data
        stock_data = StockData.objects.filter(symbol=symbol).first()
        
        if stock_data and stock_data.cagr_5y is not None and stock_data.cagr_3y is not None:
            # If both 5-year and 3-year CAGR exist in the database, return them
            return JsonResponse({
                'success': True,
                'cagr_5y': round(stock_data.cagr_5y, 2),
                'cagr_3y': round(stock_data.cagr_3y, 2),
            })

        # Fetch stock data using yfinance
        stock = yf.Ticker(symbol)
        stock_data_history = stock.history(period="5y")  # Fetch 5 years of data

        if stock_data_history.empty:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

        # Ensure 'Adj Close' is populated; use 'Close' as a fallback if necessary
        if 'Adj Close' not in stock_data_history.columns or stock_data_history['Adj Close'].isnull().all():
            stock_data_history['Adj Close'] = stock_data_history['Close']

        # Calculate the 5-Year CAGR
        start_price_5y = stock_data_history['Adj Close'].iloc[0]
        end_price_5y = stock_data_history['Adj Close'].iloc[-1]
        cagr_5y = ((end_price_5y / start_price_5y) ** (1 / 5) - 1) * 100

        # Calculate the 3-Year CAGR
        three_years_ago = stock_data_history.index[-1] - pd.DateOffset(years=3)
        stock_data_3y = stock_data_history.loc[stock_data_history.index >= three_years_ago]
        if stock_data_3y.empty:
            return JsonResponse({'success': False, 'error': f"Not enough data to calculate 3-Year CAGR for {symbol}"})

        start_price_3y = stock_data_3y['Adj Close'].iloc[0]
        end_price_3y = stock_data_3y['Adj Close'].iloc[-1]
        cagr_3y = ((end_price_3y / start_price_3y) ** (1 / 3) - 1) * 100

        # Save the calculated data to the database
        if stock_data:
            stock_data.cagr_5y = cagr_5y
            stock_data.cagr_3y = cagr_3y
            stock_data.save()
        else:
            # If the stock does not already exist in the database, create a new entry
            StockData.objects.create(
                symbol=symbol,
                cagr_5y=cagr_5y,
                cagr_3y=cagr_3y,
            )

        # Return the calculated values
        return JsonResponse({
            'success': True,
            'cagr_5y': round(cagr_5y, 2),
            'cagr_3y': round(cagr_3y, 2),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})









from .models import VolumeTraderData, PumpDumpStatus


# Fetch Volume and Trader Data
def fetch_volume_trader_data(request):
    symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="1y")

        if stock_data.empty:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

        current_volume = stock_data['Volume'].iloc[-1]
        average_volume_52_week = stock_data['Volume'].mean()
        current_volume = int(current_volume)
        average_volume_52_week = int(average_volume_52_week)

        # Calculate the percentage difference
        percentage_difference = ((current_volume - average_volume_52_week) / average_volume_52_week) * 100 if average_volume_52_week != 0 else 0

        # Use update_or_create to either update the existing record or create a new one
        volume_data, created = VolumeTraderData.objects.update_or_create(
            symbol=symbol,
            defaults={
                'current_volume': current_volume,
                'average_volume_52_week': average_volume_52_week,
                'percentage_difference': percentage_difference,
                'timestamp': datetime.now(),
            }
        )

        return JsonResponse({
            'success': True,
            'current_volume': current_volume,
            'average_volume_52_week': average_volume_52_week,
            'percentage_difference': percentage_difference,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching volume data: {str(e)}"})



# Fetch Pump or Dump Status
def fetch_pump_or_dump(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="5d")

        if stock_data.empty:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

        current_price = stock_data['Close'].iloc[-1]
        price_7_days_ago = stock_data['Close'].iloc[0]
        price_change = ((current_price - price_7_days_ago) / price_7_days_ago) * 100

        # Determine if the stock is being pumped or dumped
        pump_status = 'Yes, It is being pumped!' if price_change > 30 else 'No'
        dump_status = 'Yes, It is being dumped!' if price_change < -30 else 'No'

        # Store in the database
        pump_dump_data = PumpDumpStatus(
            symbol=symbol,
            pump_status=pump_status,
            dump_status=dump_status,
            price_change=price_change,
            timestamp=datetime.now()
        )
        pump_dump_data.save()

        return JsonResponse({
            'success': True,
            'pump_status': pump_status,
            'dump_status': dump_status
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})







def fetch_stock_indicators(request):
    """
    Fetches MACD, RSI, and Bollinger Bands for a given stock symbol using yfinance and saves them to the database.
    """
    # Extract the symbol from the request
    symbol = request.GET.get("symbol", None)
    if not symbol:
        return JsonResponse({"success": False, "error": "No stock symbol provided."})
    
    try:
        # Ensure the symbol is uppercase and ends with ".NS"
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # Fetch stock data using yfinance
        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="6mo", interval="1d")

        # Ensure data is available
        if stock_data.empty or len(stock_data) < 26:
            return JsonResponse({"success": False, "error": "Insufficient data for calculations."})

        # MACD Calculation
        stock_data['EMA12'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
        stock_data['EMA26'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
        stock_data['MACD'] = stock_data['EMA12'] - stock_data['EMA26']
        stock_data['Signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
        macd = stock_data.iloc[-1][['MACD', 'Signal']].to_dict()

        # RSI Calculation
        delta = stock_data['Close'].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        stock_data['RSI'] = 100 - (100 / (1 + rs))
        rsi = stock_data.iloc[-1]['RSI']

        # Bollinger Bands Calculation
        stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()
        stock_data['UpperBand'] = stock_data['SMA20'] + (2 * stock_data['Close'].rolling(window=20).std())
        stock_data['LowerBand'] = stock_data['SMA20'] - (2 * stock_data['Close'].rolling(window=20).std())
        bollinger_bands = stock_data.iloc[-1][['SMA20', 'UpperBand', 'LowerBand']].to_dict()

        # Save the indicators to the database
        stock_data_entry, created = StockData.objects.get_or_create(symbol=symbol)
        stock_data_entry.macd = macd['MACD']
        stock_data_entry.rsi = rsi
        stock_data_entry.bollinger_bands = str(bollinger_bands)  # Store as string or JSON (depending on your preference)
        stock_data_entry.save()

        # Return the results
        return JsonResponse({
            "success": True,
            "data": {
                "MACD": macd,
                "RSI": rsi,
                "BollingerBands": bollinger_bands
            }
        }, safe=False)
    
    except Exception as e:
        return JsonResponse({"success": False, "error": f"An error occurred while processing the data: {str(e)}"})



# # Fetch Stock Indicators (MACD, RSI, Bollinger Bands)
# def fetch_stock_indicators(request):
#     symbol = request.GET.get('symbol')
#     print(f"Received symbol: {symbol}")
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         symbol = symbol.upper()
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Check if stock indicators data exists in the database
#         stock_record, created = StockData.objects.get_or_create(symbol=symbol)

#         # Return existing data if available
#         if stock_record.macd is not None and stock_record.rsi is not None and stock_record.bollinger_bands:
#             return JsonResponse({
#                 'success': True,
#                 'data': {
#                     'MACD': stock_record.macd,
#                     'RSI': stock_record.rsi,
#                     'BollingerBands': eval(stock_record.bollinger_bands),  # Convert string to dictionary
#                 }
#             })

#         # Fetch stock data from yfinance
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="6mo", interval="1d")

#         if stock_data.empty or len(stock_data) < 26:
#             return JsonResponse({'success': False, 'error': 'Insufficient data for calculations'})

#         # MACD Calculation
#         stock_data['EMA12'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
#         stock_data['EMA26'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
#         stock_data['MACD'] = stock_data['EMA12'] - stock_data['EMA26']
#         stock_data['Signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
#         macd = stock_data.iloc[-1]['MACD']

#         # RSI Calculation
#         delta = stock_data['Close'].diff(1)
#         gain = delta.where(delta > 0, 0)
#         loss = -delta.where(delta < 0, 0)
#         avg_gain = gain.rolling(window=14).mean()
#         avg_loss = loss.rolling(window=14).mean()
#         rs = avg_gain / avg_loss
#         rsi = 100 - (100 / (1 + rs)).iloc[-1]

#         # Bollinger Bands Calculation
#         stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()
#         stock_data['UpperBand'] = stock_data['SMA20'] + (2 * stock_data['Close'].rolling(window=20).std())
#         stock_data['LowerBand'] = stock_data['SMA20'] - (2 * stock_data['Close'].rolling(window=20).std())
#         bollinger_bands = {
#             'SMA20': stock_data.iloc[-1]['SMA20'],
#             'UpperBand': stock_data.iloc[-1]['UpperBand'],
#             'LowerBand': stock_data.iloc[-1]['LowerBand'],
#         }

#         # Update and save the database record
#         stock_record.macd = macd
#         stock_record.rsi = rsi
#         stock_record.bollinger_bands = str(bollinger_bands)  # Convert dict to string for storage
#         stock_record.save()

#         return JsonResponse({
#             'success': True,
#             'data': {
#                 'MACD': macd,
#                 'RSI': rsi,
#                 'BollingerBands': bollinger_bands,
#             }
#         })

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})



# def fetch_stock_indicators(request):
#     symbol = request.GET.get('symbol')
#     print(f"Received symbol: {symbol}")
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         symbol = symbol.upper()
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Check if stock indicators data exists in the database
#         stock_data = StockData.objects.filter(symbol=symbol).first()

#         if stock_data and stock_data.macd and stock_data.rsi and stock_data.bollinger_bands:
#             # Return data from the database if available
#             return JsonResponse({
#                 'success': True,
#                 'data': {
#                     'MACD': stock_data.macd,
#                     'RSI': stock_data.rsi,
#                     'BollingerBands': stock_data.bollinger_bands,
#                 }
#             })
        
#         # Fetch stock data from yfinance
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="6mo", interval="1d")

#         if stock_data.empty or len(stock_data) < 26:
#             return JsonResponse({'success': False, 'error': 'Insufficient data for calculations'})

#         # MACD Calculation
#         stock_data['EMA12'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
#         stock_data['EMA26'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
#         stock_data['MACD'] = stock_data['EMA12'] - stock_data['EMA26']
#         stock_data['Signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
#         macd = stock_data.iloc[-1]['MACD']

#         # RSI Calculation
#         delta = stock_data['Close'].diff(1)
#         gain = delta.where(delta > 0, 0)
#         loss = -delta.where(delta < 0, 0)
#         avg_gain = gain.rolling(window=14).mean()
#         avg_loss = loss.rolling(window=14).mean()
#         rs = avg_gain / avg_loss
#         rsi = 100 - (100 / (1 + rs)).iloc[-1]

#         # Bollinger Bands Calculation
#         stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()
#         stock_data['UpperBand'] = stock_data['SMA20'] + (2 * stock_data['Close'].rolling(window=20).std())
#         stock_data['LowerBand'] = stock_data['SMA20'] - (2 * stock_data['Close'].rolling(window=20).std())
#         bollinger_bands = {
#             'SMA20': stock_data.iloc[-1]['SMA20'],
#             'UpperBand': stock_data.iloc[-1]['UpperBand'],
#             'LowerBand': stock_data.iloc[-1]['LowerBand'],
#         }

#         # Save the calculated data into the database
#         if stock_data:
#             stock_data.macd = macd
#             stock_data.rsi = rsi
#             stock_data.bollinger_bands = str(bollinger_bands)  # Store as a string (JSON or CSV)
#             stock_data.save()

#         return JsonResponse({
#             'success': True,
#             'data': {
#                 'MACD': macd,
#                 'RSI': rsi,
#                 'BollingerBands': bollinger_bands,
#             }
#         })
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})



# def fetch_stock_data(request):
#     symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         # Ensure the symbol is uppercase
#         symbol = symbol.upper()

#         # Append .NS if necessary for Indian stocks
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Fetch stock data using yfinance
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="1y")  # Fetch 1 year data
        
#         if stock_data.empty:
#             return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

#         # Find current price, 52-week high, and 52-week low
#         current_price = stock_data['Close'].iloc[-1]
#         high_52_week = stock_data['High'].max()
#         low_52_week = stock_data['Low'].min()

#         # Prepare response data
#         response_data = {
#             'success': True,
#             'current_price': round(current_price, 2),
#             'high_52_week': round(high_52_week, 2),
#             'low_52_week': round(low_52_week, 2),
#         }

#         return JsonResponse(response_data)

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})




# def fetch_market_cap(request):
#     symbol = request.GET.get('symbol')
#     if not symbol:
#         return JsonResponse({"success": False, "error": "Symbol not provided."}, status=400)

#     # Automatically add .NS to the symbol if it's not already there
#     if not symbol.endswith('.NS'):
#         symbol = f"{symbol}.NS"

#     try:
#         # Fetch company data using yfinance
#         company = yf.Ticker(symbol)

#         # Get the market capitalization (in the form of a number)
#         market_cap = company.info.get("marketCap")
        
#         if market_cap is None:
#             return JsonResponse({"success": False, "error": "Market capitalization not available."}, status=404)

#         # Convert the market cap to crores (₹1 crore = ₹10,000,000)
#         market_cap_in_crores = market_cap / 10**7

#         # Format the market cap to 2 decimal places
#         # market_cap_in_crores = round(market_cap_in_crores, 2)
#         # formatted_market_cap = f"{market_cap_in_crores} Crore"
#         formatted_market_cap = f"{market_cap_in_crores:,.2f} Cr"

#         # Return the market cap in INR or as is
#         return JsonResponse({"success": True, "market_cap":formatted_market_cap})

#     except Exception as e:
#         return JsonResponse({"success": False, "error": str(e)}, status=500)






# import yfinance as yf

# def fetch_stock_price_inr(request):
#     symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         # Ensure the symbol is uppercase
#         symbol = symbol.upper()

#         # Check if the symbol is for an Indian stock; append .NS if necessary

#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Fetch stock data using yfinance
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="1d")
        
#         # Log the raw stock data for debugging
#         print(f"Raw stock data for {symbol}: {stock_data}")
        
#         if stock_data.empty:
#             return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})
        
#         # Extract the closing price in INR (yfinance provides the price in local currency of the stock exchange)
#         stock_price_inr = stock_data['Close'].iloc[-1]
#         print(f"Extracted stock price (INR) for {symbol}: {stock_price_inr}")

#         return JsonResponse({'success': True, 'price': round(stock_price_inr, 2)})

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': f"Error fetching stock price: {str(e)}"})




# def fetch_nse_data(request):
#     """
#     Fetches equity data from NSE and returns a list of objects with 'name' and 'symbol'.
#     """
#     nse_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

#     # Headers for the request
#     headers = { 
         
#         'User-Agent': 'Mozilla/5.0'
#     }

#     try:
#         # Fetch the data
#         with requests.Session() as session:
#             session.headers.update(headers)
#             response = session.get(nse_url)
#             response.raise_for_status()  # Raise an error for bad HTTP status

#         # print(f"Response Status Code: {response.status_code}")

#         # Load CSV content into pandas DataFrame
#         df_nse = pd.read_csv(io.BytesIO(response.content))

#         # print(f"Columns in CSV: {df_nse.columns}")
        


#         # Ensure the required columns exist
#         if "SYMBOL" not in df_nse.columns or "NAME OF COMPANY" not in df_nse.columns:
#             return JsonResponse({"success": False, "error": "Missing required columns in CSV file."})

#         # Create a list of dictionaries
#         company_list = [{"name": row["NAME OF COMPANY"],"symbol": row["SYMBOL"]} for _, row in df_nse.iterrows()]
#         company_dict = {company["name"]: company["symbol"] for company in company_list}
        
      
#         return JsonResponse({"success": True, "data": company_dict}, safe=False)

#     except requests.exceptions.RequestException as e:
#         return JsonResponse({"success": False, "error": str(e)})

#     except Exception as e:
#         return JsonResponse({"success": False, "error": "An error occurred while processing the data: " + str(e)})





# def fetch_cagr_data(request):
#     symbol = request.GET.get('symbol')
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         # Ensure symbol is uppercase and append ".NS" for Indian stocks if not already present
#         symbol = symbol.upper()
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Fetch stock data using yfinance
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="5y")  # Fetch 5 years of data

#         if stock_data.empty:
#             return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

#         # Ensure 'Adj Close' is populated; use 'Close' as a fallback if necessary
#         if 'Adj Close' not in stock_data.columns or stock_data['Adj Close'].isnull().all():
#             stock_data['Adj Close'] = stock_data['Close']

#         # Calculate the 5-Year CAGR using the manual formula
#         start_price_5y = stock_data['Adj Close'].iloc[0]
#         end_price_5y = stock_data['Adj Close'].iloc[-1]
#         cagr_5y = ((end_price_5y / start_price_5y) ** (1 / 5) - 1) * 100

#         # Calculate the 3-Year CAGR using the manual formula
#         three_years_ago = stock_data.index[-1] - pd.DateOffset(years=3)
#         stock_data_3y = stock_data.loc[stock_data.index >= three_years_ago]
#         if stock_data_3y.empty:
#             return JsonResponse({'success': False, 'error': f"Not enough data to calculate 3-Year CAGR for {symbol}"})

#         start_price_3y = stock_data_3y['Adj Close'].iloc[0]
#         end_price_3y = stock_data_3y['Adj Close'].iloc[-1]
#         cagr_3y = ((end_price_3y / start_price_3y) ** (1 / 3) - 1) * 100

#         # Return the calculated values
#         return JsonResponse({
#             'success': True,
#             'cagr_5y': round(cagr_5y, 2),
#             'cagr_3y': round(cagr_3y, 2),
#         })

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})



   


# def fetch_volume_trader_data(request):
#     symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         # Ensure the symbol is uppercase and append ".NS" for Indian stocks if not already present
#         symbol = symbol.upper()
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Fetch stock data using yfinance (1-year data)
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="1y")

#         if stock_data.empty:
#             return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

#         # Get the current trading volume and 52-week average volume
#         current_volume = stock_data['Volume'].iloc[-1]
#         average_volume_52_week = stock_data['Volume'].mean()  # Calculate the 52-week average volume

#         # Convert the volumes to standard Python int to avoid JSON serialization issue
#         current_volume = int(current_volume)
#         average_volume_52_week = int(average_volume_52_week)

#         # Calculate the percentage difference between current volume and 52-week average volume
#         if average_volume_52_week != 0:
#             percentage_difference = ((current_volume - average_volume_52_week) / average_volume_52_week) * 100
#         else:
#             percentage_difference = 0  # Avoid division by zero if the average volume is 0

#         # Return the data as JSON to the frontend
#         response_data = {
#             'success': True,
#             'current_volume': current_volume,
#             'average_volume_52_week': average_volume_52_week,
#             'percentage_difference': percentage_difference,
#         }

#         return JsonResponse(response_data)

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': f"Error fetching volume data: {str(e)}"})



   
# from datetime import datetime, timedelta

# def fetch_pump_or_dump(request):
#     symbol = request.GET.get('symbol')
#     if not symbol:
#         return JsonResponse({'success': False, 'error': 'Symbol not provided'})

#     try:
#         # Ensure the symbol is uppercase and append ".NS" for Indian stocks if not already present
#         symbol = symbol.upper()
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Fetch stock data using yfinance (fetch last 7 days of data)
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="5d")

#         if stock_data.empty:
#             return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

#         # Get the current price and the price 7 days ago
#         current_price = stock_data['Close'].iloc[-1]
#         price_7_days_ago = stock_data['Close'].iloc[0]

#         # Calculate percentage change
#         price_change = ((current_price - price_7_days_ago) / price_7_days_ago) * 100

#         # Determine if the stock is being pumped or dumped
#         if price_change > 30:
#             pump_status = 'Yes, It is being pumped!'
#             dump_status = 'No'
#         elif price_change < -30:
#             pump_status = 'No'
#             dump_status = 'Yes, It is being dumped!'
#         else:
#             pump_status = 'No'
#             dump_status = 'No'

#         return JsonResponse({
#             'success': True,
#             'pump_status': pump_status,
#             'dump_status': dump_status
#         })

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})

# def fetch_stock_indicators(request):
#     """
#     Fetches MACD, RSI, and Bollinger Bands for a given stock symbol using yfinance.
#     """
#     # Extract the symbol from the request
#     symbol = request.GET.get("symbol", None)
#     if not symbol:
#         return JsonResponse({"success": False, "error": "No stock symbol provided."})
    
#     try:
#         # Ensure the symbol is uppercase and ends with ".NS"
#         symbol = symbol.upper()
#         if not symbol.endswith(".NS"):
#             symbol = f"{symbol}.NS"

#         # Fetch stock data using yfinance
#         stock = yf.Ticker(symbol)
#         stock_data = stock.history(period="6mo", interval="1d")

#         # Ensure data is available
#         if stock_data.empty or len(stock_data) < 26:
#             return JsonResponse({"success": False, "error": "Insufficient data for calculations."})

#         # MACD Calculation
#         stock_data['EMA12'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
#         stock_data['EMA26'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
#         stock_data['MACD'] = stock_data['EMA12'] - stock_data['EMA26']
#         stock_data['Signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
#         macd = stock_data.iloc[-1][['MACD', 'Signal']].to_dict()

#         # RSI Calculation
#         delta = stock_data['Close'].diff(1)
#         gain = delta.where(delta > 0, 0)
#         loss = -delta.where(delta < 0, 0)
#         avg_gain = gain.rolling(window=14).mean()
#         avg_loss = loss.rolling(window=14).mean()
#         rs = avg_gain / avg_loss
#         stock_data['RSI'] = 100 - (100 / (1 + rs))
#         rsi = stock_data.iloc[-1]['RSI']

#         # Bollinger Bands Calculation
#         stock_data['SMA20'] = stock_data['Close'].rolling(window=20).mean()
#         stock_data['UpperBand'] = stock_data['SMA20'] + (2 * stock_data['Close'].rolling(window=20).std())
#         stock_data['LowerBand'] = stock_data['SMA20'] - (2 * stock_data['Close'].rolling(window=20).std())
#         bollinger_bands = stock_data.iloc[-1][['SMA20', 'UpperBand', 'LowerBand']].to_dict()

#         # Return the results
#         return JsonResponse({
#             "success": True,
#             "data": {
#                 "MACD": macd,
#                 "RSI": rsi,
#                 "BollingerBands": bollinger_bands
#             }
#         }, safe=False)
    
#     except Exception as e:
#         return JsonResponse({"success": False, "error": f"An error occurred while processing the data: {str(e)}"})






