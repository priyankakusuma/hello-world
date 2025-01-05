from django.shortcuts import render

def contact_view(request):
    if request.method == 'POST':
        # Process the form data (e.g., send an email)
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # ... send email logic ...
        return render(request, 'success.html')  # Display a success message

    return render(request, 'contact.html')