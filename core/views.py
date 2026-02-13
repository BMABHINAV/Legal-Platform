from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
import json

from .models import (
    User, ProviderProfile, ServiceListing, AnalysisResult, ChatSession, 
    ChatMessage, Booking, Review, Payment, ProviderAvailability, 
    ProviderTimeOff, FavoriteProvider, ConsultationNote
)
from .forms import SignUpForm, LoginForm, ProviderSignUpForm, DocumentUploadForm, ChatForm
from .mock_data import TRIAGE_QUESTIONS, LEGAL_CATEGORIES
from .incentive_rules import get_provider_tier, get_next_tier, INCENTIVE_RULES, REWARD_TIERS
from .gemini_service import analyze_document_with_ai, chat_with_legal_ai, extract_text_from_file


def get_providers_queryset():
    """Get verified providers queryset with annotations"""
    return ProviderProfile.objects.filter(
        user__verification_status='verified',
        user__is_active=True
    ).select_related('user').annotate(
        computed_review_count=Count('reviews'),
        computed_avg_rating=Avg('reviews__rating')
    )


def provider_to_dict(provider):
    """Convert ProviderProfile to dictionary format for templates"""
    # Check availability status
    is_available = provider.availability_status == 'available'
    
    return {
        'id': str(provider.id),
        'user_id': str(provider.user.id),
        'name': provider.user.get_full_name() or provider.user.username,
        'email': provider.user.email,
        'phone': provider.user.phone or '',
        'provider_type': provider.provider_type,
        'provider_type_display': provider.get_provider_type_display(),
        'bar_registration_number': provider.bar_registration_number or '',
        'specializations': provider.specializations or [],
        'languages': provider.languages or ['English'],
        'years_of_experience': provider.years_of_experience,
        'bio': provider.bio or '',
        'rating': float(provider.rating) if provider.rating else 0,
        'reviews_count': getattr(provider, 'computed_review_count', None) or provider.review_count or 0,
        'hourly_rate': float(provider.hourly_rate) if provider.hourly_rate else 1500,
        'is_available': is_available,
        'availability_status': provider.get_availability_status_display(),
        'incentive_points': provider.incentive_points,
        'tier': get_provider_tier(provider.incentive_points),
        'profile_image': provider.user.profile_image.url if provider.user.profile_image else None,
        'verified': provider.user.verification_status == 'verified',
        'verification_status': provider.user.verification_status,
        'location': f"{provider.city}, {provider.state}" if provider.city else 'India',
        'city': provider.city or '',
        'state': provider.state or '',
        'completed_cases': provider.completed_cases,
        'response_time': provider.response_time or 'Within 24 hours',
        'review_count': provider.review_count or 0,
        'profile': provider,  # Keep reference for database operations
    }


def home(request):
    """Home page view"""
    # Get featured providers (top 3 by rating)
    providers = get_providers_queryset().order_by('-rating')[:6]
    featured_providers = [provider_to_dict(p) for p in providers]
    
    # If no real providers, show message
    if not featured_providers:
        featured_providers = []
    
    # Get stats for the home page
    total_providers = ProviderProfile.objects.filter(user__verification_status='verified').count()
    total_cases = Booking.objects.filter(status='completed').count()
    total_users = User.objects.filter(is_active=True).count()
    total_analyses = AnalysisResult.objects.count()
    
    # Calculate average rating
    avg_rating = ProviderProfile.objects.filter(
        user__verification_status='verified'
    ).aggregate(avg=Avg('rating'))['avg'] or 4.8
    
    context = {
        'featured_providers': featured_providers,
        'legal_categories': LEGAL_CATEGORIES,
        'total_providers': total_providers or 500,  # Show placeholder if empty
        'total_cases': total_cases or 10000,
        'total_users': total_users or 50000,
        'total_analyses': total_analyses or 25000,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'core/home.html', context)


def about(request):
    """About page view"""
    return render(request, 'core/about.html')


