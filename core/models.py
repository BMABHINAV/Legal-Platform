from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    
    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('provider', 'Provider'),
        ('admin', 'Admin'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class ProviderProfile(models.Model):
    """Provider profile for legal service providers"""
    
    PROVIDER_TYPE_CHOICES = [
        ('advocate', 'Advocate'),
        ('mediator', 'Mediator'),
        ('arbitrator', 'Arbitrator'),
        ('notary', 'Notary'),
        ('document_writer', 'Document Writer'),
        ('legal-aid', 'Legal Aid'),
    ]
    
    AVAILABILITY_STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    provider_type = models.CharField(max_length=30, choices=PROVIDER_TYPE_CHOICES)
    bar_registration_number = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0)
    specializations = models.JSONField(default=list)  # Store as list
    languages = models.JSONField(default=list)  # Store as list
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.IntegerField(default=0)
    completed_cases = models.IntegerField(default=0)
    response_time = models.CharField(max_length=50, blank=True, null=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS_CHOICES, default='available')
    hourly_rate = models.IntegerField(blank=True, null=True)
    incentive_points = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'provider_profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_provider_type_display()}"

    @property
    def location(self):
        return {'city': self.city, 'state': self.state}

    def get_tier(self):
        """Get the reward tier based on incentive points"""
        from .incentive_rules import get_provider_tier
        return get_provider_tier(self.incentive_points)


class Badge(models.Model):
    """Badges earned by providers"""
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='badges')
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10)  # Emoji icon
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'badges'

    def __str__(self):
        return f"{self.name} - {self.provider.user.get_full_name()}"


