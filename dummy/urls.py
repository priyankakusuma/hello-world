from django.urls import path
from . import views 

urlpatterns = [
    path('dummy/', views.dummy_view, name='dummy'), 
]