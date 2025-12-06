from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import UniqueConstraint, Enum as SQLEnum
import enum

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    total_seats = db.Column(db.Integer, default=50000)
    # This column is redundant with Ticket.is_available and can be removed.
    # available_seats = db.Column(db.Integer, default=50000)
    ticket_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    tickets = db.relationship('Ticket', backref='match', lazy=True)
    
    def __repr__(self):
        return f'<Match {self.home_team} vs {self.away_team}>'


class Ticket(db.Model):
    __tablename__ = 'tickets'
    __table_args__ = (UniqueConstraint('match_id', 'seat_number', 'section', name='_match_seat_section_uc'),)
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    
    def __repr__(self):
        return f'<Ticket {self.seat_number}>'


class BookingStatus(enum.Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'

class PaymentStatus(enum.Enum):
    UNPAID = 'unpaid'
    PENDING = 'pending'
    PAID = 'paid'
    REFUNDED = 'refunded'

class PaymentProcessingStatus(enum.Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    REFUNDED = 'refunded'

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Removed ticket_id - now using one-to-many relationship via Ticket.booking_id
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    payment_status = db.Column(SQLEnum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # One-to-many relationship: a booking can have multiple tickets
    tickets = db.relationship('Ticket', backref='booking', lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.id}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100))
    status = db.Column(SQLEnum(PaymentProcessingStatus), default=PaymentProcessingStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    booking = db.relationship('Booking', backref=db.backref('payment', uselist=False))
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'