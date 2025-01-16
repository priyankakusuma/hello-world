from sqlite3 import Row
from django.shortcuts import render
import requests
import pandas as pd
import io
from django.http import JsonResponse
# import yfinance as yf

# Create your views here.

def test():
    return "hello"

def home(request):
    return render(request, 'home.html')



def fetch_stock_data(request):
    symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        # Ensure the symbol is uppercase
        symbol = symbol.upper()

        # Append .NS if necessary for Indian stocks
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # Fetch stock data using yfinance
        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="1y")  # Fetch 1 year data
        
        if stock_data.empty:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

        # Find current price, 52-week high, and 52-week low
        current_price = stock_data['Close'].iloc[-1]
        high_52_week = stock_data['High'].max()
        low_52_week = stock_data['Low'].min()

        # Prepare response data
        response_data = {
            'success': True,
            'current_price': round(current_price, 2),
            'high_52_week': round(high_52_week, 2),
            'low_52_week': round(low_52_week, 2),
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})




def fetch_market_cap(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({"success": False, "error": "Symbol not provided."}, status=400)

    # Automatically add .NS to the symbol if it's not already there
    if not symbol.endswith('.NS'):
        symbol = f"{symbol}.NS"

    try:
        # Fetch company data using yfinance
        company = yf.Ticker(symbol)

        # Get the market capitalization (in the form of a number)
        market_cap = company.info.get("marketCap")
        
        if market_cap is None:
            return JsonResponse({"success": False, "error": "Market capitalization not available."}, status=404)

        # Convert the market cap to crores (₹1 crore = ₹10,000,000)
        market_cap_in_crores = market_cap / 10**7

        # Format the market cap to 2 decimal places
        # market_cap_in_crores = round(market_cap_in_crores, 2)
        # formatted_market_cap = f"{market_cap_in_crores} Crore"
        formatted_market_cap = f"{market_cap_in_crores:,.2f} Cr"

        # Return the market cap in INR or as is
        return JsonResponse({"success": True, "market_cap":formatted_market_cap})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)






import yfinance as yf

