from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('fetch-nse-data/', views.fetch_nse_data, name='fetch_nse_data'),
    # path('company-details/<str:symbol>/', views.company_details, name='company_details'),
    path('fetch-stock-price-inr/', views.fetch_stock_price_inr, name='fetch-stock-price-inr'),

    path('fetch-market-cap/', views.fetch_market_cap, name='fetch_market_cap'),

   


]