from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm
from .forms import TopUpForm
from .models import Profile, Transaction


import requests
from django.conf import settings

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        recaptcha_response = request.POST.get("recaptcha-token")  # Updated
        # Verify reCAPTCHA
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.META.get('REMOTE_ADDR'),
        }
        recaptcha_verification = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data
        )
        result = recaptcha_verification.json()
        # Check reCAPTCHA response
        if not result.get("success"):
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
            return redirect("users:login")  # Redirect back to the login page
        # Authenticate user if reCAPTCHA is valid
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided, else default to user profile
            next_url = request.GET.get('next', reverse("users:user"))  # Simplified fallback
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "users/login.html")

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required(login_url='users:login')
def user(request):
    return render(request, "users/user.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', reverse("users:user"))
            return HttpResponseRedirect(next_url)
        else:
            messages.error(request, "Invalid Credentials.")
    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')

def user_view(request):
    profile = request.user.profile  # Get the logged-in user's profile
    return render(request, 'users/user.html', {'balance': profile.balance})

def user(request):
    profile = request.user.profile
    return render(request, 'users/user.html', {
        'user': request.user,
        'balance': profile.balance
    })

# Top-up balance view function
def top_up_balance(request):
    # Check if the request is a POST (form submission)
    if request.method == 'POST':  
        form = TopUpForm(request.POST)  # Create a form instance populated with POST data
        # Validate the form input
        if form.is_valid():  
            amount = form.cleaned_data['amount']  # Extract the cleaned amount from the form
            profile = request.user.profile  # Retrieve the profile associated with the logged-in user
            profile.balance += amount  # Add the entered amount to the user's current balance
            profile.save()  # Save the updated profile information to the database
            # Create a new transaction record for the top-up
            Transaction.objects.create(user=request.user, amount=amount)  
            # Add a success message to be displayed to the user
            messages.success(request, f"Successfully added ${amount:.2f} to your balance!")  
            return redirect('users:user')  # Redirect to the user profile page
        else:
            # Add an error message if the form is invalid
            messages.error(request, "Invalid input. Please try again.")  
    else:
        # If the request is a GET, create an empty form
        form = TopUpForm()  

    # Render the top-up page with the form
    return render(request, 'users/top_up_balance.html', {'form': form})  