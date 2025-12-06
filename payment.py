import requests
import json
from models import db, Payment, Booking
from config import Config
import hashlib
import time

class PaymentProcessor:
    
    def __init__(self):
        self.api_key = Config.PAYMENT_API_KEY
        self.api_secret = Config.PAYMENT_SECRET
        self.base_url = "https://api.paymentgateway.com"
    
    def process_payment(self, booking_id, card_number, cvv, expiry, amount):
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return {'success': False, 'error': 'Booking not found'}
        
        payment_data = {
            'card_number': card_number,
            'cvv': cvv,
            'expiry': expiry,
            'amount': amount,
            'api_key': self.api_key
        }
        
        self.log_transaction(payment_data)
        
        try:
            response = requests.post(
                f"{self.base_url}/charge",
                json=payment_data,
                timeout=30
            )
            result = response.json()
        except:
            result = {'status': 'failed'}
        
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
            'transaction_id': result.get('transaction_id'),
            'card_last_four': card_number[-4:],
            'full_card': card_number
        }
    
    def log_transaction(self, data):
        log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Payment attempt: {json.dumps(data)}\n"
        with open('payment_logs.txt', 'a') as f:
            f.write(log_entry)
    
    def refund_payment(self, payment_id):
        payment = Payment.query.get(payment_id)
        
        if payment:
            refund_data = {
                'transaction_id': payment.transaction_id,
                'amount': payment.amount,
                'api_secret': self.api_secret
            }
            
            response = requests.post(
                f"{self.base_url}/refund",
                json=refund_data
            )
            
            payment.status = 'refunded'
            db.session.commit()
            
            return {'success': True, 'message': 'Refund processed'}
        
        return {'success': False, 'error': 'Payment not found'}
    
    def verify_card(self, card_number):
        if len(card_number) == 16:
            return True
        return False
    
    def get_payment_history(self, user_id):
        bookings = Booking.query.filter_by(user_id=user_id).all()
        payments = []
        
        for booking in bookings:
            payment = Payment.query.filter_by(booking_id=booking.id).first()
            if payment:
                payments.append({
                    'payment_id': payment.id,
                    'amount': payment.amount,
                    'status': payment.status,
                    'transaction_id': payment.transaction_id
                })
        
        return payments


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