def signup_view(request):
    """User signup view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = SignUpForm()
    
    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'core/profile.html')


def providers_list(request):
    """List all providers with filtering"""
    # Start with verified providers
    providers_qs = get_providers_queryset()
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category = request.GET.get('category', '')
    provider_type = request.GET.get('type', '')
    sort_by = request.GET.get('sort', 'rating')
    price_range = request.GET.get('price', 'all')
    language = request.GET.get('language', '')
    
    # Apply filters using Django ORM
    if search_query:
        providers_qs = providers_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query)
        )
    
    if provider_type:
        providers_qs = providers_qs.filter(provider_type=provider_type)
    
    if price_range != 'all':
        if price_range == 'under-2000':
            providers_qs = providers_qs.filter(hourly_rate__lt=2000)
        elif price_range == '2000-4000':
            providers_qs = providers_qs.filter(hourly_rate__gte=2000, hourly_rate__lte=4000)
        elif price_range == 'above-4000':
            providers_qs = providers_qs.filter(hourly_rate__gt=4000)
    
    # Apply sorting
    if sort_by == 'rating':
        providers_qs = providers_qs.order_by('-rating')
    elif sort_by == 'experience':
        providers_qs = providers_qs.order_by('-years_of_experience')
    elif sort_by == 'price-low':
        providers_qs = providers_qs.order_by('hourly_rate')
    elif sort_by == 'price-high':
        providers_qs = providers_qs.order_by('-hourly_rate')
    elif sort_by == 'reviews':
        providers_qs = providers_qs.order_by('-review_count')
    
    # Convert to list of dictionaries
    providers = [provider_to_dict(p) for p in providers_qs]
    
    # Apply JSONField filters in Python (SQLite doesn't support contains on JSON)
    if category:
        providers = [p for p in providers if category.lower() in [s.lower() for s in (p.get('specializations') or [])]]
    
    if language:
        providers = [p for p in providers if language.lower() in [l.lower() for l in (p.get('languages') or [])]]
    
    # Pagination
    paginator = Paginator(providers, 12)  # 12 providers per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'providers': page_obj,
        'page_obj': page_obj,
        'legal_categories': LEGAL_CATEGORIES,
        'search_query': search_query,
        'selected_category': category,
        'selected_type': provider_type,
        'sort_by': sort_by,
        'price_range': price_range,
        'selected_language': language,
        'languages': ['English', 'Hindi', 'Marathi', 'Tamil', 'Telugu', 'Gujarati', 'Bengali', 'Punjabi', 'Kannada', 'Malayalam'],
        'total_count': len(providers),
    }
    return render(request, 'core/providers.html', context)


def provider_detail(request, provider_id):
    """Provider detail view"""
    # Try to get provider from database - first try by provider ID, then by user ID
    try:
        # Try to get by provider profile ID first
        try:
            provider_profile = ProviderProfile.objects.select_related('user').get(id=provider_id)
        except ProviderProfile.DoesNotExist:
            # Fallback to user ID lookup
            provider_profile = ProviderProfile.objects.select_related('user').get(user__id=provider_id)
        
        provider = provider_to_dict(provider_profile)
        
        # Get services for this provider
        services = ServiceListing.objects.filter(provider=provider_profile, is_active=True)
        
        # Get reviews
        reviews = Review.objects.filter(provider=provider_profile).select_related('user').order_by('-created_at')[:10]
        
        # Get availability
        availability = ProviderAvailability.objects.filter(
            provider=provider_profile, 
            is_available=True
        ).order_by('day_of_week', 'start_time')
        
        # Check if user has favorited this provider
        is_favorite = False
        if request.user.is_authenticated:
            is_favorite = FavoriteProvider.objects.filter(
                user=request.user, 
                provider=provider_profile
            ).exists()
        
        context = {
            'provider': provider,
            'provider_profile': provider_profile,
            'services': services,
            'reviews': reviews,
            'availability': availability,
            'is_favorite': is_favorite,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        }
        return render(request, 'core/provider_detail.html', context)
        
    except ProviderProfile.DoesNotExist:
        messages.error(request, 'Provider not found')
        return redirect('providers')


def become_provider(request):
    """Become a provider page"""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in first to become a provider.')
            return redirect('login')
        
        form = ProviderSignUpForm(request.POST)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.languages = [lang.strip() for lang in form.cleaned_data['languages'].split(',')]
            provider.save()
            
            request.user.role = 'provider'
            request.user.save()
            
            messages.success(request, 'Your provider profile has been created!')
            return redirect('provider_dashboard')
    else:
        form = ProviderSignUpForm()
    
    return render(request, 'core/become_provider.html', {'form': form})


@login_required
def provider_dashboard(request):
    """Provider dashboard view"""
    try:
        provider = request.user.provider_profile
    except ProviderProfile.DoesNotExist:
        messages.warning(request, 'You need to create a provider profile first.')
        return redirect('become_provider')
    
    tier = provider.get_tier()
    next_tier_info = get_next_tier(provider.incentive_points)
    
    # Calculate progress percentage if there's a next tier
    if next_tier_info:
        current_points = provider.incentive_points
        next_min = next_tier_info['tier']['min_points']
        tier_min = tier.get('min_points', 0)
        if next_min > tier_min:
            progress = int(((current_points - tier_min) / (next_min - tier_min)) * 100)
            next_tier_info['progress_percent'] = min(progress, 100)
        else:
            next_tier_info['progress_percent'] = 0
    
    context = {
        'provider': provider,
        'tier': tier,
        'next_tier': next_tier_info,
        'incentive_rules': INCENTIVE_RULES,
    }
    return render(request, 'core/provider_dashboard.html', context)


def leaderboard(request):
    """Leaderboard page"""
    # Get providers sorted by incentive points from database
    providers_qs = get_providers_queryset().order_by('-incentive_points')[:20]
    
    # Convert to list and add rank
    ranked_providers = []
    for i, provider in enumerate(providers_qs):
        provider_dict = provider_to_dict(provider)
        provider_dict['rank'] = i + 1
        ranked_providers.append(provider_dict)
    
    top_three = ranked_providers[:3]
    rest_of_leaders = ranked_providers[3:20]
    
    context = {
        'top_three': top_three,
        'rest_of_leaders': rest_of_leaders,
        'reward_tiers': REWARD_TIERS,
    }
    return render(request, 'core/leaderboard.html', context)


def incentives(request):
    """Incentives page"""
    context = {
        'incentive_rules': INCENTIVE_RULES,
        'reward_tiers': REWARD_TIERS,
    }
    return render(request, 'core/incentives.html', context)


def document_analyzer(request):
    """Document analyzer page"""
    form = DocumentUploadForm()
    
    context = {
        'form': form,
        'supported_types': [
            'Rental Agreement',
            'Employment Contract',
            'Sale Deed',
            'Power of Attorney',
            'Loan Agreement',
            'NDA',
            'Legal Notice',
            'Partnership Deed',
        ],
    }
    return render(request, 'core/document_analyzer.html', context)


@require_POST
def analyze_document(request):
    """Handle document upload and analysis"""
    form = DocumentUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form data'}, status=400)
    
    uploaded_file = request.FILES['document']
    filename = uploaded_file.name
    
    # Extract text from file
    text = extract_text_from_file(uploaded_file)
    
    if not text or len(text.strip()) == 0:
        return JsonResponse({'error': 'Could not extract text from file'}, status=400)
    
    # Analyze document
    analysis = analyze_document_with_ai(text, filename)
    
    # Save analysis result if user is logged in
    if request.user.is_authenticated:
        AnalysisResult.objects.create(
            user=request.user,
            file_name=analysis['file_name'],
            file_type=analysis['file_type'],
            document_type=analysis['document_type'],
            health_score=analysis['health_score'],
            risk_level=analysis['risk_level'],
            summary=analysis['summary'],
            risks=analysis['risks'],
            recommendations=analysis['recommendations'],
            suggested_lawyer_categories=analysis['suggested_lawyer_categories'],
        )
    
    return JsonResponse(analysis)


def document_results(request):
    """Document analysis results page"""
    # Results are passed via session or query params
    analysis_id = request.GET.get('id')
    
    if analysis_id:
        try:
            analysis = AnalysisResult.objects.get(id=analysis_id)
            context = {'analysis': analysis}
        except AnalysisResult.DoesNotExist:
            context = {'analysis': None}
    else:
        context = {'analysis': None}
    
    return render(request, 'core/document_results.html', context)


def ai_assistant(request):
    """AI Assistant chat page"""
    return render(request, 'core/ai_assistant.html')


@require_POST
@csrf_exempt
def chat_api(request):
    """Handle chat messages"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        history = data.get('history', [])
        lang_code = data.get('lang_code', request.LANGUAGE_CODE or 'en')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        result = chat_with_legal_ai(history, message, lang_code=lang_code)
        
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_exempt
def htmx_chat(request):
    """HTMX-powered chat endpoint - returns HTML for instant swap"""
    try:
        message = request.POST.get('message', '')
        history_json = request.POST.get('history', '[]')
        lang_code = request.POST.get('lang_code', request.LANGUAGE_CODE or 'en')
        
        if not message:
            return HttpResponse('<div class="alert alert-error">Message is required</div>', status=400)
        
        try:
            history = json.loads(history_json)
        except:
            history = []
        
        result = chat_with_legal_ai(history, message, lang_code=lang_code)
        
        if result.get('success'):
            ai_response = result.get('text', 'No response')
            provider = result.get('ai_provider', 'AI')
            provider_badge = ''
            if 'llama' in provider.lower() or 'groq' in provider.lower():
                provider_badge = '<span class="badge badge-success badge-xs ml-2">⚡ Llama 3.1</span>'
            
            html = f'''
            <div class="chat chat-start" x-data x-init="$el.scrollIntoView({{ behavior: 'smooth' }})">
                <div class="chat-image avatar placeholder">
                    <div class="bg-primary text-primary-content rounded-xl w-10">
                        <span class="text-xl">🤖</span>
                    </div>
                </div>
                <div class="chat-header">
                    Legal AI {provider_badge}
                </div>
                <div class="chat-bubble chat-bubble-primary">{ai_response}</div>
            </div>
            '''
            return HttpResponse(html)
        else:
            error = result.get('error', 'Unknown error')
            return HttpResponse(f'<div class="alert alert-error">{error}</div>')
            
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-error">Error: {str(e)}</div>', status=500)


