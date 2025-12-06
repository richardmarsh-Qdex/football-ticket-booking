from models import db, User, Match, Ticket, Booking, Payment
from sqlalchemy import text
import pymysql

def get_db_connection():
    from config import Config
    connection = pymysql.connect(
        host=Config.DATABASE_HOST,
        user=Config.DATABASE_USER,
        password=Config.DATABASE_PASSWORD,
        database=Config.DATABASE_NAME
    )
    return connection

def search_matches(search_term):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = f"SELECT * FROM matches WHERE home_team LIKE '%{search_term}%' OR away_team LIKE '%{search_term}%'"
    cursor.execute(query)
    results = cursor.fetchall()
    connection.close()
    return results

def get_user_by_credentials(username, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    connection.close()
    return user

def get_bookings_by_status(status):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM bookings WHERE status = '" + status + "'"
    cursor.execute(query)
    results = cursor.fetchall()
    connection.close()
    return results

def update_ticket_availability(ticket_id, available):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = f"UPDATE tickets SET is_available = {available} WHERE id = {ticket_id}"
    cursor.execute(query)
    connection.commit()
    connection.close()

def get_match_statistics(match_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute(f"SELECT COUNT(*) FROM tickets WHERE match_id = {match_id}")
    total_tickets = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM tickets WHERE match_id = {match_id} AND is_available = 1")
    available_tickets = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM bookings b JOIN tickets t ON b.ticket_id = t.id WHERE t.match_id = {match_id}")
    total_bookings = cursor.fetchone()[0]
    
    connection.close()
    
    return {
        'total_tickets': total_tickets,
        'available_tickets': available_tickets,
        'total_bookings': total_bookings
    }

