from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('fetch-nse-data/', views.fetch_nse_data, name='fetch_nse_data'),
    
    path('fetch-stock-price-inr/', views.fetch_stock_price_inr, name='fetch-stock-price-inr'),

    path('fetch-market-cap/', views.fetch_market_cap, name='fetch_market_cap'),
    path('fetch-stock-data/', views.fetch_stock_data, name='fetch_stock_data'),
    path('fetch-cagr-data/', views.fetch_cagr_data, name='fetch_cagr_data'),
    path('fetch-volume-trader-data/', views.fetch_volume_trader_data, name='fetch_volume_trader_data'),
    # path('company/<str:symbol>/pump_or_dump/', views.fetch_pump_or_dump, name='fetch_pump_or_dump'),
    path('company/pump_or_dump/', views.fetch_pump_or_dump, name='fetch_pump_or_dump'),
    path('fetch-stock-indicators/', views.fetch_stock_indicators, name='fetch_stock_indicators'),
    path('fetch_kpi_data/', views.fetch_kpi_data, name='fetch_kpi_data'),

   


]