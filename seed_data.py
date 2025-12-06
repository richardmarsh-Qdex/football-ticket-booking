from app import create_app
from models import db, User, Match, Ticket
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed_database():
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        admin = User(
            username='admin',
            email='admin@footballtickets.com',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        
        user1 = User(
            username='john_doe',
            email='john@example.com',
            password=generate_password_hash('password123')
        )
        
        user2 = User(
            username='jane_smith',
            email='jane@example.com',
            password=generate_password_hash('password123')
        )
        
        db.session.add_all([admin, user1, user2])
        
        matches = [
            Match(
                home_team='Manchester United',
                away_team='Liverpool',
                venue='Old Trafford',
                match_date=datetime.now() + timedelta(days=7),
                total_seats=75000,
                available_seats=75000,
                ticket_price=89.99
            ),
            Match(
                home_team='Chelsea',
                away_team='Arsenal',
                venue='Stamford Bridge',
                match_date=datetime.now() + timedelta(days=14),
                total_seats=40000,
                available_seats=40000,
                ticket_price=79.99
            ),
            Match(
                home_team='Manchester City',
                away_team='Tottenham',
                venue='Etihad Stadium',
                match_date=datetime.now() + timedelta(days=21),
                total_seats=55000,
                available_seats=55000,
                ticket_price=99.99
            )
        ]
        
        db.session.add_all(matches)
        db.session.commit()
        
        sections = ['VIP', 'Premium', 'Standard', 'Economy']
        prices = {'VIP': 199.99, 'Premium': 149.99, 'Standard': 89.99, 'Economy': 49.99}
        
        for match in matches:
            for section in sections:
                for i in range(1, 101):
                    ticket = Ticket(
                        match_id=match.id,
                        seat_number=f"{section[0]}{i:03d}",
                        section=section,
                        price=prices[section],
                        is_available=True
                    )
                    db.session.add(ticket)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
