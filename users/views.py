from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm
from .forms import TopUpForm
from .models import Profile, Transaction

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from chipin.models import Event
from users.models import Profile, Transaction
from users.models import Transaction


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

@login_required
def user(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "users/user.html", {
        'user': request.user,
        'balance': request.user.profile.balance,
        'transactions': transactions,
    })

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

@transaction.atomic
def transfer_funds(request, group_id, event_id):
    # Get the event and ensure it’s valid
    event = get_object_or_404(Event, id=event_id, group_id=group_id)
    if event.archived:
        messages.error(request, "This event is already archived.")
        return redirect('chipin:group_detail', group_id=group_id)

    # Ensure the current user is the group admin
    if request.user != event.group.admin:
        messages.error(request, "You are not authorized to transfer funds for this event.")
        return redirect('chipin:group_detail', group_id=group_id)

    # Calculate shares and validate balances
    members = event.group.members.exclude(id=request.user.id)
    total_share = 0
    for member in members:
        profile = member.profile
        share = event.share_amount
        if profile.balance < share:
            messages.error(request, f"{member.username} has insufficient balance.")
            return redirect('chipin:group_detail', group_id=group_id)
        profile.balance -= share
        profile.save()
        total_share += share
        Transaction.objects.create(user=member, event=event, amount=-share)

    # Update the admin's balance and log the transaction
    admin_profile = request.user.profile
    admin_profile.balance += total_share
    admin_profile.save()
    Transaction.objects.create(user=request.user, event=event, amount=total_share)

    # Archive the event
    event.archived = True
    event.save()

    messages.success(request, "Funds transferred successfully and the event has been archived.")
    return redirect('chipin:group_detail', group_id=group_id)