@require_GET
def htmx_check_availability(request, provider_id):
    """HTMX endpoint to check provider availability for a given date"""
    date_str = request.GET.get('date', '')
    
    if not date_str:
        return HttpResponse('''
            <select name="time" class="select select-bordered w-full" required>
                <option value="">Select date first</option>
            </select>
        ''')
    
    try:
        # Parse the date
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_of_week = selected_date.weekday()  # 0=Monday, 6=Sunday
        
        # Get provider - try by provider profile ID first, then by user ID
        try:
            provider = ProviderProfile.objects.get(id=provider_id)
        except ProviderProfile.DoesNotExist:
            provider = ProviderProfile.objects.get(user__id=provider_id)
        
        # Get provider's availability for this day
        availability = ProviderAvailability.objects.filter(
            provider=provider,
            day_of_week=day_of_week,
            is_available=True
        )
        
        # Check if provider has time off
        has_time_off = ProviderTimeOff.objects.filter(
            provider=provider,
            date=selected_date
        ).exists()
        
        if has_time_off:
            return HttpResponse('''
                <select name="time" class="select select-bordered w-full" disabled>
                    <option value="">Provider unavailable on this date</option>
                </select>
                <div class="text-xs text-error mt-1">✗ Provider is not available on this day</div>
            ''')
        
        # Get already booked slots for this date
        booked_times = Booking.objects.filter(
            provider=provider,
            scheduled_date=selected_date,
            status__in=['pending', 'payment_pending', 'confirmed', 'accepted', 'in-progress']
        ).values_list('scheduled_time', flat=True)
        
        # Generate available time slots
        available_slots = []
        for slot in availability:
            current_time = slot.start_time
            while current_time < slot.end_time:
                if current_time not in booked_times:
                    available_slots.append(current_time.strftime('%H:%M'))
                # Move to next 30-minute slot
                current_datetime = datetime.combine(selected_date, current_time)
                current_datetime += timedelta(minutes=30)
                current_time = current_datetime.time()
        
        if not available_slots:
            # Default slots if provider hasn't set availability
            default_slots = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00']
            available_slots = [s for s in default_slots if datetime.strptime(s, '%H:%M').time() not in booked_times]
        
        # Build HTML for time slots
        options = '<option value="">Select time</option>'
        for slot in available_slots:
            hour, minute = map(int, slot.split(':'))
            display = f"{hour}:{minute:02d} AM" if hour < 12 else f"{hour-12 if hour > 12 else 12}:{minute:02d} PM"
            options += f'<option value="{slot}">{display}</option>'
        
        html = f'''
            <select name="time" class="select select-bordered w-full animate-pulse" required>
                {options}
            </select>
            <div class="text-xs text-success mt-1">✓ {len(available_slots)} slots available</div>
        '''
        return HttpResponse(html)
        
    except ProviderProfile.DoesNotExist:
        return HttpResponse('''
            <select name="time" class="select select-bordered w-full" disabled>
                <option value="">Provider not found</option>
            </select>
        ''')
    except Exception as e:
        return HttpResponse(f'''
            <select name="time" class="select select-bordered w-full" disabled>
                <option value="">Error loading slots</option>
            </select>
            <div class="text-xs text-error mt-1">{str(e)}</div>
        ''')


@require_POST
def htmx_create_booking(request, provider_id):
    """HTMX endpoint to create a booking"""
    if not request.user.is_authenticated:
        return HttpResponse('''
            <div class="alert alert-warning">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <span>Please <a href="/login/" class="link">login</a> to book a consultation</span>
            </div>
        ''')
    
    try:
        service_id = request.POST.get('service', '')
        date_str = request.POST.get('date', '')
        time_str = request.POST.get('time', '')
        notes = request.POST.get('notes', '')
        consultation_type = request.POST.get('consultation_type', 'video')
        
        # If date is not provided, use tomorrow's date
        if not date_str:
            from datetime import date as dt_date
            tomorrow = dt_date.today() + timedelta(days=1)
            date_str = tomorrow.strftime('%Y-%m-%d')
        
        # If time is not provided, use default time
        if not time_str:
            time_str = '10:00'
        
        # Get provider - try by provider profile ID first, then by user ID
        try:
            provider = ProviderProfile.objects.get(id=provider_id)
        except ProviderProfile.DoesNotExist:
            provider = ProviderProfile.objects.get(user__id=provider_id)
        
        # Parse date and time
        scheduled_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Check if slot is still available
        existing_booking = Booking.objects.filter(
            provider=provider,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            status__in=['pending', 'payment_pending', 'confirmed', 'accepted']
        ).exists()
        
        if existing_booking:
            return HttpResponse('''
                <div class="alert alert-error">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span>This slot has been booked. Please select another time.</span>
                </div>
            ''')
        
        # Get service if provided
        service = None
        if service_id:
            try:
                service = ServiceListing.objects.get(id=service_id)
            except ServiceListing.DoesNotExist:
                pass
        
        # Calculate amount
        amount = service.price if service else provider.hourly_rate or Decimal('1500.00')
        
        # Create booking with payment pending status
        booking = Booking.objects.create(
            user=request.user,
            provider=provider,
            service=service,
            consultation_type=consultation_type,
            description=notes,
            status='payment_pending',
            amount=amount,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration_minutes=30,
        )
        
        # Return payment form
        html = f'''
            <div class="alert alert-info mb-4">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <div>
                    <h3 class="font-bold">Booking Created! 🎉</h3>
                    <p class="text-sm">Please complete payment to confirm your booking</p>
                </div>
            </div>
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h2 class="card-title">Payment Details</h2>
                    <div class="divider"></div>
                    <div class="flex justify-between">
                        <span>Consultation Fee</span>
                        <span class="font-bold">₹{amount}</span>
                    </div>
                    <div class="flex justify-between text-sm text-base-content/70">
                        <span>Date</span>
                        <span>{scheduled_date.strftime('%B %d, %Y')}</span>
                    </div>
                    <div class="flex justify-between text-sm text-base-content/70">
                        <span>Time</span>
                        <span>{scheduled_time.strftime('%I:%M %p')}</span>
                    </div>
                    <div class="divider"></div>
                    <button 
                        id="pay-btn"
                        class="btn btn-primary btn-block"
                        onclick="initiatePayment('{booking.id}', {int(amount * 100)})"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                        </svg>
                        Pay ₹{amount}
                    </button>
                </div>
            </div>
        '''
        return HttpResponse(html)
        
    except ProviderProfile.DoesNotExist:
        return HttpResponse('''
            <div class="alert alert-error">
                <span>Provider not found</span>
            </div>
        ''')
    except Exception as e:
        return HttpResponse(f'''
            <div class="alert alert-error">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>Booking failed: {str(e)}</span>
            </div>
        ''')