class ServiceListing(models.Model):
    """Services offered by providers"""
    
    CATEGORY_CHOICES = [
        ('family', 'Family'),
        ('property', 'Property'),
        ('criminal', 'Criminal'),
        ('civil', 'Civil'),
        ('corporate', 'Corporate'),
        ('labor', 'Labor'),
        ('tax', 'Tax'),
        ('consumer', 'Consumer'),
        ('other', 'Other'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    price_min = models.IntegerField()
    price_max = models.IntegerField()
    duration = models.CharField(max_length=100, blank=True, null=True)
    delivery_time = models.CharField(max_length=100, blank=True, null=True)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_listings'

    def __str__(self):
        return self.title

    @property
    def price_range(self):
        return {'min': self.price_min, 'max': self.price_max}


class AnalysisResult(models.Model):
    """Document analysis results"""
    
    RISK_LEVEL_CHOICES = [
        ('safe', 'Safe'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analyses')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    document_type = models.CharField(max_length=100)
    health_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)
    summary = models.JSONField(default=dict)
    risks = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    suggested_lawyer_categories = models.JSONField(default=list)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analysis_results'
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"Analysis: {self.file_name} ({self.risk_level})"


class ChatSession(models.Model):
    """AI Chat sessions"""
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions')
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    """Messages in a chat session"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class Booking(models.Model):
    """Bookings between users and providers"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('payment_pending', 'Payment Pending'),
        ('confirmed', 'Confirmed'),
        ('accepted', 'Accepted'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ESCROW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('held', 'Held'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
    ]
    
    CONSULTATION_TYPE_CHOICES = [
        ('video', 'Video Consultation'),
        ('audio', 'Audio Consultation'),
        ('chat', 'Chat Consultation'),
        ('in_person', 'In-Person Meeting'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(ServiceListing, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    # Consultation details
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES, default='video')
    description = models.TextField(blank=True, help_text="Brief description of the legal issue")
    notes = models.TextField(blank=True)
    
    # Status and payment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    escrow_status = models.CharField(max_length=20, choices=ESCROW_STATUS_CHOICES, default='pending')
    
    # Payment tracking
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_signature = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=30)
    
    # Timestamps
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id[:8]} - {self.user.username} → {self.provider.user.username}"
    
    @property
    def scheduled_datetime(self):
        if self.scheduled_date and self.scheduled_time:
            from datetime import datetime
            return datetime.combine(self.scheduled_date, self.scheduled_time)
        return self.scheduled_at


class Payment(models.Model):
    """Payment transactions"""
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('booking', 'Booking Payment'),
        ('donation', 'Crowdfunding Donation'),
        ('tip', 'Tip'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='booking')
    
    # Additional info
    description = models.TextField(blank=True)
    receipt = models.CharField(max_length=100, blank=True)
    notes = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.razorpay_order_id} - ₹{self.amount} ({self.status})"


class Review(models.Model):
    """Reviews for providers"""
    id = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review: {self.rating}/5 by {self.user.username}"


# ============================================
# REAL-TIME FEATURES MODELS
# ============================================

class ChatRoom(models.Model):
    """Real-time chat room between client and lawyer"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='chat_room', null=True, blank=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_client')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='chat_rooms')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_rooms'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat: {self.client.username} <-> {self.provider.user.username}"


class RealTimeMessage(models.Model):
    """Messages in real-time chat rooms"""
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    is_encrypted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'realtime_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender}: {self.content[:50]}"


class VideoSession(models.Model):
    """Video consultation sessions"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('waiting', 'Waiting'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='video_session')
    room_code = models.CharField(max_length=100, unique=True)
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    whiteboard_data = models.JSONField(default=dict, blank=True)
    recording_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'video_sessions'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Video: {self.room_code} - {self.status}"


class Notification(models.Model):
    """Push notifications for users"""
    
    TYPE_CHOICES = [
        ('booking_request', 'Booking Request'),
        ('booking_accepted', 'Booking Accepted'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('document_ready', 'Document Ready'),
        ('payment_received', 'Payment Received'),
        ('payment_released', 'Payment Released'),
        ('message', 'New Message'),
        ('emergency', 'Emergency Alert'),
        ('case_update', 'Case Update'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.title} -> {self.user.username}"


class LegalEmergency(models.Model):
    """Panic Button - Legal Emergency requests"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('responded', 'Responded'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergencies')
    responder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='emergency_responses')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'legal_emergencies'
        ordering = ['-created_at']

    def __str__(self):
        return f"Emergency: {self.user.username} - {self.status}"


class CasePrediction(models.Model):
    """AI Judge Simulator - Case predictions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_predictions')
    case_type = models.CharField(max_length=100)
    case_facts = models.TextField()
    win_probability = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    supporting_cases = models.JSONField(default=list)
    opposing_cases = models.JSONField(default=list)
    analysis = models.TextField()
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'case_predictions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction: {self.case_type} - {self.win_probability}%"


class EscrowTransaction(models.Model):
    """Smart Contract Escrow - Payment tracking"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('held', 'Held in Escrow'),
        ('released', 'Released to Provider'),
        ('refunded', 'Refunded to Client'),
        ('disputed', 'Under Dispute'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='escrow_transaction')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Milestone-based release
    service_completed = models.BooleanField(default=False)
    client_confirmed = models.BooleanField(default=False)
    dispute_reason = models.TextField(blank=True)
    
    # Timestamps
    held_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    dispute_opened_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'escrow_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Escrow: ₹{self.amount} - {self.status}"


class CrowdfundingCampaign(models.Model):
    """Crowd-Justice - Pro Bono Funding"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('active', 'Active'),
        ('funded', 'Fully Funded'),
        ('in-progress', 'Case In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    assigned_lawyer = models.ForeignKey(ProviderProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='pro_bono_cases')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    case_type = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    raised_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    income_proof = models.FileField(upload_to='crowdfunding/proofs/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crowdfunding_campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"Campaign: {self.title} - ₹{self.raised_amount}/{self.target_amount}"
    
    @property
    def funding_progress(self):
        if self.target_amount > 0:
            return int((self.raised_amount / self.target_amount) * 100)
        return 0


class CrowdfundingDonation(models.Model):
    """Donations to crowdfunding campaigns"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(CrowdfundingCampaign, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_anonymous = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crowdfunding_donations'
        ordering = ['-created_at']

    def __str__(self):
        donor_name = "Anonymous" if self.is_anonymous else (self.donor.username if self.donor else "Unknown")
        return f"Donation: ₹{self.amount} by {donor_name}"


class VoiceTranscription(models.Model):
    """Vernacular Voice-to-Legal-Text"""
    
    LANGUAGE_CHOICES = [
        ('hi', 'Hindi'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('mr', 'Marathi'),
        ('bn', 'Bengali'),
        ('gu', 'Gujarati'),
        ('pa', 'Punjabi'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transcriptions')
    source_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    original_audio = models.FileField(upload_to='transcriptions/audio/', blank=True, null=True)
    original_text = models.TextField()
    translated_text = models.TextField()  # English
    legal_interpretation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voice_transcriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transcription: {self.source_language} -> EN"


# ============================================
# PROVIDER AVAILABILITY & SCHEDULING
# ============================================

class ProviderAvailability(models.Model):
    """Provider weekly availability schedule"""
    
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'provider_availability'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['provider', 'day_of_week', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.provider.user.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class ProviderTimeOff(models.Model):
    """Provider specific dates off (vacation, holidays, etc.)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='time_off')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'provider_time_off'
        ordering = ['date']
        unique_together = ['provider', 'date']

    def __str__(self):
        return f"{self.provider.user.username} - Off on {self.date}"


class FavoriteProvider(models.Model):
    """User's favorite/saved lawyers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_providers')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorite_providers'
        unique_together = ['user', 'provider']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.provider.user.username}"


class ConsultationNote(models.Model):
    """Notes from lawyer about consultations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='consultation_notes')
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='consultation_notes')
    notes = models.TextField()
    is_private = models.BooleanField(default=True, help_text="If true, only visible to lawyer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for Booking #{self.booking.id[:8]} by {self.provider.user.username}"
