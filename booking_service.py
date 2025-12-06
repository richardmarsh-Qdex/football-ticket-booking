from models import db, Match, Ticket, Booking, User
from sqlalchemy.orm import joinedload
from sqlalchemy import func

class BookingService:
    
    def get_all_matches_with_details(self):
        matches_data = db.session.query(
            Match,
            func.count(Ticket.id).filter(Ticket.is_available == True).label('available_count'),
            func.coalesce(func.sum(Booking.total_amount), 0).label('total_revenue')
        ).outerjoin(Ticket, Match.id == Ticket.match_id
        ).outerjoin(Booking, Ticket.id == Booking.ticket_id
        ).group_by(Match.id).all()
        
        result = []
        for match, available_count, total_revenue in matches_data:
            result.append({
                'match_id': match.id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'available_tickets': available_count,
                'total_revenue': float(total_revenue)
            })
        
        return result
    
    def get_user_booking_history(self, user_id):
        bookings = Booking.query.filter_by(user_id=user_id).all()
        history = []
        
        for booking in bookings:
            ticket = Ticket.query.get(booking.ticket_id)
            match = Match.query.get(ticket.match_id)
            
            history.append({
                'booking_id': booking.id,
                'match': f"{match.home_team} vs {match.away_team}",
                'seat': ticket.seat_number,
                'section': ticket.section,
                'amount': booking.total_amount,
                'status': booking.status
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
                ticket = Ticket.query.with_for_update().get(ticket_id)
                
                if ticket and ticket.is_available:
                    booking = Booking(
                        user_id=user_id,
                        ticket_id=ticket_id,
                        total_amount=ticket.price,
                        status='confirmed',
                        payment_status='pending'
                    )
                    
                    ticket.is_available = False
                    if ticket.match:
                        ticket.match.available_seats -= 1
                    
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
        total = db.session.query(func.sum(Booking.total_amount)).scalar() or 0
        return float(total)
    
    def get_match_attendance_stats(self):
        stats_data = db.session.query(
            Match.id,
            Match.home_team,
            Match.away_team,
            Match.total_seats,
            func.count(Ticket.id).filter(Ticket.is_available == False).label('booked_count')
        ).outerjoin(Ticket, Match.id == Ticket.match_id
        ).group_by(Match.id).all()
        
        stats = []
        for match_id, home_team, away_team, total_seats, booked_count in stats_data:
            attendance_rate = (booked_count / total_seats) * 100 if total_seats > 0 else 0
            stats.append({
                'match_id': match_id,
                'match_name': f"{home_team} vs {away_team}",
                'booked': booked_count,
                'total': total_seats,
                'attendance_rate': attendance_rate
            })
        
        return stats
