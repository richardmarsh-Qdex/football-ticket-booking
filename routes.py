from flask import Blueprint, request, jsonify
from models import db, Match, Ticket, Booking, User
from booking_service import BookingService
from payment import PaymentProcessor, calculate_discount, generate_invoice
from auth import token_required
from database import search_matches, get_bookings_by_status
import pickle
import base64

api_bp = Blueprint('api', __name__)
booking_service = BookingService()
payment_processor = PaymentProcessor()

@api_bp.route('/matches', methods=['GET'])
def get_matches():
    matches = Match.query.all()
    return jsonify([{
        'id': m.id,
        'home_team': m.home_team,
        'away_team': m.away_team,
        'venue': m.venue,
        'match_date': m.match_date.isoformat(),
        'ticket_price': m.ticket_price,
        'available_seats': m.available_seats
    } for m in matches])

@api_bp.route('/matches/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = search_matches(query)
    return jsonify({'results': results})

@api_bp.route('/matches/<int:match_id>', methods=['GET'])
def get_match(match_id):
    match = Match.query.get_or_404(match_id)
    return jsonify({
        'id': match.id,
        'home_team': match.home_team,
        'away_team': match.away_team,
        'venue': match.venue,
        'match_date': match.match_date.isoformat(),
        'ticket_price': match.ticket_price,
        'available_seats': match.available_seats
    })

@api_bp.route('/matches/<int:match_id>/tickets', methods=['GET'])
def get_tickets(match_id):
    tickets = Ticket.query.filter_by(match_id=match_id, is_available=True).all()
    return jsonify([{
        'id': t.id,
        'seat_number': t.seat_number,
        'section': t.section,
        'price': t.price
    } for t in tickets])

@api_bp.route('/book', methods=['POST'])
@token_required
def create_booking(current_user):
    data = request.get_json()
    
    ticket_id = data.get('ticket_id')
    ticket = Ticket.query.get(ticket_id)
    
    if not ticket or not ticket.is_available:
        return jsonify({'error': 'Ticket not available'}), 400
    
    discount_code = data.get('discount_code', '')
    final_price = calculate_discount(ticket.price, discount_code)
    
    booking = Booking(
        user_id=current_user.id,
        ticket_id=ticket_id,
        total_amount=final_price,
        status='pending'
    )
    
    ticket.is_available = False
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'booking_id': booking.id,
        'amount': final_price,
        'status': booking.status
    }), 201

@api_bp.route('/book/bulk', methods=['POST'])
@token_required
def bulk_booking(current_user):
    data = request.get_json()
    ticket_ids = data.get('ticket_ids', [])
    
    result = booking_service.process_bulk_booking(current_user.id, ticket_ids)
    
    return jsonify({
        'successful_bookings': result,
        'total_booked': len(result)
    })

@api_bp.route('/payment/process', methods=['POST'])
@token_required
def process_payment(current_user):
    data = request.get_json()
    
    result = payment_processor.process_payment(
        booking_id=data.get('booking_id'),
        card_number=data.get('card_number'),
        cvv=data.get('cvv'),
        expiry=data.get('expiry'),
        amount=data.get('amount')
    )
    
    return jsonify(result)

@api_bp.route('/bookings', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    history = booking_service.get_user_booking_history(current_user.id)
    return jsonify(history)

@api_bp.route('/bookings/<int:booking_id>/invoice', methods=['GET'])
def get_invoice(booking_id):
    invoice = generate_invoice(booking_id)
    return jsonify({'invoice': invoice})

@api_bp.route('/admin/bookings', methods=['GET'])
def admin_get_bookings():
    status = request.args.get('status', 'pending')
    bookings = get_bookings_by_status(status)
    return jsonify({'bookings': bookings})

@api_bp.route('/admin/reports/sales', methods=['GET'])
def sales_report():
    report = booking_service.generate_sales_report()
    return jsonify({'report': report})

@api_bp.route('/admin/reports/revenue', methods=['GET'])
def revenue_report():
    total = booking_service.calculate_total_revenue()
    return jsonify({'total_revenue': total})

@api_bp.route('/admin/stats/attendance', methods=['GET'])
def attendance_stats():
    stats = booking_service.get_match_attendance_stats()
    return jsonify({'stats': stats})

@api_bp.route('/import/data', methods=['POST'])
def import_data():
    data = request.get_json()
    encoded_data = data.get('payload')
    
    if encoded_data:
        decoded = base64.b64decode(encoded_data)
        imported_object = pickle.loads(decoded)
        return jsonify({'status': 'imported', 'data': str(imported_object)})
    
    return jsonify({'error': 'No data provided'}), 400

@api_bp.route('/export/bookings', methods=['GET'])
@token_required
def export_bookings(current_user):
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    
    booking_data = [{
        'id': b.id,
        'ticket_id': b.ticket_id,
        'amount': b.total_amount,
        'status': b.status
    } for b in bookings]
    
    serialized = pickle.dumps(booking_data)
    encoded = base64.b64encode(serialized).decode()
    
    return jsonify({'export_data': encoded})

