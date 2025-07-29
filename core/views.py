# ewaste_backend/core/views.py

from django.shortcuts import render, redirect
from django.core.mail import send_mail, get_connection
from django.conf import settings # Crucial for accessing settings variables
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from .forms import PickupRequestForm
from .models import PickupRequest

import ssl
import certifi
import traceback
import google.generativeai as genai
from .forms import PickupRequestForm, ContactForm 
from .models import PickupRequest, ContactMessage 

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            contact_message.save()

            # Optional: Send an email notification to yourself (admin)
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                connection = get_connection(ssl_context=ssl_context)
                send_mail(
                    subject=f"New Contact Message: {contact_message.subject}",
                    message=(
                        f"From: {contact_message.name} ({contact_message.email})\n"
                        f"Subject: {contact_message.subject}\n\n"
                        f"Message:\n{contact_message.message}"
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[settings.ADMIN_EMAIL], # You'll need to define ADMIN_EMAIL in settings.py
                    connection=connection,
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent successfully!')
            except Exception as e:
                print(f"[EMAIL ERROR] Failed to send contact notification email: {e}")
                traceback.print_exc()
                messages.warning(request, 'Your message was saved, but we could not send a notification email.')

            return redirect('contact') # Redirect to the same page or a thank you page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm() # Create an empty form for GET requests

    context = {'form': form}
    return render(request, 'contact.html', context)

# ---------------------------
# 📄 Static Page Views
# ---------------------------

def homepage(request):
    return render(request, 'index.html')

def services(request):
    return render(request, 'services.html')

def about(request):
    return render(request, 'about.html')

def team(request):
    return render(request, 'team.html')

def contact(request):
    return render(request, 'contact.html')

def data_destruction(request):
    return render(request, 'data_destruction.html')

def refurbishment(request): # Renamed from 're' context
    return render(request, 'recycling_refurbishment.html')


# ---------------------------
# 🧑‍💻 User Authentication
# ---------------------------

@csrf_protect
def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('signup')

        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = name
        user.save()

        if user.id:
            messages.success(request, f"Welcome {name}, your account was created successfully!")
            return redirect('login')
        else:
            messages.error(request, "Signup failed. Please try again.")

    return render(request, 'signup.html')


@csrf_protect
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('homepage')
        else:
            messages.error(request, "Invalid email or password. Please try again.")

    return render(request, 'login.html')


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ---------------------------
# 🚚 Pickup Request Handling
# ---------------------------

def pickup(request):
    # Prepare context with initial form or form with POST data
    context = {
        'form': PickupRequestForm(),
        # REMOVED: 'MAPPLS_API_KEY': settings.MAPPLS_API_KEY, # No longer passing API key since map is not desired
    }

    if request.method == 'POST':
        form = PickupRequestForm(request.POST)
        context['form'] = form # Update form in context with POST data for re-rendering

        if form.is_valid():
            pickup_request = form.save(commit=False) # Get the instance but don't save yet

            # The latitude and longitude fields were related to map, now assume they are not present
            # or will be handled differently if you re-introduce coordinates without a map later.
            # For now, if the form still has lat/lon fields, they will just be saved as whatever is submitted.

            pickup_request.save() # Save the request

            # --- Email Sending ---
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                connection = get_connection(ssl_context=ssl_context)

                send_mail(
                    subject='E-Waste Pickup Confirmation',
                    message=(
                        f"Dear {form.cleaned_data['name']},\n\n"
                        "Thank you for your e-waste pickup request. We will reach out soon."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[form.cleaned_data['email']],
                    connection=connection,
                    fail_silently=False,
                )
                messages.success(request, 'Your pickup request has been submitted successfully!')
                return redirect('reqs') # Redirect on success
            except Exception as e:
                print(f"[EMAIL ERROR] Failed to send email: {e}")
                traceback.print_exc()
                messages.error(request, 'Email could not be sent. Please try again.')
                # If email fails, re-render the page with the form and the error message
                return render(request, 'pickup.html', context)
        else:
            # Form is NOT valid; errors will be displayed by the template
            messages.error(request, 'Please correct the errors below.')

    # Render the form (for GET requests or invalid POST requests)
    return render(request, 'pickup.html', context)


def reqs(request):
    return render(request, 'reqs.html')


# ---------------------------
# 📋 Admin View
# ---------------------------

def list_pickup_requests(request):
    requests = PickupRequest.objects.all().order_by('-created_at')
    return render(request, 'list_pickup_requests.html', {'pickup_requests': requests})


# ---------------------------
# 🤖 Gemini Chatbot Integration
# ---------------------------

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '')

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        # Removed the direct settings.GEMINI_API_KEY access check here for cleaner view
        # assuming it's correctly handled in settings.py loading.
        # It's better to let genai.configure fail if key is bad or missing.
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY) # Access GEMINI_API_KEY from settings
            model = genai.GenerativeModel('gemini-1.5-flash')
            chat_session = model.start_chat(history=[])
            response = chat_session.send_message(user_message)
            chatbot_reply = response.text

            return JsonResponse({'response': chatbot_reply})

        except Exception as e:
            print(f"[GEMINI ERROR] {e}")
            traceback.print_exc()
            # Provide a more user-friendly error if API key is truly the problem
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                return JsonResponse(
                    {'error': 'Gemini API key is invalid or not configured on the server.'},
                    status=500
                )
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)