@require_GET
def htmx_booking_status(request, booking_id):
    """HTMX endpoint for real-time booking status polling"""
    try:
        booking = Booking.objects.get(id=booking_id)
        status = booking.status
    except Booking.DoesNotExist:
        return HttpResponse('<span class="badge badge-error">Not Found</span>')
    
    status_badges = {
        'completed': '<span class="badge badge-success badge-lg gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Completed</span>',
        'pending': '<span class="badge badge-warning badge-lg gap-2 animate-pulse"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Pending</span>',
        'payment_pending': '<span class="badge badge-secondary badge-lg gap-2 animate-pulse"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>Payment Pending</span>',
        'confirmed': '<span class="badge badge-success badge-lg gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Confirmed</span>',
        'accepted': '<span class="badge badge-info badge-lg gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Accepted</span>',
        'in-progress': '<span class="badge badge-primary badge-lg gap-2 animate-pulse"><svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>In Progress</span>',
        'cancelled': '<span class="badge badge-error badge-lg gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>Cancelled</span>',
    }
    
    return HttpResponse(status_badges.get(status, f'<span class="badge badge-neutral badge-lg">{status}</span>'))


@require_POST
def htmx_cancel_booking(request, booking_id):
    """HTMX endpoint to cancel a booking"""
    # In production, update database
    # booking = get_object_or_404(Booking, id=booking_id)
    # booking.status = 'cancelled'
    # booking.save()
    
    html = '''
    <div class="card bg-base-100 shadow-2xl">
        <div class="card-body text-center">
            <div class="text-6xl mb-4">❌</div>
            <h2 class="card-title justify-center text-2xl">Booking Cancelled</h2>
            <p class="opacity-60 mb-6">Your booking has been cancelled and any payment will be refunded within 3-5 business days.</p>
            <div class="card-actions justify-center">
                <a href="/citizen/dashboard/" class="btn btn-primary">
                    Back to Dashboard
                </a>
            </div>
        </div>
    </div>
    '''
    return HttpResponse(html)


def triage(request):
    """Triage questionnaire page"""
    context = {
        'questions': TRIAGE_QUESTIONS,
        'questions_json': json.dumps(TRIAGE_QUESTIONS),
    }
    return render(request, 'core/triage.html', context)


def triage_results(request):
    """Triage results page"""
    # Get answers from session or query params
    category = request.GET.get('category', 'other')
    
    # Filter providers by category from database
    providers_qs = get_providers_queryset().filter(
        specializations__contains=[category]
    ).order_by('-rating')[:5]
    
    matching_providers = [provider_to_dict(p) for p in providers_qs]
    
    context = {
        'category': category,
        'providers': matching_providers,
    }
    return render(request, 'core/triage_results.html', context)


