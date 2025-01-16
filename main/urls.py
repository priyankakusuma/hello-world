from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('fetch-nse-data/', views.fetch_nse_data, name='fetch_nse_data'),
    
    path('fetch-stock-price-inr/', views.fetch_stock_price_inr, name='fetch-stock-price-inr'),

    path('fetch-market-cap/', views.fetch_market_cap, name='fetch_market_cap'),
    path('fetch-stock-data/', views.fetch_stock_data, name='fetch_stock_data'),
    path('fetch-cagr-data/', views.fetch_cagr_data, name='fetch_cagr_data'),

   


]