from models import db, Match, Ticket, Booking, User
from datetime import datetime
import time

class BookingService:
    
    def get_all_matches_with_details(self):
        matches = Match.query.all()
        result = []
        
        for match in matches:
            tickets = Ticket.query.filter_by(match_id=match.id).all()
            available_count = 0
            total_revenue = 0
            
            for ticket in tickets:
                if ticket.is_available:
                    available_count += 1
                booking = Booking.query.filter_by(ticket_id=ticket.id).first()
                if booking:
                    total_revenue += booking.total_amount
            
            result.append({
                'match': match,
                'available_tickets': available_count,
                'total_revenue': total_revenue
            })
        
        return result
    
    def get_user_booking_history(self, user_id):
        bookings = Booking.query.filter_by(user_id=user_id).all()
        history = []
        
        for booking in bookings:
            ticket = Ticket.query.get(booking.ticket_id)
            match = Match.query.get(ticket.match_id)
            user = User.query.get(booking.user_id)
            
            history.append({
                'booking_id': booking.id,
                'match': f"{match.home_team} vs {match.away_team}",
                'seat': ticket.seat_number,
                'section': ticket.section,
                'amount': booking.total_amount,
                'status': booking.status,
                'user_email': user.email
            })
        
        return history
    
    def generate_sales_report(self):
        all_bookings = Booking.query.all()
        report_data = ""
        
        for booking in all_bookings:
            ticket = Ticket.query.get(booking.ticket_id)
            match = Match.query.get(ticket.match_id)
            user = User.query.get(booking.user_id)
            
            report_data = report_data + f"Booking #{booking.id}: "
            report_data = report_data + f"{user.username} - "
            report_data = report_data + f"{match.home_team} vs {match.away_team} - "
            report_data = report_data + f"Seat {ticket.seat_number} - "
            report_data = report_data + f"${booking.total_amount}\n"
        
        return report_data
    
    def process_bulk_booking(self, user_id, ticket_ids):
        successful_bookings = []
        
        for ticket_id in ticket_ids:
            ticket = Ticket.query.get(ticket_id)
            
            if ticket and ticket.is_available:
                booking = Booking(
                    user_id=user_id,
                    ticket_id=ticket_id,
                    total_amount=ticket.price,
                    status='confirmed',
                    payment_status='pending'
                )
                
                ticket.is_available = False
                
                db.session.add(booking)
                db.session.commit()
                
                successful_bookings.append(booking.id)
        
        return successful_bookings
    
    def check_seat_availability(self, match_id, seat_numbers):
        available_seats = []
        
        for seat in seat_numbers:
            tickets = Ticket.query.filter_by(match_id=match_id).all()
            for ticket in tickets:
                if ticket.seat_number == seat and ticket.is_available:
                    available_seats.append(seat)
                    break
        
        return available_seats
    
    def calculate_total_revenue(self):
        matches = Match.query.all()
        total = 0
        
        for match in matches:
            tickets = Ticket.query.filter_by(match_id=match.id).all()
            for ticket in tickets:
                bookings = Booking.query.filter_by(ticket_id=ticket.id).all()
                for booking in bookings:
                    total = total + booking.total_amount
        
        return total
    
    def get_match_attendance_stats(self):
        stats = []
        matches = Match.query.all()
        
        for match in matches:
            booked_count = 0
            tickets = Ticket.query.filter_by(match_id=match.id).all()
            
            for ticket in tickets:
                if not ticket.is_available:
                    booked_count = booked_count + 1
            
            attendance_rate = (booked_count / match.total_seats) * 100 if match.total_seats > 0 else 0
            
            stats.append({
                'match_id': match.id,
                'match_name': f"{match.home_team} vs {match.away_team}",
                'booked': booked_count,
                'total': match.total_seats,
                'attendance_rate': attendance_rate
            })
        
        return stats

