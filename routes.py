from flask import Blueprint, request, jsonify
from models import db, Match, Ticket, Booking
from booking_service import BookingService
from payment import PaymentProcessor, calculate_discount, generate_invoice
from auth import token_required
from database import search_matches, get_bookings_by_status

api_bp = Blueprint('api', __name__)
booking_service = BookingService()
payment_processor = PaymentProcessor()

MAX_PER_PAGE = 100

@api_bp.route('/matches', methods=['GET'])
def get_matches():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), MAX_PER_PAGE)
    
    matches = Match.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'matches': [{
            'id': m.id,
            'home_team': m.home_team,
            'away_team': m.away_team,
            'venue': m.venue,
            'match_date': m.match_date.isoformat(),
            'ticket_price': m.ticket_price,
            'available_seats': m.available_seats
        } for m in matches.items],
        'total': matches.total,
        'pages': matches.pages,
        'current_page': page
    })

@api_bp.route('/matches/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    results = search_matches(query)
    return jsonify({'results': [{
        'id': m.id,
        'home_team': m.home_team,
        'away_team': m.away_team,
        'venue': m.venue
    } for m in results]})

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
    
    if not data or 'booking_id' not in data or 'payment_token' not in data:
        return jsonify({'error': 'Missing required payment information'}), 400
    
    booking = Booking.query.get(data.get('booking_id'))
    if not booking or booking.user_id != current_user.id:
        return jsonify({'error': 'Booking not found'}), 404
    
    result = payment_processor.process_payment(
        booking_id=booking.id,
        payment_token=data.get('payment_token')
    )
    
    return jsonify(result)

@api_bp.route('/bookings', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    history = booking_service.get_user_booking_history(current_user.id)
    return jsonify(history)

@api_bp.route('/bookings/<int:booking_id>/invoice', methods=['GET'])
@token_required
def get_invoice(current_user, booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    
    invoice = generate_invoice(booking_id)
    return jsonify({'invoice': invoice})

@api_bp.route('/admin/bookings', methods=['GET'])
def admin_get_bookings():
    status = request.args.get('status', 'pending')
    bookings = get_bookings_by_status(status)
    return jsonify({'bookings': [{
        'id': b.id,
        'user_id': b.user_id,
        'ticket_id': b.ticket_id,
        'status': b.status,
        'total_amount': b.total_amount
    } for b in bookings]})

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
