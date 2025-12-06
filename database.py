from models import db, Match, Ticket, Booking
from sqlalchemy import text, or_, func, case

def search_matches(search_term):
    return Match.query.filter(
        or_(Match.home_team.like('%' + search_term + '%'), Match.away_team.like('%' + search_term + '%'))
    ).all()

def get_bookings_by_status(status):
    return Booking.query.filter_by(status=status).all()

def update_ticket_availability(ticket_id, available):
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        ticket.is_available = available
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # It's good practice to log the error here
            raise e

def get_match_statistics(match_id):
    stats = db.session.query(
        func.count(Ticket.id).label('total_tickets'),
        func.sum(case((Ticket.is_available == True, 1), else_=0)).label('available_tickets'),
        func.count(Booking.id).label('total_bookings')
    ).select_from(Ticket).outerjoin(Booking).filter(Ticket.match_id == match_id).one()
    
    return {
        'total_tickets': stats.total_tickets,
        'available_tickets': stats.available_tickets,
        'total_bookings': stats.total_bookings
    }