def fetch_stock_price_inr(request):
    symbol = request.GET.get('symbol')  # Get the stock symbol from query parameters
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        # Ensure the symbol is uppercase
        symbol = symbol.upper()

        # Check if the symbol is for an Indian stock; append .NS if necessary

        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # Fetch stock data using yfinance
        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="1d")
        
        # Log the raw stock data for debugging
        print(f"Raw stock data for {symbol}: {stock_data}")
        
        if stock_data.empty:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})
        
        # Extract the closing price in INR (yfinance provides the price in local currency of the stock exchange)
        stock_price_inr = stock_data['Close'].iloc[-1]
        print(f"Extracted stock price (INR) for {symbol}: {stock_price_inr}")

        return JsonResponse({'success': True, 'price': round(stock_price_inr, 2)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching stock price: {str(e)}"})




def fetch_nse_data(request):
    """
    Fetches equity data from NSE and returns a list of objects with 'name' and 'symbol'.
    """
    nse_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

    # Headers for the request
    headers = { 
         
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        # Fetch the data
        with requests.Session() as session:
            session.headers.update(headers)
            response = session.get(nse_url)
            response.raise_for_status()  # Raise an error for bad HTTP status

        # print(f"Response Status Code: {response.status_code}")

        # Load CSV content into pandas DataFrame
        df_nse = pd.read_csv(io.BytesIO(response.content))

        # print(f"Columns in CSV: {df_nse.columns}")
        


        # Ensure the required columns exist
        if "SYMBOL" not in df_nse.columns or "NAME OF COMPANY" not in df_nse.columns:
            return JsonResponse({"success": False, "error": "Missing required columns in CSV file."})

        # Create a list of dictionaries
        company_list = [{"name": row["NAME OF COMPANY"],"symbol": row["SYMBOL"]} for _, row in df_nse.iterrows()]
        company_dict = {company["name"]: company["symbol"] for company in company_list}
        print(df_nse.head())
      
        return JsonResponse({"success": True, "data": company_dict}, safe=False)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"success": False, "error": str(e)})

    except Exception as e:
        return JsonResponse({"success": False, "error": "An error occurred while processing the data: " + str(e)})


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

#         # Calculate the 5-Year CAGR
#         start_price_5y = stock_data['Close'].iloc[0]
#         end_price_5y = stock_data['Close'].iloc[-1]
#         cagr_5y = ((end_price_5y / start_price_5y) ** (1 / 5) - 1) * 100

#         # Calculate the 3-Year CAGR (using last 3 years of data)
#         stock_data_3y = stock_data.loc[stock_data.index >= (stock_data.index[-1] - pd.DateOffset(years=3))]
#         # stock_data_3y = stock_data.tail(756)  # Approx. 3 years of trading days
#         start_price_3y = stock_data_3y['Close'].iloc[0]
#         end_price_3y = stock_data_3y['Close'].iloc[-1]
#         cagr_3y = ((end_price_3y / start_price_3y) ** (1 / 3) - 1) * 100
#         print(f"5-Year CAGR: {cagr_5y}")
#         print(f"3-Year CAGR: {cagr_3y}")
#         # print(stock_data.head())
#         # print(stock_data.tail())
#         # print(stock_data_3y.head())
#         # print(stock_data_3y.tail())
#         # print("Filtered 3-Year Data:")
#         # print(stock_data_3y)

#         # print(f"Start Price (3Y): {start_price_3y}, End Price (3Y): {end_price_3y}")
#         # print(f"3-Year CAGR Calculation: (({end_price_3y} / {start_price_3y}) ** (1 / 3) - 1) * 100")



#         return JsonResponse({
#             'success': True,
#             'cagr_5y': round(cagr_5y, 2),
#             'cagr_3y': round(cagr_3y, 2),
#         })
            

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})



def fetch_cagr_data(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({'success': False, 'error': 'Symbol not provided'})

    try:
        # Ensure symbol is uppercase and append ".NS" for Indian stocks if not already present
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        # Fetch stock data using yfinance
        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="5y")  # Fetch 5 years of data

        if stock_data.empty:
            return JsonResponse({'success': False, 'error': f"No data found for symbol: {symbol}. The stock may be delisted or unavailable."})

        # Calculate the 5-Year CAGR
        start_price_5y = stock_data['Close'].iloc[0]
        end_price_5y = stock_data['Close'].iloc[-1]
        cagr_5y = ((end_price_5y / start_price_5y) ** (1 / 5) - 1) * 100

        # Calculate the 3-Year CAGR (using last 3 years of data)
        stock_data_3y = stock_data.loc[stock_data.index >= (stock_data.index[-1] - pd.DateOffset(years=3))]  # 3 years of data
        if stock_data_3y.empty:
            return JsonResponse({'success': False, 'error': f"Not enough data to calculate 3-Year CAGR for {symbol}"})
        
        start_price_3y = stock_data_3y['Close'].iloc[0]
        end_price_3y = stock_data_3y['Close'].iloc[-1]
        cagr_3y = ((end_price_3y / start_price_3y) ** (1 / 3) - 1) * 100
        print(f"Start Date (3Y): {stock_data_3y.index[0]}")
        print(f"End Date (3Y): {stock_data_3y.index[-1]}")
        print(f"Start Price (3Y): {start_price_3y}, End Price (3Y): {end_price_3y}")
        print(f"3-Year CAGR Calculation: (({end_price_3y} / {start_price_3y}) ** (1 / 3) - 1) * 100 = {cagr_3y}")

        return JsonResponse({
            'success': True,
            'cagr_5y': round(cagr_5y, 2),
            'cagr_3y': round(cagr_3y, 2),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error fetching data: {str(e)}"})




