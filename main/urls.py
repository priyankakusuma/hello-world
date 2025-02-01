from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('fetch-nse-data/', views.fetch_nse_data, name='fetch_nse_data'),
  
    path('fetch-kpi-data/', views.fetch_kpi_data, name='fetch_kpi_data'),

   


]