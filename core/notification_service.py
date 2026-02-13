"""
Notification Services for Email and SMS.
Handles all platform notifications.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging
import requests
import os

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service for sending email notifications.
    Supports both plain text and HTML emails.
    """
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation to client"""
        try:
            subject = f'Booking Confirmed - {booking.provider.user.get_full_name()}'
            
            context = {
                'booking': booking,
                'client_name': booking.user.get_full_name() or booking.user.username,
                'provider_name': booking.provider.user.get_full_name(),
                'date': booking.scheduled_date,
                'time': booking.scheduled_time,
                'amount': booking.amount,
                'consultation_type': booking.get_consultation_type_display(),
            }
            
            html_content = render_to_string('emails/booking_confirmation.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Booking confirmation email sent to {booking.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email: {e}")
            return False
    
    @staticmethod
    def send_booking_notification_to_provider(booking):
        """Send new booking notification to provider"""
        try:
            subject = f'New Booking Request - {booking.user.get_full_name()}'
            
            context = {
                'booking': booking,
                'provider_name': booking.provider.user.get_full_name(),
                'client_name': booking.user.get_full_name() or booking.user.username,
                'date': booking.scheduled_date,
                'time': booking.scheduled_time,
                'amount': booking.amount,
            }
            
            html_content = render_to_string('emails/new_booking_provider.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.provider.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"New booking email sent to provider {booking.provider.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send booking notification to provider: {e}")
            return False
    
    @staticmethod
    def send_payment_receipt(payment):
        """Send payment receipt to client"""
        try:
            subject = f'Payment Receipt - ₹{payment.amount}'
            
            context = {
                'payment': payment,
                'booking': payment.booking,
                'client_name': payment.user.get_full_name() or payment.user.username,
            }
            
            html_content = render_to_string('emails/payment_receipt.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[payment.user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Payment receipt sent to {payment.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send payment receipt: {e}")
            return False
    
    @staticmethod
    def send_booking_reminder(booking):
        """Send booking reminder 1 hour before consultation"""
        try:
            subject = f'Reminder: Consultation in 1 hour with {booking.provider.user.get_full_name()}'
            
            context = {
                'booking': booking,
                'client_name': booking.user.get_full_name(),
                'provider_name': booking.provider.user.get_full_name(),
            }
            
            html_content = render_to_string('emails/booking_reminder.html', context)
            text_content = strip_tags(html_content)
            
            # Send to both client and provider
            recipients = [booking.user.email, booking.provider.user.email]
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Booking reminder sent for booking {booking.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send booking reminder: {e}")
            return False
    
    @staticmethod
    def send_emergency_alert(emergency, nearby_providers):
        """Send emergency alert to nearby providers"""
        try:
            subject = '🆘 URGENT: Legal Emergency Nearby!'
            
            for provider in nearby_providers:
                context = {
                    'emergency': emergency,
                    'provider_name': provider.user.get_full_name(),
                    'client_name': emergency.user.get_full_name() if emergency.user else 'Anonymous',
                    'location': emergency.location_address,
                }
                
                html_content = render_to_string('emails/emergency_alert.html', context)
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[provider.user.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            
            logger.info(f"Emergency alerts sent to {len(nearby_providers)} providers")
            return True
        except Exception as e:
            logger.error(f"Failed to send emergency alerts: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        try:
            subject = 'Welcome to Legal Platform!'
            
            context = {
                'user': user,
                'name': user.get_full_name() or user.username,
            }
            
            html_content = render_to_string('emails/welcome.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    @staticmethod
    def send_provider_verification(user):
        """Send notification when provider is verified"""
        try:
            subject = '✅ Your Provider Account is Verified!'
            
            context = {
                'user': user,
                'name': user.get_full_name() or user.username,
            }
            
            html_content = render_to_string('emails/provider_verified.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Verification email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False


class SMSNotificationService:
    """
    Service for sending SMS notifications.
    Uses configurable SMS gateway (default: Fast2SMS for India).
    """
    
    SMS_API_KEY = os.getenv('SMS_API_KEY', '')
    SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'LGLPLT')
    SMS_GATEWAY_URL = os.getenv('SMS_GATEWAY_URL', 'https://www.fast2sms.com/dev/bulkV2')
    
    @classmethod
    def send_sms(cls, phone_number, message):
        """Send SMS using configured gateway"""
        if not cls.SMS_API_KEY:
            logger.warning("SMS API key not configured. SMS not sent.")
            # For development, just log the message
            logger.info(f"[DEV SMS] To: {phone_number}, Message: {message}")
            return True
        
        try:
            # Clean phone number
            phone = phone_number.replace(' ', '').replace('+91', '').replace('-', '')
            
            payload = {
                'authorization': cls.SMS_API_KEY,
                'sender_id': cls.SMS_SENDER_ID,
                'message': message,
                'language': 'english',
                'route': 'q',  # Quick SMS
                'numbers': phone,
            }
            
            response = requests.post(cls.SMS_GATEWAY_URL, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('return'):
                    logger.info(f"SMS sent to {phone_number}")
                    return True
                else:
                    logger.error(f"SMS failed: {result.get('message')}")
                    return False
            else:
                logger.error(f"SMS API error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    @classmethod
    def send_booking_confirmation_sms(cls, booking):
        """Send booking confirmation SMS to client"""
        message = (
            f"Legal Platform: Your booking with {booking.provider.user.get_full_name()} "
            f"is confirmed for {booking.scheduled_date.strftime('%d %b')} at "
            f"{booking.scheduled_time.strftime('%I:%M %p')}. "
            f"Amount: Rs.{booking.amount}"
        )
        return cls.send_sms(booking.user.phone, message)
    
    @classmethod
    def send_booking_reminder_sms(cls, booking):
        """Send booking reminder SMS"""
        message = (
            f"Legal Platform: Reminder - Your consultation with "
            f"{booking.provider.user.get_full_name()} is in 1 hour. "
            f"Please be ready."
        )
        return cls.send_sms(booking.user.phone, message)
    
    @classmethod
    def send_new_booking_sms_to_provider(cls, booking):
        """Send new booking SMS to provider"""
        message = (
            f"Legal Platform: New booking from {booking.user.get_full_name()} "
            f"for {booking.scheduled_date.strftime('%d %b')} at "
            f"{booking.scheduled_time.strftime('%I:%M %p')}. "
            f"Please review and accept."
        )
        return cls.send_sms(booking.provider.user.phone, message)
    
    @classmethod
    def send_emergency_alert_sms(cls, emergency, provider):
        """Send emergency alert SMS to provider"""
        location = emergency.location_address or 'Unknown location'
        message = (
            f"🆘 URGENT: Legal emergency nearby! "
            f"Location: {location[:50]}. "
            f"Open app to respond immediately."
        )
        return cls.send_sms(provider.user.phone, message)
    
    @classmethod
    def send_otp_sms(cls, phone_number, otp):
        """Send OTP SMS for verification"""
        message = f"Legal Platform: Your OTP is {otp}. Valid for 10 minutes. Do not share with anyone."
        return cls.send_sms(phone_number, message)
    
    @classmethod
    def send_payment_confirmation_sms(cls, payment):
        """Send payment confirmation SMS"""
        message = (
            f"Legal Platform: Payment of Rs.{payment.amount} received. "
            f"Transaction ID: {payment.razorpay_payment_id[:12]}. "
            f"Thank you!"
        )
        return cls.send_sms(payment.user.phone, message)


# Convenience functions
def send_booking_notifications(booking):
    """Send all booking notifications (email + SMS)"""
    # Email notifications
    EmailNotificationService.send_booking_confirmation(booking)
    EmailNotificationService.send_booking_notification_to_provider(booking)
    
    # SMS notifications
    if booking.user.phone:
        SMSNotificationService.send_booking_confirmation_sms(booking)
    if booking.provider.user.phone:
        SMSNotificationService.send_new_booking_sms_to_provider(booking)


def send_payment_notifications(payment):
    """Send payment notifications"""
    EmailNotificationService.send_payment_receipt(payment)
    if payment.user.phone:
        SMSNotificationService.send_payment_confirmation_sms(payment)


def send_emergency_notifications(emergency, providers):
    """Send emergency notifications to nearby providers"""
    EmailNotificationService.send_emergency_alert(emergency, providers)
    for provider in providers:
        if provider.user.phone:
            SMSNotificationService.send_emergency_alert_sms(emergency, provider)
