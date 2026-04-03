# CODE REVIEW - HOTEL RESERVATION APP

## Executive Summary
Overall code quality is **FAIR** with **GOOD** naming conventions but significant issues in DRY principle, security, and error handling. Several critical improvements needed before production.

**Grade: C+ (Needs Improvement)**

---

## 1. NAMING CONVENTIONS ✓ GOOD

### Positive Observations:
- ✓ Function names follow snake_case convention
- ✓ Variable names are descriptive: `check_in_date`, `available_rooms`, `reference_number`
- ✓ Constants in UPPERCASE: `ROOMS`, `BOOKINGS_FILE`
- ✓ Boolean function names are clear: `is_room_available()`, `is_valid_email()`
- ✓ No single-letter variables except loop indices

### Minor Suggestions:
- Consider renaming `book_room()` to `show_booking_form()` for clarity (it shows form, doesn't book)
- `b` in loop (line 198) could be `booking` for consistency with rest of code

**Recommendation:** Rename the loop variable:
```python
# Current (line 198):
for i, b in enumerate(bookings):
    if b['reference_number'] == reference_number:

# Better:
for i, booking in enumerate(bookings):
    if booking['reference_number'] == reference_number:
```

---

## 2. DOCUMENTATION & COMMENTS ⚠ NEEDS IMPROVEMENT

### Positive Observations:
- ✓ All functions have docstrings
- ✓ Module-level docstrings are present
- ✓ Key logic points have comments (line 47: "Check for overlap")

### Issues Found:

**Issue 2.1: Missing complex logic explanation**
- Lines 44-48: Date overlap check is complex but not well explained
- Lines 82-92: Search results calculation includes repeated date parsing

**Issue 2.2: No inline comments for tricky business logic**
- Date overlap condition `if not (check_out_date <= booking_in or check_in_date >= booking_out)` is not intuitive

**Issue 2.3: Missing explanation of design decisions**
- Why check availability twice (line 107 in book_room and line 143 in confirm_booking)?
- Why store bookings.json in current directory vs structured location?

### Improvements:

**Better comments for overlap detection:**
```python
def is_room_available(room_type, check_in, check_out):
    """Check if a room is available for the given dates."""
    bookings = load_bookings()
    check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
    
    for booking in bookings:
        if booking['room_type'] == room_type and booking['status'] == 'confirmed':
            booking_in = datetime.strptime(booking['check_in'], '%Y-%m-%d')
            booking_out = datetime.strptime(booking['check_out'], '%Y-%m-%d')
            
            # Dates don't overlap if: new_checkout <= existing_checkin OR new_checkin >= existing_checkout
            # If neither condition is true, there IS an overlap
            if not (check_out_date <= booking_in or check_in_date >= booking_out):
                return False
    return True
```

---

## 3. DRY PRINCIPLE ✗ MULTIPLE VIOLATIONS

### Issue 3.1: Date Parsing Repeated Throughout Code
**Problem:** `datetime.strptime(date_string, '%Y-%m-%d')` appears **6+ times**

```python
# Line 38-39 (search function)
check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
check_out_date = datetime.strptime(check_out, '%Y-%m-%d')

# Line 40-41 (is_room_available)
booking_in = datetime.strptime(booking['check_in'], '%Y-%m-%d')
booking_out = datetime.strptime(booking['check_out'], '%Y-%m-%d')

# Line 54-55 (calculate_total_price)
check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
check_out_date = datetime.strptime(check_out, '%Y-%m-%d')

# Similar in book_room, confirm_booking, etc.
```

**Severity:** HIGH - Violates DRY principle and makes changes error-prone

**Solution: Create helper function**
```python
# Add this near the top after imports
DATE_FORMAT = '%Y-%m-%d'

def parse_date(date_string):
    """Parse date string in standard format."""
    return datetime.strptime(date_string, DATE_FORMAT)

# Usage:
check_in_date = parse_date(check_in)
check_out_date = parse_date(check_out)
```

---

### Issue 3.2: Date Validation Logic Repetition
**Problem:** Date validation happens in multiple places:

```python
# search() function validation
if check_in_date >= check_out_date:
    flash('Check-out date must be after check-in date.', 'error')
    return redirect(url_for('index'))

# Should be extracted to helper function
def validate_dates(check_in, check_out):
    """Validate date range. Returns (is_valid, error_message)"""
    try:
        check_in_date = parse_date(check_in)
        check_out_date = parse_date(check_out)
        
        if check_in_date >= check_out_date:
            return False, 'Check-out date must be after check-in date.'
        
        if check_in_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return False, 'Check-in date cannot be in the past.'
        
        return True, None
    except ValueError:
        return False, 'Invalid date format.'
```

---

### Issue 3.3: Availability Checking
**Current:** Checked independently in `book_room()` and again in `confirm_booking()`

**Better approach:** Create a wrapper function
```python
def validate_room_selection(room_type, check_in, check_out):
    """Validate room selection and return error message or None"""
    if room_type not in ROOMS:
        return 'Invalid room type'
    
    if not is_room_available(room_type, check_in, check_out):
        return 'This room is no longer available for those dates.'
    
    return None
```

**Usage in both functions:**
```python
error = validate_room_selection(room_type, check_in, check_out)
if error:
    flash(error, 'error')
    return redirect(url_for('index'))
```

---

## 4. SECURITY ISSUES ⚠ CRITICAL FINDINGS

### Issue 4.1: No Email Validation
**Severity:** MEDIUM  
**Location:** `confirm_booking()` function

**Problem:**
```python
guest_email = request.form.get('guest_email')
# No validation - could be "notanemail" or empty string in JSON
```

**Fix:**
```python
import re

def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# In confirm_booking():
if not is_valid_email(guest_email):
    flash('Invalid email address.', 'error')
    return redirect(url_for('index'))
```

---

### Issue 4.2: No Input Sanitization
**Severity:** MEDIUM  
**Problem:** `guest_name` not validated/sanitized

```python
guest_name = request.form.get('guest_name')
# Could contain: "<script>alert('xss')</script>", SQL injection chars, etc.
```

**Risk:** If this data is displayed in future features without escaping, XSS vulnerability

**Fix:**
```python
from markupsafe import escape
import re

def is_valid_guest_name(name):
    """Validate guest name."""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > 100:  # Reasonable limit
        return False
    # Allow only letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s'-]{1,100}$", name):
        return False
    return True

# In confirm_booking():
if not is_valid_guest_name(guest_name):
    flash('Invalid guest name.', 'error')
    return redirect(url_for('index'))

# Store sanitized version
guest_name = escape(guest_name.strip())
```

---

### Issue 4.3: Hardcoded Secret Key
**Severity:** HIGH  
**Location:** Line 8

```python
app.secret_key = 'hotel-reservation-secret-key'  # ← EXPOSED IN SOURCE CODE
```

**Problem:** Secret key is hardcoded in repository. Anyone with access can forge sessions.

**Fix:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
```

**or for development:**
```python
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-only-for-testing')
```

Create `.env` file:
```
SECRET_KEY=your-production-secret-key-here
```

---

### Issue 4.4: File Permissions / Data Privacy
**Severity:** MEDIUM  
**Problem:** `bookings.json` location and permissions not controlled

```python
BOOKINGS_FILE = 'bookings.json'  # Stored in current directory, world-readable
```

**Risks:**
- Could be accessed by other processes
- No version control/audit trail
- Not backed up

**Fix:**
```python
import os
from pathlib import Path

# Create data directory if it doesn't exist
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
BOOKINGS_FILE = DATA_DIR / 'bookings.json'

# Ensure file permissions (Unix-like systems)
os.chmod(BOOKINGS_FILE, 0o600) if BOOKINGS_FILE.exists() else None
```

---

### Issue 4.5: Reference Number Case Sensitivity
**Severity:** MEDIUM (already reported by TESTER)

```python
# Line 198: Case-sensitive comparison
if b['reference_number'] == reference_number:
```

**Should be:**
```python
if b['reference_number'].upper() == reference_number.upper():
```

---

### Issue 4.6: Error Messages Leak Information
**Severity:** LOW  
**Problem:** Error messages reveal system state

```python
# Line 90: Exposes that validation happens in search
flash('Check-out date cannot be in the past.')

# Line 189: Reveals booking structure
flash('This booking is already cancelled.')
```

**Better approach:** Generic messages in production
```python
# More generic for users
flash('Unable to process your request. Please try again.', 'error')

# But log detailed errors for debugging
import logging
logger = logging.getLogger(__name__)
logger.error(f"Validation failed for dates: {check_in}, {check_out}")
```

---

## 5. CODE QUALITY ISSUES ✗ SEVERAL PROBLEMS

### Issue 5.1: No Error Handling for File I/O
**Severity:** MEDIUM

```python
def load_bookings():
    """Load bookings from JSON file."""
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as f:
            return json.load(f)
    return []
```

**Problems:**
- `json.load()` could fail if file is corrupted
- `open()` could raise permission errors
- No logging

**Better:**
```python
def load_bookings():
    """Load bookings from JSON file."""
    try:
        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load bookings: {e}")
        # Return empty list and let app continue
    return []
```

---

### Issue 5.2: No Input Validation in Helper Functions
**Severity:** MEDIUM

```python
def calculate_total_price(room_type, check_in, check_out):
    """Calculate total price for a booking."""
    # What if room_type not in ROOMS?
    # What if dates are invalid?
    nights = (check_out_date - check_in_date).days
    return ROOMS[room_type] * nights  # ← Could raise KeyError
```

**Better:**
```python
def calculate_total_price(room_type, check_in, check_out):
    """Calculate total price for a booking.
    
    Args:
        room_type: Must be in ROOMS
        check_in: Date string YYYY-MM-DD
        check_out: Date string YYYY-MM-DD
        
    Returns:
        int: Total price or 0 if invalid
    """
    if room_type not in ROOMS:
        logger.warning(f"Invalid room type: {room_type}")
        return 0
    
    try:
        check_in_date = parse_date(check_in)
        check_out_date = parse_date(check_out)
        nights = max(0, (check_out_date - check_in_date).days)
        return ROOMS[room_type] * nights
    except (ValueError, AttributeError) as e:
        logger.error(f"Price calculation failed: {e}")
        return 0
```

---

### Issue 5.3: Missing Logging
**Severity:** MEDIUM  
**Problem:** No logging for debugging/auditing

```python
# No logs for:
# - Booking creation
# - Cancellations  
# - Errors
# - Validation failures
```

**Add:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Then add throughout:
logger.info(f"Booking created: {reference_number} for {guest_name}")
logger.warning(f"Booking cancellation failed: {reference_number} not found")
logger.error(f"File I/O error: {str(e)}")
```

---

### Issue 5.4: Magic Strings/Numbers
**Severity:** LOW

```python
# Magic strings scattered throughout:
'%Y-%m-%d'                              # Line 38, 40, 54, etc.
'hotel-reservation-secret-key'          # Line 8
'confirmed'                             # Line 43, 140, 159
'cancelled'                             # Line 186, 193
'error'                                 # Multiple locations
```

**Better:**
```python
# Define constants at top
DATE_FORMAT = '%Y-%m-%d'
BOOKING_STATUS_CONFIRMED = 'confirmed'
BOOKING_STATUS_CANCELLED = 'cancelled'
FLASH_CATEGORY_ERROR = 'error'
FLASH_CATEGORY_SUCCESS = 'success'

# Usage:
check_in_date = datetime.strptime(check_in, DATE_FORMAT)
if booking['status'] == BOOKING_STATUS_CANCELLED:
    flash('This booking is already cancelled.', FLASH_CATEGORY_ERROR)
```

---

## 6. PERFORMANCE ISSUES ⚠ MINOR

### Issue 6.1: Inefficient Booking Lookup
**Severity:** LOW (OK for current scale)

```python
# process_cancellation() - O(n) lookup
for i, booking in enumerate(bookings):
    if booking['reference_number'] == reference_number:
        # Found it
```

**At scale:** With 10,000+ bookings, this is slow

**Better for future:**
```python
# Could use database eventually
# For now, acceptable for small apps
```

---

### Issue 6.2: Recalculating Availability
**Severity:** LOW

```python
# Check in book_room() (line 107)
if not is_room_available(room_type, check_in, check_out):

# Then check again in confirm_booking() (line 143)  
if not is_room_available(room_type, check_in, check_out):
```

**Reasoning:** Good for race condition safety (double-check)
**Comment:** Add explanation:
```python
# Recheck availability - another user may have booked this room
if not is_room_available(room_type, check_in, check_out):
```

---

## 7. TESTING & MAINTAINABILITY ✗ LACKING

### Issue 7.1: No Unit Tests
**Severity:** MEDIUM  
- No tests for `is_room_available()`
- No tests for `calculate_total_price()`
- No tests for date validation

**Recommendation:** Add `tests/test_app.py`

### Issue 7.2: Configuration Not Externalized
**Severity:** LOW  
- Room prices hardcoded in dictionary
- Other settings mixed with code

**Better:**
```python
# config.py
ROOM_TYPES = {
    'Standard': 100,
    'Deluxe': 150,
    'Suite': 250
}

# Or load from JSON:
CONFIG = json.load(open('config/rooms.json'))
```

---

## 8. RECOMMENDATIONS SUMMARY

| Priority | Issue | Fix Time |
|----------|-------|----------|
| **CRITICAL** | Fix the `check = ` bug (TESTER #1) | 5 min |
| **HIGH** | Add email validation | 15 min |
| **HIGH** | Remove hardcoded secret key | 10 min |
| **HIGH** | Extract date parsing helper | 20 min |
| **MEDIUM** | Add input sanitization | 20 min |
| **MEDIUM** | Add error handling for file I/O | 15 min |
| **MEDIUM** | Add logging throughout | 30 min |
| **MEDIUM** | Fix reference number case sensitivity | 5 min |
| **LOW** | Extract magic strings to constants | 15 min |
| **LOW** | Add comprehensive docstring examples | 20 min |

---

## 9. REFACTORED CODE EXAMPLE

Here's what a cleaned-up version would look like:

```python
# app.py - IMPROVED VERSION
import json
import uuid
import logging
import re
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import escape

# Configuration
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-only-change-in-production')

# Constants
DATE_FORMAT = '%Y-%m-%d'
BOOKING_STATUS_CONFIRMED = 'confirmed'
BOOKING_STATUS_CANCELLED = 'cancelled'
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
BOOKINGS_FILE = DATA_DIR / 'bookings.json'

ROOM_TYPES = {
    'Standard': 100,
    'Deluxe': 150,
    'Suite': 250
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper Functions
def parse_date(date_string):
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_string, DATE_FORMAT)

def is_valid_email(email):
    """Check if email format is valid."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_guest_name(name):
    """Check if guest name is valid."""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > 100:
        return False
    return re.match(r"^[a-zA-Z\s'-]{1,100}$", name) is not None

def validate_dates(check_in_str, check_out_str):
    """Validate date range.
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        check_in = parse_date(check_in_str)
        check_out = parse_date(check_out_str)
        
        if check_in >= check_out:
            return False, 'Check-out date must be after check-in date.'
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if check_in < today:
            return False, 'Check-in date cannot be in the past.'
        
        return True, None
    except ValueError:
        return False, 'Invalid date format.'

# ... rest of the functions with improvements ...
```

---

## Overall Assessment

**Strengths:**
- ✓ Good naming conventions
- ✓ Clear function structure
- ✓ Proper MVC separation
- ✓ Responsive design

**Weaknesses:**
- ✗ DRY principle violations (repeated date parsing)
- ✗ Missing security validations
- ✗ No logging or error handling
- ✗ Hardcoded configuration
- ✗ Code bug (check vs check_in)

**Grade: C+ → B with proposed improvements**

---

**Reviewed by:** REVIEWER Agent  
**Date:** 2026-04-03  
**Recommendation:** Implement HIGH priority items before code review approval
