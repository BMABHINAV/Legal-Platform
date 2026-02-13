from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import (
    User, ProviderProfile, Badge, ServiceListing, AnalysisResult, 
    ChatSession, ChatMessage, Booking, Review,
    ChatRoom, RealTimeMessage, VideoSession, Notification, LegalEmergency,
    CasePrediction, EscrowTransaction, CrowdfundingCampaign, CrowdfundingDonation,
    VoiceTranscription
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'verification_status_badge', 'created_at')
    list_filter = ('role', 'verification_status')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['verify_users', 'reject_users', 'mark_pending']
    
    def verification_status_badge(self, obj):
        colors = {
            'verified': '#10b981',
            'pending': '#f59e0b',
            'unverified': '#6b7280',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.verification_status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            obj.verification_status.upper()
        )
    verification_status_badge.short_description = 'Status'
    
    @admin.action(description='✅ Verify selected users')
    def verify_users(self, request, queryset):
        updated = queryset.update(verification_status='verified')
        self.message_user(request, f'{updated} user(s) verified successfully.', messages.SUCCESS)
        
        # Send notification emails
        for user in queryset:
            try:
                from .notification_service import EmailNotificationService
                email_service = EmailNotificationService()
                email_service.send_provider_verification(user)
            except Exception as e:
                pass
    
    @admin.action(description='❌ Reject selected users')
    def reject_users(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} user(s) rejected.', messages.WARNING)
    
    @admin.action(description='⏳ Mark as pending review')
    def mark_pending(self, request, queryset):
        updated = queryset.update(verification_status='pending')
        self.message_user(request, f'{updated} user(s) marked as pending.', messages.INFO)


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider_type', 'city', 'state', 'user_verification', 'rating', 'incentive_points')
    list_filter = ('provider_type', 'availability_status', 'state', 'user__verification_status')
    search_fields = ('user__username', 'user__email', 'city')
    actions = ['verify_providers', 'reject_providers']
    
    def user_verification(self, obj):
        status = obj.user.verification_status
        colors = {
            'verified': '#10b981',
            'pending': '#f59e0b',
            'unverified': '#6b7280',
            'rejected': '#ef4444',
        }
        color = colors.get(status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            status.upper()
        )
    user_verification.short_description = 'Verification'
    
    @admin.action(description='✅ Verify selected providers')
    def verify_providers(self, request, queryset):
        updated = 0
        for profile in queryset:
            profile.user.verification_status = 'verified'
            profile.user.save()
            updated += 1
            
            # Send notification email
            try:
                from .notification_service import EmailNotificationService
                email_service = EmailNotificationService()
                email_service.send_provider_verification(profile.user)
            except Exception as e:
                pass
        
        self.message_user(request, f'{updated} provider(s) verified successfully.', messages.SUCCESS)
    
    @admin.action(description='❌ Reject selected providers')
    def reject_providers(self, request, queryset):
        updated = 0
        for profile in queryset:
            profile.user.verification_status = 'rejected'
            profile.user.save()
            updated += 1
        
        self.message_user(request, f'{updated} provider(s) rejected.', messages.WARNING)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'earned_at')
    list_filter = ('name',)


@admin.register(ServiceListing)
class ServiceListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price_min', 'price_max')
    list_filter = ('category',)
    search_fields = ('title', 'description')


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'document_type', 'health_score', 'risk_level', 'analyzed_at')
    list_filter = ('document_type', 'risk_level')
    search_fields = ('file_name',)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at')
    list_filter = ('role',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'status', 'amount', 'scheduled_at')
    list_filter = ('status', 'escrow_status')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'rating', 'created_at')
    list_filter = ('rating',)


# Real-time Communication Models
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'provider', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(RealTimeMessage)
class RealTimeMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(VideoSession)
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_code', 'booking', 'status', 'scheduled_at')
    list_filter = ('status',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')


# Emergency & Safety Models
@admin.register(LegalEmergency)
class LegalEmergencyAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'responder', 'created_at')
    list_filter = ('status',)


# AI & Prediction Models
@admin.register(CasePrediction)
class CasePredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'case_type', 'win_probability', 'created_at')
    list_filter = ('case_type',)


# Financial Models
@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(CrowdfundingCampaign)
class CrowdfundingCampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'target_amount', 'raised_amount', 'status', 'is_verified')
    list_filter = ('status', 'is_verified', 'case_type')


@admin.register(CrowdfundingDonation)
class CrowdfundingDonationAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'donor', 'amount', 'is_anonymous', 'created_at')
    list_filter = ('is_anonymous',)


# Voice & Accessibility Models
@admin.register(VoiceTranscription)
class VoiceTranscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_language', 'created_at')
    list_filter = ('source_language',)
