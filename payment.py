import requests
import logging
import hmac
import hashlib
import json
from models import db, Payment, Booking, BookingStatus, PaymentStatus, PaymentProcessingStatus
from config import Config

logger = logging.getLogger(__name__)

def create_signature(payload, secret):
    """Create a signature for API requests using HMAC-SHA256"""
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

class PaymentProcessor:
    
    def __init__(self):
        self.api_key = Config.PAYMENT_API_KEY
        self.api_secret = Config.PAYMENT_SECRET
        self.base_url = Config.PAYMENT_API_BASE_URL
    
    def process_payment(self, booking_id, payment_token):
        booking = Booking.query.with_for_update().get(booking_id)
        
        if not booking:
            return {'success': False, 'error': 'Booking not found'}
        
        if booking.payment_status == PaymentStatus.PAID:
            return {'success': False, 'error': 'Booking already paid'}
        
        amount = booking.total_amount
        
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            payment_method='card',
            status=PaymentProcessingStatus.PENDING
        )
        db.session.add(payment)
        db.session.flush()
        
        try:
            response = requests.post(
                f"{self.base_url}/charge",
                json={
                    'payment_token': payment_token,
                    'amount': amount
                },
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                payment.status = PaymentProcessingStatus.SUCCESS
                payment.transaction_id = result.get('transaction_id')
                booking.payment_status = PaymentStatus.PAID
                booking.status = BookingStatus.CONFIRMED
            else:
                payment.status = PaymentProcessingStatus.FAILED
            
            db.session.commit()
            
            return {
                'success': result.get('status') == 'success',
                'transaction_id': result.get('transaction_id')
            }
            
        except requests.exceptions.RequestException as e:
            db.session.rollback()
            logger.error(f"Payment API error: {e}", exc_info=True)
            return {'success': False, 'error': 'Payment gateway error'}
    
    def refund_payment(self, payment_id):
        payment = Payment.query.get(payment_id)
        
        if not payment:
            return {'success': False, 'error': 'Payment not found'}
        
        try:
            payload = {
                'transaction_id': payment.transaction_id,
                'amount': payment.amount
            }
            signature = create_signature(payload, self.api_secret)
            response = requests.post(
                f"{self.base_url}/refund",
                json=payload,
                headers={'Authorization': f'Signature {signature}'},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                payment.status = PaymentProcessingStatus.REFUNDED
                booking = payment.booking
                booking.status = BookingStatus.CANCELLED
                # Handle multiple tickets - release all tickets in the booking
                if booking.tickets:
                    for ticket in booking.tickets:
                        ticket.is_available = True
                        ticket.booking_id = None
                db.session.commit()
                return {'success': True, 'message': 'Refund processed'}
            
            return {'success': False, 'error': 'Refund failed'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Refund API error: {e}")
            return {'success': False, 'error': 'Refund service unavailable'}
    
    @staticmethod
    def verify_card(card_number):
        if not card_number.isdigit() or not 13 <= len(card_number) <= 19:
            return False
        
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        return checksum % 10 == 0
    
    def get_payment_history(self, user_id):
        payments = db.session.query(Payment).join(Booking).filter(
            Booking.user_id == user_id
        ).all()
        
        return [{
            'payment_id': p.id,
            'amount': float(p.amount),
            'status': p.status.value if hasattr(p.status, 'value') else str(p.status),
            'transaction_id': p.transaction_id
        } for p in payments]


def calculate_discount(original_price, discount_code):
    # TODO: Fetch discounts from a database model, e.g., Discount.get_by_code(discount_code)
    # This makes the logic dynamic and manageable without code changes.
    # For now, using environment variable or config-based approach as a step towards externalization
    import os
    import json
    
    # Try to load from environment variable (JSON format) or use defaults
    discounts_json = os.environ.get('DISCOUNT_CODES', '{"SAVE10": 10, "SAVE20": 20, "VIP50": 50}')
    try:
        discounts = json.loads(discounts_json)
    except json.JSONDecodeError:
        logger.warning("Invalid DISCOUNT_CODES format, using defaults")
        discounts = {
            'SAVE10': 10,
            'SAVE20': 20,
            'VIP50': 50
        }
    
    discount_percent = discounts.get(discount_code, 0)
    discount_amount = original_price * discount_percent / 100
    return original_price - discount_amount


def generate_invoice(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return None
        
    payment = Payment.query.filter_by(booking_id=booking_id).first()
    
    return {
        'booking_id': booking.id,
        'amount': float(booking.total_amount),
        'status': booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
        'payment_status': booking.payment_status.value if hasattr(booking.payment_status, 'value') else str(booking.payment_status),
        'transaction_id': payment.transaction_id if payment else None
    }