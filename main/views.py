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





