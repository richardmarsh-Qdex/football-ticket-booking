from models import db, Match, Ticket, Booking, BookingStatus
from sqlalchemy import text, or_, func, case
import logging

logger = logging.getLogger(__name__)

def search_matches(search_term):
    # Using parameterized query to prevent SQL injection
    # Note: LIKE with leading wildcard prevents index usage - consider full-text search for production
    search_pattern = f"%{search_term}%"
    return Match.query.filter(
        or_(Match.home_team.like(search_pattern), Match.away_team.like(search_pattern))
    ).all()

def get_bookings_by_status(status):
    # Convert string status to enum if needed
    status_map = {
        'pending': BookingStatus.PENDING,
        'confirmed': BookingStatus.CONFIRMED,
        'cancelled': BookingStatus.CANCELLED
    }
    enum_status = status_map.get(status.lower())
    if enum_status:
        return Booking.query.filter_by(status=enum_status).all()
    return Booking.query.filter_by(status=status).all()

def update_ticket_availability(ticket_id, available):
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        ticket.is_available = available
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update ticket availability for ticket {ticket_id}: {e}", exc_info=True)
            raise e

def get_match_statistics(match_id):
    stats = db.session.query(
        func.count(Ticket.id).label('total_tickets'),
        func.sum(case((Ticket.is_available == True, 1), else_=0)).label('available_tickets'),
        func.count(Booking.id).label('total_bookings')
    ).select_from(Ticket).outerjoin(Booking).filter(Ticket.match_id == match_id).one_or_none()
    
    if not stats:
        return {
            'total_tickets': 0,
            'available_tickets': 0,
            'total_bookings': 0
        }
    
    return {
        'total_tickets': stats.total_tickets,
        'available_tickets': stats.available_tickets,
        'total_bookings': stats.total_bookings
    }