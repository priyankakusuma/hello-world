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

        # Return the market cap in INR or as is
        return JsonResponse({"success": True, "market_cap": market_cap})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)




# Function to fetch market cap for the selected symbol using yfinance
# def fetch_market_cap(request):
#     symbol = request.GET.get('symbol')
#     if not symbol:
#         return JsonResponse({"success": False, "error": "Symbol not provided."}, status=400)

#     try:
#         # Fetch company data using yfinance
#         company = yf.Ticker(symbol)

#         # Get the market capitalization (in the form of a number)
#         market_cap = company.info.get("marketCap")
        
#         if market_cap is None:
#             return JsonResponse({"success": False, "error": "Market capitalization not available."}, status=404)

#         # Return the market cap in INR or as is
#         return JsonResponse({"success": True, "market_cap": market_cap})

#     except Exception as e:
#         return JsonResponse({"success": False, "error": str(e)}, status=500)


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





