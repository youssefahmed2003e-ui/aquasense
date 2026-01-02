import os
import random
import requests
import json
import logging
import google.generativeai as genai

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Course, Reservation
from .forms import SignUpForm

# Configure logging
logger = logging.getLogger(__name__)

# ==========================================
#               MAIN PAGES
# ==========================================

def home(request):
    """Renders the homepage."""
    return render(request, 'reservations/index.html')

def about(request):
    """Renders the about page."""
    return render(request, 'reservations/about.html')

def contact(request):
    """Renders the contact page - currently static."""
    return render(request, 'reservations/contact.html')

# ==========================================
#            COURSE & BOOKING
# ==========================================

def courses(request):
    """
    Displays the list of courses with advanced filtering and sorting.
    Handles 'q' (search), 'difficulty', and 'price_range' filtering.
    """
    courses = Course.objects.all().order_by('-is_popular', 'title')
    
    # --- Filter Logic ---
    query = request.GET.get('q')
    difficulty = request.GET.get('difficulty')
    price_range = request.GET.get('price_range')

    if query:
        courses = courses.filter(title__icontains=query) | courses.filter(description__icontains=query)
    
    if difficulty and difficulty != 'All':
        courses = courses.filter(difficulty=difficulty)
        
    if price_range:
        if price_range == 'low':
            courses = courses.filter(price__lt=100)
        elif price_range == 'mid':
            courses = courses.filter(price__gte=100, price__lte=500)
        elif price_range == 'high':
            courses = courses.filter(price__gt=500)

    # Remove duplicates if any
    courses = courses.distinct()

    return render(request, 'reservations/courses.html', {
        'courses': courses,
        'selected_difficulty': difficulty,
        'selected_price': price_range,
        'search_query': query
    })

def details(request, slug):
    """Displays specific course details based on the slug."""
    course = get_object_or_404(Course, slug=slug)
    return render(request, 'reservations/details.html', {'course': course})

@login_required
def book_course(request, course_id):
    """
    Handles the booking process.
    Creates a Reservation with 'Pending' status and redirects to dashboard.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        # Get data from form
        scheduled_date = request.POST.get('date')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        divers = request.POST.get('divers', 1)
        cert_level = request.POST.get('certification')
        medical = request.POST.get('medical_clearance') == 'on'

        Reservation.objects.create(
            user=request.user,
            course=course,
            status='Pending',
            scheduled_date=scheduled_date if scheduled_date else None,
            full_name=full_name,
            email=email,
            phone_number=phone,
            number_of_divers=divers,
            certification_level=cert_level,
            medical_clearance=medical
        )
        return redirect('dashboard')

    return render(request, 'reservations/checkout.html', {'course': course})

@login_required
def checkout(request):
    """Renders the checkout page (if used in future flows)."""
    return render(request, 'reservations/checkout.html')

@login_required
def dashboard(request):
    """Displays the user's dashboard with their list of reservations."""
    reservations = Reservation.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'reservations/dashboard.html', {'reservations': reservations})

# ==========================================
#           AUTHENTICATION
# ==========================================

def login_view(request):
    """
    Handles user login.
    Redirects Admins to /admin/ and regular users to /home/.
    """
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Admin Security Redirect
            if user.is_staff or user.is_superuser:
                return redirect('/admin/')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'reservations/login.html', {'form': form})