@login_required
def citizen_dashboard(request):
    """Citizen dashboard view"""
    # Get user's recent analyses
    recent_analyses = AnalysisResult.objects.filter(user=request.user)[:5]
    
    # Get all user's bookings for counting
    all_bookings = Booking.objects.filter(user=request.user)
    
    # Get user's recent bookings for display
    bookings = all_bookings.select_related(
        'provider', 'provider__user'
    ).order_by('-created_at')[:10]
    
    # Get favorite providers
    favorites = FavoriteProvider.objects.filter(user=request.user).select_related(
        'provider', 'provider__user'
    )[:5]
    
    context = {
        'recent_analyses': recent_analyses,
        'bookings': bookings,
        'favorites': favorites,
        'pending_bookings': all_bookings.filter(status__in=['pending', 'payment_pending', 'confirmed']).count(),
        'completed_bookings': all_bookings.filter(status='completed').count(),
    }
    return render(request, 'core/citizen_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied')
        return redirect('home')
    
    context = {
        'total_users': User.objects.count(),
        'total_providers': ProviderProfile.objects.count(),
        'total_analyses': AnalysisResult.objects.count(),
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'total_revenue': Payment.objects.filter(status='captured').aggregate(
            total=Sum('amount')
        )['total'] or 0,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def booking_create(request, provider_id):
    """Create a booking"""
    try:
        # Try to get by provider profile ID first
        try:
            provider_profile = ProviderProfile.objects.select_related('user').get(id=provider_id)
        except ProviderProfile.DoesNotExist:
            # Fallback to user ID lookup
            provider_profile = ProviderProfile.objects.select_related('user').get(user__id=provider_id)
        
        provider = provider_to_dict(provider_profile)
        
        # Get services for this provider
        services = ServiceListing.objects.filter(provider=provider_profile, is_active=True)
        
        # Get availability for next 7 days
        today = timezone.now().date()
        availability = ProviderAvailability.objects.filter(
            provider=provider_profile,
            is_available=True
        ).order_by('day_of_week', 'start_time')
        
        # Get already booked slots
        booked_slots = Booking.objects.filter(
            provider=provider_profile,
            scheduled_date__gte=today,
            scheduled_date__lte=today + timedelta(days=7),
            status__in=['pending', 'payment_pending', 'confirmed', 'accepted']
        ).values_list('scheduled_date', 'scheduled_time')
        
        context = {
            'provider': provider,
            'provider_profile': provider_profile,
            'services': services,
            'availability': availability,
            'booked_slots': list(booked_slots),
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'min_booking_amount': settings.MIN_BOOKING_AMOUNT,
        }
        return render(request, 'core/booking_create.html', context)
        
    except ProviderProfile.DoesNotExist:
        messages.error(request, 'Provider not found')
        return redirect('providers')


@login_required
def booking_detail(request, booking_id):
    """Booking detail view"""
    booking = get_object_or_404(
        Booking.objects.select_related('provider', 'provider__user', 'user'),
        id=booking_id
    )
    
    # Check if user has permission to view this booking
    if booking.user != request.user and booking.provider.user != request.user:
        messages.error(request, 'Access denied')
        return redirect('home')
    
    # Get consultation notes if provider is viewing
    consultation_notes = []
    if booking.provider.user == request.user:
        consultation_notes = ConsultationNote.objects.filter(booking=booking)
    
    context = {
        'booking': booking,
        'consultation_notes': consultation_notes,
        'is_provider': booking.provider.user == request.user,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'core/booking_detail.html', context)


# ============================================
# REAL-TIME FEATURES VIEWS
# ============================================

@login_required
def chat_room(request, room_id):
    """Real-time chat room between client and lawyer"""
    from .models import ChatRoom, RealTimeMessage
    
    try:
        # First try to find by room_id
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            # If not found, treat room_id as booking_id and create/get chat room
            booking = get_object_or_404(Booking, id=room_id)
            room, created = ChatRoom.objects.get_or_create(
                client=booking.user,
                provider=booking.provider,
                defaults={
                    'booking': booking,
                }
            )
        
        # Check if user is participant
        if request.user != room.client and request.user != room.provider.user:
            messages.error(request, 'Access denied to this chat room')
            return redirect('home')
    except Exception as e:
        messages.error(request, f'Chat room error: {str(e)}')
        return redirect('home')
    
    # Get previous messages
    previous_messages = RealTimeMessage.objects.filter(room=room).order_by('created_at')[:100]
    
    context = {
        'room': room,
        'room_id': str(room.id),
        'messages': previous_messages,
        'other_user': room.provider.user if request.user == room.client else room.client,
    }
    return render(request, 'core/chat_room.html', context)


@login_required
def get_chat_rooms(request):
    """Get all chat rooms for current user"""
    from .models import ChatRoom
    
    if hasattr(request.user, 'provider_profile'):
        rooms = ChatRoom.objects.filter(provider=request.user.provider_profile)
    else:
        rooms = ChatRoom.objects.filter(client=request.user)
    
    rooms_data = [
        {
            'id': str(room.id),
            'other_user': room.provider.user.get_full_name() if request.user == room.client else room.client.get_full_name(),
            'status': room.status,
            'updated_at': room.updated_at.isoformat(),
        }
        for room in rooms
    ]
    
    return JsonResponse({'rooms': rooms_data})


@login_required
def video_room(request, room_code):
    """Video/Audio consultation room with WebRTC"""
    from .models import VideoSession
    import uuid
    
    try:
        # First try to find by room_code
        try:
            session = VideoSession.objects.select_related('booking__user', 'booking__provider__user').get(room_code=room_code)
        except VideoSession.DoesNotExist:
            # If not found, treat room_code as booking_id and create/get session
            booking = get_object_or_404(Booking, id=room_code)
            session, created = VideoSession.objects.get_or_create(
                booking=booking,
                defaults={
                    'room_code': f"legal-{uuid.uuid4().hex[:8]}",
                    'scheduled_at': booking.scheduled_at if hasattr(booking, 'scheduled_at') else timezone.now(),
                }
            )
        
        booking = session.booking
        
        # Check if user is participant
        if request.user != booking.user and request.user != booking.provider.user:
            messages.error(request, 'Access denied to this video room')
            return redirect('home')
            
    except Exception as e:
        messages.error(request, f'Session error: {str(e)}')
        return redirect('home')
    
    from django.conf import settings
    
    # Determine if audio only based on consultation type
    is_audio_only = booking.consultation_type == 'audio' if hasattr(booking, 'consultation_type') else False
    
    context = {
        'session': session,
        'room_code': session.room_code,
        'booking': booking,
        'is_provider': request.user == booking.provider.user,
        'is_audio_only': is_audio_only,
        'stun_servers': getattr(settings, 'WEBRTC_STUN_SERVERS', ['stun:stun.l.google.com:19302']),
    }
    return render(request, 'core/video_room.html', context)


@login_required
@require_POST
def create_video_session(request, booking_id):
    """Create a video session for a booking"""
    from .models import VideoSession
    import uuid
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if provider
    if request.user != booking.provider.user:
        return JsonResponse({'error': 'Only provider can create video session'}, status=403)
    
    # Create or get session
    session, created = VideoSession.objects.get_or_create(
        booking=booking,
        defaults={
            'room_code': f"legal-{uuid.uuid4().hex[:8]}",
            'scheduled_at': booking.scheduled_at,
        }
    )
    
    return JsonResponse({
        'success': True,
        'room_code': session.room_code,
        'scheduled_at': session.scheduled_at.isoformat(),
    })


def emergency_page(request):
    """Panic Button page"""
    return render(request, 'core/emergency.html')


@login_required
@require_POST
def create_emergency(request):
    """Create legal emergency alert"""
    from .models import LegalEmergency, ProviderProfile
    
    data = json.loads(request.body)
    
    emergency = LegalEmergency.objects.create(
        user=request.user,
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        description=data.get('description', 'Legal Emergency'),
    )
    
    # Send notifications to nearby providers
    try:
        from .notification_service import send_emergency_notifications
        
        # Get nearby providers (basic city-based for now)
        nearby_providers = ProviderProfile.objects.filter(
            user__verification_status='verified',
            availability_status='available'
        ).select_related('user')[:10]
        
        location = data.get('location_name', 'Unknown location')
        
        for provider in nearby_providers:
            send_emergency_notifications(
                emergency,
                provider.user,
                location
            )
    except Exception as e:
        print(f"Emergency notification error: {e}")
    
    return JsonResponse({
        'success': True,
        'emergency_id': str(emergency.id),
    })


@login_required
@require_POST
def respond_to_emergency(request, emergency_id):
    """Lawyer responds to emergency"""
    from .models import LegalEmergency
    from django.conf import settings
    
    emergency = get_object_or_404(LegalEmergency, id=emergency_id, status='active')
    
    # Check if provider
    if not hasattr(request.user, 'provider_profile'):
        return JsonResponse({'error': 'Only providers can respond'}, status=403)
    
    emergency.responder = request.user
    emergency.status = 'responded'
    emergency.responded_at = timezone.now()
    emergency.save()
    
    # Award bonus points
    provider = request.user.provider_profile
    provider.incentive_points += settings.PANIC_BUTTON_BONUS_POINTS
    provider.save()
    
    return JsonResponse({
        'success': True,
        'bonus_points': settings.PANIC_BUTTON_BONUS_POINTS,
    })


def case_predictor(request):
    """AI Judge Simulator page"""
    from .models import CasePrediction
    
    predictions = []
    if request.user.is_authenticated:
        predictions = CasePrediction.objects.filter(user=request.user)[:5]
    
    context = {
        'predictions': predictions,
    }
    return render(request, 'core/case_predictor.html', context)


@login_required
@require_POST
def predict_case_api(request):
    """Submit case for AI prediction"""
    from .tasks import predict_case_outcome
    
    data = json.loads(request.body)
    case_type = data.get('case_type', '')
    case_facts = data.get('case_facts', '')
    
    if not case_type or not case_facts:
        return JsonResponse({'error': 'Case type and facts are required'}, status=400)
    
    # Run in background
    task = predict_case_outcome.delay(str(request.user.id), case_type, case_facts)
    
    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'message': 'Analysis started. You will be notified when complete.',
    })


