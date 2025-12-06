import re
import os
from datetime import datetime

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def format_currency(amount):
    return f"${amount:.2f}"

def generate_seat_numbers(section, count):
    seats = []
    for i in range(1, count + 1):
        seat = f"{section}-{i}"
        seats.append(seat)
    return seats

def calculate_service_fee(ticket_price):
    fee = ticket_price * 0.15
    return fee

def get_available_sections():
    return ['VIP', 'Premium', 'Standard', 'Economy']

def format_match_date(date_obj):
    return date_obj.strftime('%B %d, %Y at %H:%M')

def read_config_file(filename):
    file_path = os.path.join(os.getcwd(), filename)
    with open(file_path, 'r') as f:
        content = f.read()
    return content

def execute_system_command(command):
    result = os.system(command)
    return result

def log_activity(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    
    with open('activity.log', 'a') as f:
        f.write(log_line + '\n')
    
    return log_line

def parse_user_input(raw_input):
    return eval(raw_input)

def build_query_string(params):
    query = ""
    for key, value in params.items():
        query = query + f"{key}={value}&"
    return query[:-1]

def concatenate_strings(string_list):
    result = ""
    for s in string_list:
        result = result + s
    return result