def signup(request):
    """Handles user registration."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'reservations/signup.html', {'form': form})

def logout_view(request):
    """Logs the user out and redirects to home."""
    logout(request)
    return redirect('home')

# ==========================================
#        PASSWORD RESET (OTP)
# ==========================================

def send_otp_email(email, otp):
    """
    Helper function to send OTP email via Resend API.
    Returns True if successful, False otherwise.
    """
    api_key = settings.RESEND_API_KEY
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "onboarding@resend.dev",
        "to": [email],
        "subject": "AquaSense Password Reset OTP",
        "html": f"<p>Your OTP for password reset is: <strong>{otp}</strong></p>"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            # Fallback for development logging
            print(f"\n{'='*50}")
            print(f"DEV MODE - Resend API Status: {response.status_code}")
            print(f"OTP for {email}: {otp}")
            print(f"{'='*50}\n")
            return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def forgot_password(request):
    """
    Step 1: Ask for email and send OTP.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            
            # Store in session
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            request.session['otp_attempts'] = 0
            
            if send_otp_email(email, otp):
                messages.success(request, 'OTP generated! Check your email (or terminal in Dev mode).')
                return redirect('verify_otp')
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
        except User.DoesNotExist:
            messages.error(request, 'Email not found.')
    return render(request, 'reservations/forgot_password.html')

def verify_otp(request):
    """
    Step 2: Verify the OTP entered by the user.
    """
    if 'reset_email' not in request.session or 'reset_otp' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        otp_actual = request.session.get('reset_otp')
        attempts = request.session.get('otp_attempts', 0)
        
        if otp_entered == otp_actual:
            request.session['reset_verified'] = True
            return redirect('reset_password')
        else:
            attempts += 1
            request.session['otp_attempts'] = attempts
            if attempts >= 3:
                messages.error(request, 'Too many failed attempts. Please login again.')
                # Clear session
                for key in ['reset_email', 'reset_otp', 'otp_attempts']:
                    if key in request.session: del request.session[key]
                return redirect('login')
            else:
                messages.error(request, f'Invalid OTP. You have {3 - attempts} attempts left.')
    
    return render(request, 'reservations/verify_otp.html')

def reset_password(request):
    """
    Step 3: Allow user to set a new password.
    """
    if not request.session.get('reset_verified'):
        return redirect('login')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password:
            email = request.session.get('reset_email')
            try:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                
                # Cleanup Session
                for key in ['reset_email', 'reset_otp', 'otp_attempts', 'reset_verified']:
                    if key in request.session: del request.session[key]
                
                messages.success(request, 'Password reset successfully. Please login.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
        else:
            messages.error(request, 'Passwords do not match.')
            
    return render(request, 'reservations/reset_password.html')

# ==========================================
#           AI CHAT API
# ==========================================

@csrf_exempt
def chat_view(request):
    """
    API endpoint for the Gemini AI Chatbot.
    Expects a POST request with JSON body {'message': '...'}.
    """
    if request.method == 'POST':
        try:
            # Log incoming request
            logger.info("Chat request received")
            
            # Get and validate API key
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables")
                return JsonResponse({'error': 'API key not configured.'}, status=500)
            
            logger.info(f"API Key found: {api_key[:10]}...")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Parse request body
            data = json.loads(request.body)
            user_message = data.get('message', '')
            logger.info(f"User message: {user_message}")
            
            # --- System Prompt Configuration ---
            system_prompt = """
            You are the AI Dive Advisor for AquaSense, a premier diving center.
            Your goal is to be helpful, friendly, and professional.
            
            Info:
            - Location: Cairo , Egypt.
            - Contact: +1 (123) 456-7890.
            
            Courses:
            1. Open Water Diver: $350 (Beginner)
            2. Advanced Diving Skills: $450 (Intermediate)
            3. Coral Reef Exploration: $200 (For everyone)
            4. Wreck Diving: $500 (Advanced)
            
            Keep responses concise.
            """
            
            # Use the latest stable model
            logger.info("Initializing Gemini model...")
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            logger.info("Starting chat...")
            chat = model.start_chat(history=[
                {'role': 'user', 'parts': [system_prompt]},
                {'role': 'model', 'parts': ["Understood. Ready to help."]}
            ])
            
            logger.info("Sending message to Gemini...")
            response = chat.send_message(user_message)
            
            logger.info(f"AI response: {response.text[:50]}...")
            return JsonResponse({'response': response.text})
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
        except Exception as e:
            logger.error(f"Error in chat_view: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
