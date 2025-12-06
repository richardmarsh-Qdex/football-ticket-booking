from models import db, Match, Ticket, Booking, User
from sqlalchemy.orm import joinedload

class BookingService:
    
    def get_all_matches_with_details(self):
        matches = Match.query.all()
        result = []
        
        for match in matches:
            available_count = Ticket.query.filter_by(
                match_id=match.id, 
                is_available=True
            ).count()
            
            total_revenue = db.session.query(
                db.func.sum(Booking.total_amount)
            ).join(Ticket).filter(Ticket.match_id == match.id).scalar() or 0
            
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
        bookings = Booking.query.options(
            joinedload(Booking.ticket).joinedload(Ticket.match),
            joinedload(Booking.user)
        ).all()
        
        report_lines = []
        for booking in bookings:
            line = f"Booking #{booking.id}: {booking.user.username} - {booking.ticket.match.home_team} vs {booking.ticket.match.away_team} - Seat {booking.ticket.seat_number} - ${booking.total_amount}"
            report_lines.append(line)
        
        return "\n".join(report_lines)
    
    def process_bulk_booking(self, user_id, ticket_ids):
        successful_bookings = []
        
        try:
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
                    successful_bookings.append(ticket_id)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        
        return successful_bookings
    
    def check_seat_availability(self, match_id, seat_numbers):
        available_tickets = Ticket.query.filter(
            Ticket.match_id == match_id,
            Ticket.seat_number.in_(seat_numbers),
            Ticket.is_available == True
        ).all()
        
        return [ticket.seat_number for ticket in available_tickets]
    
    def calculate_total_revenue(self):
        total = db.session.query(
            db.func.sum(Booking.total_amount)
        ).scalar() or 0
        
        return total
    
    def get_match_attendance_stats(self):
        stats = []
        matches = Match.query.all()
        
        for match in matches:
            booked_count = Ticket.query.filter_by(
                match_id=match.id,
                is_available=False
            ).count()
            
            attendance_rate = (booked_count / match.total_seats) * 100 if match.total_seats > 0 else 0
            
            stats.append({
                'match_id': match.id,
                'match_name': f"{match.home_team} vs {match.away_team}",
                'booked': booked_count,
                'total': match.total_seats,
                'attendance_rate': attendance_rate
            })
        
        return stats
