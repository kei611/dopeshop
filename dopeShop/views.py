from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def contact(request):
    return render(request, 'contact.html')

def termsAndPrivacy(request):
    return render(request, 'terms_and_privacy.html')