@login_required
@require_POST
def release_escrow(request, booking_id):
    """Client confirms service and releases escrow"""
    from .models import EscrowTransaction
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    try:
        escrow = booking.escrow_transaction
        escrow.client_confirmed = True
        
        if escrow.service_completed:
            escrow.status = 'released'
            escrow.released_at = timezone.now()
        
        escrow.save()
        
        return JsonResponse({'success': True, 'status': escrow.status})
    except EscrowTransaction.DoesNotExist:
        return JsonResponse({'error': 'No escrow transaction found'}, status=404)


@login_required
@require_POST
def dispute_escrow(request, booking_id):
    """Client disputes escrow payment"""
    from .models import EscrowTransaction
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    data = json.loads(request.body)
    
    try:
        escrow = booking.escrow_transaction
        escrow.status = 'disputed'
        escrow.dispute_reason = data.get('reason', '')
        escrow.dispute_opened_at = timezone.now()
        escrow.save()
        
        return JsonResponse({'success': True})
    except EscrowTransaction.DoesNotExist:
        return JsonResponse({'error': 'No escrow transaction found'}, status=404)


def crowdfunding_list(request):
    """List all active crowdfunding campaigns"""
    from .models import CrowdfundingCampaign
    
    campaigns = CrowdfundingCampaign.objects.filter(
        status__in=['active', 'funded']
    ).order_by('-created_at')
    
    context = {
        'campaigns': campaigns,
    }
    return render(request, 'core/crowdfunding_list.html', context)


@login_required
def crowdfunding_create(request):
    """Create new crowdfunding campaign"""
    from .models import CrowdfundingCampaign
    
    if request.method == 'POST':
        campaign = CrowdfundingCampaign.objects.create(
            user=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            case_type=request.POST.get('case_type'),
            target_amount=request.POST.get('target_amount'),
        )
        
        if 'income_proof' in request.FILES:
            campaign.income_proof = request.FILES['income_proof']
            campaign.save()
        
        messages.success(request, 'Campaign created! It will be reviewed shortly.')
        return redirect('crowdfunding_detail', campaign_id=str(campaign.id))
    
    return render(request, 'core/crowdfunding_create.html')


def crowdfunding_detail(request, campaign_id):
    """Crowdfunding campaign detail"""
    from .models import CrowdfundingCampaign
    
    campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id)
    donations = campaign.donations.all()[:20]
    
    context = {
        'campaign': campaign,
        'donations': donations,
    }
    return render(request, 'core/crowdfunding_detail.html', context)


@login_required
@require_POST
def donate_to_campaign(request, campaign_id):
    """Donate to a crowdfunding campaign"""
    from .models import CrowdfundingCampaign, CrowdfundingDonation
    from decimal import Decimal
    
    campaign = get_object_or_404(CrowdfundingCampaign, id=campaign_id, status='active')
    
    data = json.loads(request.body)
    amount = Decimal(data.get('amount', 0))
    
    if amount <= 0:
        return JsonResponse({'error': 'Invalid amount'}, status=400)
    
    donation = CrowdfundingDonation.objects.create(
        campaign=campaign,
        donor=request.user,
        amount=amount,
        is_anonymous=data.get('is_anonymous', False),
        message=data.get('message', ''),
    )
    
    # Update campaign raised amount
    campaign.raised_amount += amount
    if campaign.raised_amount >= campaign.target_amount:
        campaign.status = 'funded'
    campaign.save()
    
    return JsonResponse({
        'success': True,
        'new_total': str(campaign.raised_amount),
        'funding_progress': campaign.funding_progress,
    })


def voice_input(request):
    """Voice input page for vernacular languages"""
    transcriptions = []
    if request.user.is_authenticated:
        from .models import VoiceTranscription
        transcriptions = VoiceTranscription.objects.filter(user=request.user)[:10]
    
    return render(request, 'core/voice_input.html', {
        'transcriptions': transcriptions
    })


@login_required
@require_POST
def transcribe_voice(request):
    """Transcribe voice to text"""
    from .tasks import process_voice_transcription
    
    if 'audio' not in request.FILES:
        return JsonResponse({'error': 'No audio file provided'}, status=400)
    
    audio_file = request.FILES['audio']
    source_language = request.POST.get('language', 'hi')
    
    # Save audio file temporarily
    from django.core.files.storage import default_storage
    path = default_storage.save(f'temp_audio/{audio_file.name}', audio_file)
    
    # Process in background
    task = process_voice_transcription.delay(
        str(request.user.id),
        path,
        source_language
    )
    
    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'message': 'Transcription started',
    })


def ai_status(request):
    """Check AI provider status and available models"""
    from .gemini_service import get_ai_provider
    
    try:
        from .groq_service import is_groq_available, get_available_models, test_groq_connection
        groq_available = is_groq_available()
        groq_models = get_available_models() if groq_available else {}
        groq_test = test_groq_connection() if groq_available else {'success': False}
    except ImportError:
        groq_available = False
        groq_models = {}
        groq_test = {'success': False, 'error': 'Groq not installed'}
    
    from .gemini_service import get_gemini_model
    gemini_available = get_gemini_model() is not None
    
    provider = get_ai_provider()
    
    return JsonResponse({
        'active_provider': provider,
        'providers': {
            'groq': {
                'available': groq_available,
                'tested': groq_test.get('success', False),
                'models': groq_models,
                'speed': '300+ tokens/second',
                'cost': 'FREE (beta)',
            },
            'gemini': {
                'available': gemini_available,
                'models': {'default': 'gemini-1.5-flash'},
            }
        },
        'recommendation': 'Configure GROQ_API_KEY for faster, free AI' if not groq_available else 'Using Groq (optimal)',
    })


