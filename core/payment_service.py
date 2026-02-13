"""
Razorpay Payment Service
Handles all payment-related operations for the Legal Platform
"""

import razorpay
import hashlib
import hmac
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Razorpay Payment Gateway Service"""
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount: Decimal, currency: str = 'INR', 
                     receipt: str = None, notes: dict = None) -> dict:
        """
        Create a Razorpay order
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            currency: Currency code (default: INR)
            receipt: Optional receipt ID
            notes: Optional notes dictionary
        
        Returns:
            Razorpay order object
        """
        try:
            # Convert to paise (Razorpay requires amount in smallest unit)
            amount_paise = int(float(amount) * 100)
            
            order_data = {
                'amount': amount_paise,
                'currency': currency,
                'receipt': receipt or f'receipt_{timezone.now().timestamp()}',
                'notes': notes or {},
            }
            
            order = self.client.order.create(data=order_data)
            logger.info(f"Created Razorpay order: {order['id']}")
            return {
                'success': True,
                'order': order,
                'order_id': order['id'],
                'amount': amount,
                'amount_paise': amount_paise,
                'currency': currency,
            }
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def verify_payment_signature(self, razorpay_order_id: str, 
                                  razorpay_payment_id: str, 
                                  razorpay_signature: str) -> bool:
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate signature
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(generated_signature, razorpay_signature)
            
            if is_valid:
                logger.info(f"Payment signature verified for order: {razorpay_order_id}")
            else:
                logger.warning(f"Invalid payment signature for order: {razorpay_order_id}")
            
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying payment signature: {str(e)}")
            return False
    
    def fetch_payment(self, payment_id: str) -> dict:
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            Payment details dictionary
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                'success': True,
                'payment': payment,
            }
        except Exception as e:
            logger.error(f"Error fetching payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def capture_payment(self, payment_id: str, amount: Decimal, 
                        currency: str = 'INR') -> dict:
        """
        Capture an authorized payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture
            currency: Currency code
        
        Returns:
            Capture result dictionary
        """
        try:
            amount_paise = int(float(amount) * 100)
            payment = self.client.payment.capture(payment_id, amount_paise, {
                'currency': currency
            })
            logger.info(f"Payment captured: {payment_id}")
            return {
                'success': True,
                'payment': payment,
            }
        except Exception as e:
            logger.error(f"Error capturing payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def refund_payment(self, payment_id: str, amount: Decimal = None, 
                       notes: dict = None) -> dict:
        """
        Create a refund for a payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund (if None, full refund)
            notes: Optional notes
        
        Returns:
            Refund result dictionary
        """
        try:
            refund_data = {'notes': notes or {}}
            
            if amount:
                refund_data['amount'] = int(float(amount) * 100)
            
            refund = self.client.payment.refund(payment_id, refund_data)
            logger.info(f"Refund created for payment: {payment_id}")
            return {
                'success': True,
                'refund': refund,
            }
        except Exception as e:
            logger.error(f"Error creating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_order_payments(self, order_id: str) -> dict:
        """
        Fetch all payments for an order
        
        Args:
            order_id: Razorpay order ID
        
        Returns:
            List of payments
        """
        try:
            payments = self.client.order.payments(order_id)
            return {
                'success': True,
                'payments': payments.get('items', []),
            }
        except Exception as e:
            logger.error(f"Error fetching order payments: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }


# Singleton instance
payment_service = PaymentService() if hasattr(settings, 'RAZORPAY_KEY_ID') else None


def get_payment_service():
    """Get payment service instance with lazy initialization"""
    global payment_service
    if payment_service is None:
        if hasattr(settings, 'RAZORPAY_KEY_ID') and settings.RAZORPAY_KEY_ID:
            payment_service = PaymentService()
        else:
            logger.warning("Razorpay credentials not configured")
            return None
    return payment_service
