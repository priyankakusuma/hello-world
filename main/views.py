from django.shortcuts import render

# Create your views here.

def test():
    return "hello"

def home(request):
    return render(request, 'home.html')
