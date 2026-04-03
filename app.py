from flask import Flask, render_template, request, redirect, url_for, flash
import json
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'hotel-reservation-secret-key'

BOOKINGS_FILE = 'bookings.json'

# Room types and prices per night
ROOMS = {
    'Standard': 100,
    'Deluxe': 150,
    'Suite': 250
}

def load_bookings():
    """Load bookings from JSON file."""
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_bookings(bookings):
    """Save bookings to JSON file."""
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings, f, indent=2)

def get_reference_number():
    """Generate a unique reference number."""
    return str(uuid.uuid4())[:8].upper()

def is_room_available(room_type, check_in, check_out):
    """Check if a room is available for the given dates."""
    bookings = load_bookings()
    check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
    
    for booking in bookings:
        if booking['room_type'] == room_type and booking['status'] == 'confirmed':
            booking_in = datetime.strptime(booking['check_in'], '%Y-%m-%d')
            booking_out = datetime.strptime(booking['check_out'], '%Y-%m-%d')
            
            # Check for overlap
            if not (check_out_date <= booking_in or check_in_date >= booking_out):
                return False
    return True

def calculate_total_price(room_type, check_in, check_out):
    """Calculate total price for a booking."""
    check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
    nights = (check_out_date - check_in_date).days
    return ROOMS[room_type] * nights

@app.route('/')
def index():
    """Home page with search form."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Search for available rooms."""
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    
    # Validate dates
    try:
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        
        if check_in_date >= check_out_date:
            flash('Check-out date must be after check-in date.', 'error')
            return redirect(url_for('index'))
        if check_in_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            flash('Check-in date cannot be in the past.', 'error')
            return redirect(url_for('index'))
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('index'))
    
    # Find available rooms
    available_rooms = {}
    for room_type in ROOMS:
        if is_room_available(room_type, check_in, check_out):
            nights = (check_out_date - check_in_date).days
            total_price = calculate_total_price(room_type, check_in, check_out)
            available_rooms[room_type] = {
                'price_per_night': ROOMS[room_type],
                'nights': nights,
                'total_price': total_price
            }
    
    return render_template('search_results.html', 
                         available_rooms=available_rooms,
                         check_in=check_in,
                         check_out=check_out)

@app.route('/book/<room_type>')
def book_room(room_type):
    """Booking form for selected room."""
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    
    if room_type not in ROOMS:
        return redirect(url_for('index'))
    
    if not check_in or not check_out:
        return redirect(url_for('index'))
    
    # Verify room is still available
    if not is_room_available(room_type, check_in, check_out):
        return redirect(url_for('index'))
    
    total_price = calculate_total_price(room_type, check_in, check_out)
    
    return render_template('book.html',
                         room_type=room_type,
                         check_in=check_in,
                         check_out=check_out,
                         total_price=total_price)

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    """Confirm and save the booking."""
    room_type = request.form.get('room_type')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    guest_name = request.form.get('guest_name')
    guest_email = request.form.get('guest_email')
    
    # Validate
    if not all([room_type, check_in, check_out, guest_name, guest_email]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))
    
    if room_type not in ROOMS:
        return redirect(url_for('index'))
    
    # Recheck availability
    if not is_room_available(room_type, check_in, check_out):
        flash('This room is no longer available for those dates.', 'error')
        return redirect(url_for('index'))
    
    # Create booking
    reference_number = get_reference_number()
    total_price = calculate_total_price(room_type, check_in, check_out)
    
    booking = {
        'reference_number': reference_number,
        'room_type': room_type,
        'check_in': check_in,
        'check_out': check_out,
        'guest_name': guest_name,
        'guest_email': guest_email,
        'total_price': total_price,
        'status': 'confirmed',
        'booked_at': datetime.now().isoformat()
    }
    
    bookings = load_bookings()
    bookings.append(booking)
    save_bookings(bookings)
    
    return render_template('confirmation.html', booking=booking)

@app.route('/cancel')
def cancel_page():
    """Page to cancel a booking."""
    return render_template('cancel.html')

@app.route('/process_cancellation', methods=['POST'])
def process_cancellation():
    """Process the cancellation."""
    reference_number = request.form.get('reference_number')
    
    if not reference_number:
        return render_template('cancel.html', error='Please enter a reference number.')
    
    bookings = load_bookings()
    booking = None
    booking_index = None
    
    for i, b in enumerate(bookings):
        if b['reference_number'] == reference_number:
            booking = b
            booking_index = i
            break
    
    if not booking:
        return render_template('cancel.html', error='Booking not found. Please check your reference number.')
    
    if booking['status'] == 'cancelled':
        return render_template('cancel.html', error='This booking is already cancelled.')
    
    # Cancel the booking
    bookings[booking_index]['status'] = 'cancelled'
    save_bookings(bookings)
    
    return render_template('cancellation_confirmation.html', booking=booking)

if __name__ == '__main__':
    app.run(debug=True)
