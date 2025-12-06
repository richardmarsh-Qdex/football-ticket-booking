from models import db, Match, Ticket, Booking
from sqlalchemy import text, or_

def search_matches(search_term):
    search_pattern = f"%{search_term}%"
    return Match.query.filter(
        or_(Match.home_team.like(search_pattern), Match.away_team.like(search_pattern))
    ).all()

def get_bookings_by_status(status):
    return Booking.query.filter_by(status=status).all()

def update_ticket_availability(ticket_id, available):
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        ticket.is_available = available
        db.session.commit()

def get_match_statistics(match_id):
    total_tickets = Ticket.query.filter_by(match_id=match_id).count()
    available_tickets = Ticket.query.filter_by(match_id=match_id, is_available=True).count()
    total_bookings = db.session.query(Booking).join(Ticket).filter(Ticket.match_id == match_id).count()
    
    return {
        'total_tickets': total_tickets,
        'available_tickets': available_tickets,
        'total_bookings': total_bookings
    }