# ============================================
# PAYMENT VIEWS (Razorpay Integration)
# ============================================

@login_required
@require_POST
def create_payment_order(request):
    """Create a Razorpay order for a booking"""
    try:
        booking_id = request.POST.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        if booking.is_paid:
            return JsonResponse({
                'success': False,
                'error': 'Booking is already paid'
            })
        
        from .payment_service import get_payment_service
        payment_service = get_payment_service()
        
        if not payment_service:
            return JsonResponse({
                'success': False,
                'error': 'Payment service not configured'
            })
        
        # Create Razorpay order
        result = payment_service.create_order(
            amount=booking.amount,
            receipt=f'booking_{booking.id}',
            notes={
                'booking_id': str(booking.id),
                'user_id': str(request.user.id),
                'provider_id': str(booking.provider.user.id),
            }
        )
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to create order')
            })
        
        # Save order ID to booking
        booking.payment_order_id = result['order_id']
        booking.save()
        
        # Create payment record
        Payment.objects.create(
            user=request.user,
            booking=booking,
            razorpay_order_id=result['order_id'],
            amount=booking.amount,
            payment_type='booking',
            description=f'Booking with {booking.provider.user.get_full_name()}',
        )
        
        return JsonResponse({
            'success': True,
            'order_id': result['order_id'],
            'amount': result['amount_paise'],
            'currency': result['currency'],
            'key_id': settings.RAZORPAY_KEY_ID,
            'booking_id': str(booking.id),
            'user_name': request.user.get_full_name() or request.user.username,
            'user_email': request.user.email,
            'user_phone': request.user.phone_number or '',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def verify_payment(request):
    """Verify Razorpay payment and update booking"""
    try:
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        booking_id = request.POST.get('booking_id')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, booking_id]):
            return JsonResponse({
                'success': False,
                'error': 'Missing payment details'
            })
        
        from .payment_service import get_payment_service
        payment_service = get_payment_service()
        
        if not payment_service:
            return JsonResponse({
                'success': False,
                'error': 'Payment service not configured'
            })
        
        # Verify signature
        is_valid = payment_service.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Invalid payment signature'
            })
        
        # Update booking
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        booking.payment_id = razorpay_payment_id
        booking.payment_signature = razorpay_signature
        booking.is_paid = True
        booking.paid_at = timezone.now()
        booking.status = 'confirmed'
        booking.escrow_status = 'held'
        booking.save()
        
        # Update payment record
        Payment.objects.filter(
            razorpay_order_id=razorpay_order_id
        ).update(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            status='captured'
        )
        
        # Send notifications
        try:
            from .notification_service import send_booking_notifications, send_payment_notifications
            payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if payment:
                send_payment_notifications(payment, booking)
            send_booking_notifications(booking)
        except Exception as notification_error:
            # Don't fail the payment if notifications fail
            print(f"Notification error: {notification_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Payment verified successfully',
            'booking_id': str(booking.id),
            'redirect_url': f'/bookings/{booking.id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Handle Razorpay webhook callbacks"""
    import hmac
    import hashlib
    
    try:
        # Verify webhook signature
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        if webhook_secret:
            signature = request.headers.get('X-Razorpay-Signature', '')
            body = request.body.decode('utf-8')
            
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return JsonResponse({'status': 'invalid_signature'}, status=400)
        
        # Parse event
        payload = json.loads(request.body)
        event = payload.get('event', '')
        
        if event == 'payment.captured':
            payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            
            # Update booking
            booking = Booking.objects.filter(payment_order_id=order_id).first()
            if booking and not booking.is_paid:
                booking.payment_id = payment_id
                booking.is_paid = True
                booking.paid_at = timezone.now()
                booking.status = 'confirmed'
                booking.escrow_status = 'held'
                booking.save()
                
                Payment.objects.filter(
                    razorpay_order_id=order_id
                ).update(
                    razorpay_payment_id=payment_id,
                    status='captured'
                )
        
        elif event == 'payment.failed':
            payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            
            Payment.objects.filter(
                razorpay_order_id=order_id
            ).update(status='failed')
        
        elif event == 'refund.created':
            refund_entity = payload.get('payload', {}).get('refund', {}).get('entity', {})
            payment_id = refund_entity.get('payment_id')
            
            Payment.objects.filter(
                razorpay_payment_id=payment_id
            ).update(status='refunded')
            
            # Update booking
            Booking.objects.filter(payment_id=payment_id).update(
                escrow_status='refunded',
                status='cancelled'
            )
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================
# LAWYER/PROVIDER MANAGEMENT VIEWS
# ============================================

@login_required
def provider_bookings(request):
    """View all bookings for a provider"""
    try:
        provider = request.user.provider_profile
    except ProviderProfile.DoesNotExist:
        messages.error(request, 'Provider profile not found')
        return redirect('home')
    
    status_filter = request.GET.get('status', '')
    
    bookings = Booking.objects.filter(provider=provider).select_related(
        'user', 'service'
    ).order_by('-created_at')
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'pending_count': bookings.filter(status__in=['pending', 'confirmed']).count(),
        'completed_count': bookings.filter(status='completed').count(),
    }
    return render(request, 'core/provider_bookings.html', context)


@login_required
@require_POST
def accept_booking(request, booking_id):
    """Provider accepts a booking"""
    try:
        provider = request.user.provider_profile
        booking = get_object_or_404(Booking, id=booking_id, provider=provider)
        
        if booking.status not in ['pending', 'confirmed']:
            return JsonResponse({
                'success': False,
                'error': 'Booking cannot be accepted in current status'
            })
        
        booking.status = 'accepted'
        booking.save()
        
        # Award points to provider
        provider.incentive_points += 10
        provider.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking accepted successfully'
        })
        
    except ProviderProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Provider profile not found'
        })


@login_required
@require_POST
def complete_booking(request, booking_id):
    """Provider marks booking as completed"""
    try:
        provider = request.user.provider_profile
        booking = get_object_or_404(Booking, id=booking_id, provider=provider)
        
        if booking.status not in ['accepted', 'in-progress']:
            return JsonResponse({
                'success': False,
                'error': 'Booking cannot be completed in current status'
            })
        
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.save()
        
        # Award points to provider
        provider.incentive_points += 50
        provider.cases_won += 1
        provider.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking completed successfully'
        })
        
    except ProviderProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Provider profile not found'
        })


