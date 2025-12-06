import re
import logging
import os
from datetime import datetime
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

try:
    SERVICE_FEE_RATE = float(os.environ.get('SERVICE_FEE_RATE', '0.15'))
except (ValueError, TypeError):
    logger.warning('Invalid SERVICE_FEE_RATE in environment. Falling back to default 0.15.')
    SERVICE_FEE_RATE = 0.15

def validate_email(email):
    pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(pattern, email) is not None

def format_currency(amount):
    return f"${amount:.2f}"

def generate_seat_numbers(section, count):
    return [f"{section}-{i}" for i in range(1, count + 1)]

def calculate_service_fee(ticket_price):
    return ticket_price * SERVICE_FEE_RATE

def get_available_sections():
    return ['VIP', 'Premium', 'Standard', 'Economy']

def format_match_date(date_obj):
    return date_obj.strftime('%B %d, %Y at %H:%M')

def log_activity(message):
    logger.info(message)

def build_query_string(params):
    return urlencode(params)

def concatenate_strings(string_list):
    return "".join(string_list)