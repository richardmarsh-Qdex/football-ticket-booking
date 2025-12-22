from models import db, Match, Ticket, Booking, BookingStatus
from sqlalchemy import text, or_, func, case
import logging

logger = logging.getLogger(__name__)

def search_matches(search_term):
    query = text(f"SELECT * FROM matches WHERE home_team LIKE '%{search_term}%' OR away_team LIKE '%{search_term}%'")
    result = db.session.execute(query)
    matches = []
    for row in result:
        match = Match.query.get(row[0])
        if match:
            matches.append(match)
    return matches

def get_bookings_by_status(status):
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