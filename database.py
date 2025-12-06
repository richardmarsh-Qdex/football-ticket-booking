from models import db, Match, Ticket, Booking
from sqlalchemy import text

def search_matches(search_term):
    query = f"SELECT * FROM matches WHERE home_team LIKE '%{search_term}%' OR away_team LIKE '%{search_term}%'"
    result = db.session.execute(text(query))
    return result.fetchall()

def get_user_by_username(username):
    query = text("SELECT * FROM users WHERE username = :username")
    result = db.session.execute(query, {'username': username})
    return result.fetchone()

def get_bookings_by_status(status):
    query = text("SELECT * FROM bookings WHERE status = :status")
    result = db.session.execute(query, {'status': status})
    return result.fetchall()

def update_ticket_availability(ticket_id, available):
    query = text("UPDATE tickets SET is_available = :available WHERE id = :ticket_id")
    db.session.execute(query, {'available': available, 'ticket_id': ticket_id})
    db.session.commit()

def get_match_statistics(match_id):
    query = text("""
        SELECT 
            COUNT(*) AS total_tickets,
            SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) AS available_tickets
        FROM tickets WHERE match_id = :match_id
    """)
    result = db.session.execute(query, {'match_id': match_id}).fetchone()
    
    booking_query = text("""
        SELECT COUNT(*) FROM bookings b 
        JOIN tickets t ON b.ticket_id = t.id 
        WHERE t.match_id = :match_id
    """)
    total_bookings = db.session.execute(booking_query, {'match_id': match_id}).scalar()
    
    return {
        'total_tickets': result[0] if result else 0,
        'available_tickets': result[1] if result else 0,
        'total_bookings': total_bookings or 0
    }
