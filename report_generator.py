import csv
import logging
from models import db, Booking, Payment

logger = logging.getLogger(__name__)

def generate_csv_report(output_file):
    """Generate CSV report of all bookings and payments"""
    file_handle = open(output_file, 'w', newline='')
    writer = csv.writer(file_handle)
    
    writer.writerow(['Booking ID', 'User ID', 'Amount', 'Status', 'Transaction ID'])
    
    bookings = Booking.query.all()
    for booking in bookings:
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        writer.writerow([
            booking.id,
            booking.user_id,
            booking.total_amount,
            booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
            payment.transaction_id if payment else None
        ])
    
    return output_file