@login_required
def provider_earnings(request):
    """Provider earnings dashboard"""
    try:
        provider = request.user.provider_profile
    except ProviderProfile.DoesNotExist:
        messages.error(request, 'Provider profile not found')
        return redirect('home')
    
    # Get completed bookings with payments
    completed_bookings = Booking.objects.filter(
        provider=provider,
        status='completed',
        is_paid=True
    ).order_by('-completed_at')
    
    # Calculate earnings
    total_earnings = completed_bookings.aggregate(total=Sum('amount'))['total'] or 0
    platform_fee = total_earnings * Decimal(str(settings.PLATFORM_FEE_PERCENTAGE / 100))
    net_earnings = total_earnings - platform_fee
    
    # Monthly breakdown
    from django.db.models.functions import TruncMonth
    monthly_earnings = completed_bookings.annotate(
        month=TruncMonth('completed_at')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-month')[:12]
    
    context = {
        'completed_bookings': completed_bookings[:20],
        'total_earnings': total_earnings,
        'platform_fee': platform_fee,
        'net_earnings': net_earnings,
        'monthly_earnings': monthly_earnings,
        'total_cases': completed_bookings.count(),
    }
    return render(request, 'core/provider_earnings.html', context)


@login_required
def provider_availability_manage(request):
    """Manage provider availability"""
    try:
        provider = request.user.provider_profile
    except ProviderProfile.DoesNotExist:
        messages.error(request, 'Provider profile not found')
        return redirect('become_provider')
    
    if request.method == 'POST':
        # Clear existing availability
        ProviderAvailability.objects.filter(provider=provider).delete()
        
        # Add new slots
        days = request.POST.getlist('days[]')
        start_times = request.POST.getlist('start_times[]')
        end_times = request.POST.getlist('end_times[]')
        
        for day, start, end in zip(days, start_times, end_times):
            if day and start and end:
                ProviderAvailability.objects.create(
                    provider=provider,
                    day_of_week=int(day),
                    start_time=datetime.strptime(start, '%H:%M').time(),
                    end_time=datetime.strptime(end, '%H:%M').time(),
                )
        
        messages.success(request, 'Availability updated successfully')
        return redirect('provider_availability_manage')
    
    availability = ProviderAvailability.objects.filter(provider=provider).order_by('day_of_week', 'start_time')
    time_off = ProviderTimeOff.objects.filter(provider=provider, date__gte=timezone.now().date())
    
    context = {
        'availability': availability,
        'time_off': time_off,
        'days_of_week': ProviderAvailability.DAYS_OF_WEEK,
    }
    return render(request, 'core/provider_availability.html', context)


@login_required
@require_POST
def add_consultation_note(request, booking_id):
    """Add consultation notes"""
    try:
        provider = request.user.provider_profile
        booking = get_object_or_404(Booking, id=booking_id, provider=provider)
        
        notes = request.POST.get('notes', '')
        is_private = request.POST.get('is_private', 'true') == 'true'
        
        ConsultationNote.objects.create(
            booking=booking,
            provider=provider,
            notes=notes,
            is_private=is_private,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Note added successfully'
        })
        
    except ProviderProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Provider profile not found'
        })


# ============================================
# CLIENT FEATURES
# ============================================

@login_required
@require_POST
def toggle_favorite_provider(request, provider_id):
    """Toggle favorite status for a provider"""
    try:
        provider = ProviderProfile.objects.get(user__id=provider_id)
        
        favorite, created = FavoriteProvider.objects.get_or_create(
            user=request.user,
            provider=provider
        )
        
        if not created:
            favorite.delete()
            return JsonResponse({
                'success': True,
                'is_favorite': False,
                'message': 'Removed from favorites'
            })
        
        return JsonResponse({
            'success': True,
            'is_favorite': True,
            'message': 'Added to favorites'
        })
        
    except ProviderProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Provider not found'
        })


@login_required
def my_bookings(request):
    """View user's bookings"""
    status_filter = request.GET.get('status', '')
    
    bookings = Booking.objects.filter(user=request.user).select_related(
        'provider', 'provider__user', 'service'
    ).order_by('-created_at')
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'upcoming_count': bookings.filter(status__in=['confirmed', 'accepted']).count(),
        'completed_count': bookings.filter(status='completed').count(),
    }
    return render(request, 'core/my_bookings.html', context)


@login_required
def my_favorites(request):
    """View user's favorite providers"""
    favorites = FavoriteProvider.objects.filter(
        user=request.user
    ).select_related('provider', 'provider__user')
    
    providers = [provider_to_dict(f.provider) for f in favorites]
    
    context = {
        'providers': providers,
    }
    return render(request, 'core/my_favorites.html', context)


@login_required
@require_POST  
def submit_review(request, booking_id):
    """Submit a review for completed booking"""
    booking = get_object_or_404(
        Booking, 
        id=booking_id, 
        user=request.user, 
        status='completed'
    )
    
    # Check if review already exists
    if Review.objects.filter(booking=booking).exists():
        return JsonResponse({
            'success': False,
            'error': 'You have already reviewed this consultation'
        })
    
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '')
    
    if rating < 1 or rating > 5:
        return JsonResponse({
            'success': False,
            'error': 'Invalid rating'
        })
    
    Review.objects.create(
        user=request.user,
        provider=booking.provider,
        booking=booking,
        rating=rating,
        comment=comment,
    )
    
    # Update provider rating
    avg_rating = Review.objects.filter(
        provider=booking.provider
    ).aggregate(avg=Avg('rating'))['avg']
    
    booking.provider.rating = avg_rating
    booking.provider.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Review submitted successfully'
    })


@login_required
@require_POST
def request_refund(request, booking_id):
    """Request refund for a booking"""
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )
    
    if booking.status == 'completed':
        return JsonResponse({
            'success': False,
            'error': 'Cannot refund completed bookings'
        })
    
    if not booking.is_paid:
        return JsonResponse({
            'success': False,
            'error': 'No payment to refund'
        })
    
    # Process refund through Razorpay
    from .payment_service import get_payment_service
    payment_service = get_payment_service()
    
    if payment_service and booking.payment_id:
        result = payment_service.refund_payment(
            booking.payment_id,
            notes={'reason': 'User requested refund', 'booking_id': str(booking.id)}
        )
        
        if result['success']:
            booking.escrow_status = 'refunded'
            booking.status = 'cancelled'
            booking.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Refund processed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Refund failed')
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Unable to process refund'
    })
