import requests
import json
import logging
from models import db, Payment, Booking
from config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentProcessor:
    
    def __init__(self):
        self.api_key = Config.PAYMENT_API_KEY
        self.api_secret = Config.PAYMENT_SECRET
        self.base_url = "https://api.paymentgateway.com"
    
    def process_payment(self, booking_id, payment_token, amount):
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return {'success': False, 'error': 'Booking not found'}
        
        payment_data = {
            'payment_token': payment_token,
            'amount': amount,
            'api_key': self.api_key
        }
        
        self.log_transaction(booking_id, amount)
        
        try:
            response = requests.post(
                f"{self.base_url}/charge",
                json=payment_data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment API error: {e}")
            result = {'status': 'failed', 'error': 'Payment gateway error'}
        
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            payment_method='card',
            transaction_id=result.get('transaction_id'),
            status=result.get('status', 'failed')
        )
        
        db.session.add(payment)
        
        if result.get('status') == 'success':
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
        
        db.session.commit()
        
        return {
            'success': result.get('status') == 'success',
            'transaction_id': result.get('transaction_id')
        }
    
    def log_transaction(self, booking_id, amount):
        log_entry = f"Payment attempt for booking {booking_id}: ${amount}"
        logger.info(log_entry)
    
    def refund_payment(self, payment_id):
        payment = Payment.query.get(payment_id)
        
        if not payment:
            return {'success': False, 'error': 'Payment not found'}
        
        try:
            refund_data = {
                'transaction_id': payment.transaction_id,
                'amount': payment.amount
            }
            
            response = requests.post(
                f"{self.base_url}/refund",
                json=refund_data,
                headers={'Authorization': f'Bearer {self.api_secret}'},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                payment.status = 'refunded'
                db.session.commit()
                return {'success': True, 'message': 'Refund processed'}
            
            return {'success': False, 'error': 'Refund failed'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Refund API error: {e}")
            return {'success': False, 'error': 'Refund service unavailable'}
    
    def verify_card(self, card_number):
        if not card_number.isdigit() or not 13 <= len(card_number) <= 19:
            return False
        
        # Luhn algorithm check
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
            'amount': p.amount,
            'status': p.status,
            'transaction_id': p.transaction_id
        } for p in payments]


def calculate_discount(original_price, discount_code):
    discounts = {
        'SAVE10': 10,
        'SAVE20': 20,
        'VIP50': 50
    }
    
    discount_percent = discounts.get(discount_code, 0)
    discount_amount = original_price * discount_percent / 100
    final_price = original_price - discount_amount
    
    return final_price


def generate_invoice(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return None
        
    payment = Payment.query.filter_by(booking_id=booking_id).first()
    
    invoice = f"""
    ====================================
    FOOTBALL TICKET BOOKING INVOICE
    ====================================
    Booking ID: {booking.id}
    Amount: ${booking.total_amount}
    Status: {booking.status}
    Payment Status: {booking.payment_status}
    Transaction: {payment.transaction_id if payment else 'N/A'}
    ====================================
    """
    
    return invoice
