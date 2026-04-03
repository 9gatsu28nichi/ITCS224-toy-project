# TESTER REPORT - HOTEL RESERVATION APP

## CRITICAL ISSUES FOUND

### 🚨 ISSUE #1: NameError in search() function (CRITICAL - BLOCKS CORE FEATURE)
**Location:** `app.py`, line 68-71  
**Severity:** CRITICAL - Makes search feature completely broken  
**Description:**
```python
# WRONG - Line 68:
check = request.form.get('check_in')  # ← Assigns to 'check' instead of 'check_in'
check_out = request.form.get('check_out')

# Then line 71 uses:
check_in_date = datetime.strptime(check_in, '%Y-%m-%d')  # ← 'check_in' never defined!
```

**Error Output:**
```
NameError: name 'check_in' is not defined. Did you mean: 'check_out'?
```

**Impact:** Every search request results in HTTP 500 error. Core feature is completely broken.

**Fix:** Change line 68 from `check = ` to `check_in = `

---

### ⚠️ ISSUE #2: No server-side email validation
**Location:** `app.py`, confirm_booking() function  
**Severity:** MEDIUM - Security issue  
**Description:** App accepts any value as email. Tests show invalid emails like "notanemail" are accepted.

**Test Case:**
```
POST /confirm_booking
guest_email: "notanemail"
Result: Booking created with invalid email
```

**Impact:** Bookings can be created with invalid emails, making confirmation/communication impossible.

**Recommendation:** Add server-side email validation using regex:
```python
import re
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

---

### ⚠️ ISSUE #3: Reference number case sensitivity in cancellation
**Location:** `app.py`, process_cancellation() function, line 183  
**Severity:** MEDIUM - User experience issue  
**Description:** Reference numbers are generated in uppercase but cancellation performs case-sensitive comparison.

**Scenario:**
- Generated reference: `ABC12345` (uppercase)
- User enters: `abc12345` (lowercase)
- Result: "Booking not found" error

**Fix:** Convert both sides to uppercase for comparison:
```python
if b['reference_number'].upper() == reference_number.upper():
```

---

## TEST RESULTS SUMMARY

| Test # | Description | Status | Notes |
|--------|-------------|--------|-------|
| 1 | Home page loads | ✓ PASS | |
| 2 | Search with valid dates | ✗ FAIL | HTTP 500 - NameError in line 71 |
| 3 | Search same check-in/out | ✗ FAIL | HTTP 500 - NameError in line 71 |
| 4 | Search with past date | ✗ FAIL | HTTP 500 - NameError in line 71 |
| 5 | Book Standard room | ✗ FAIL | Cannot proceed due to Issue #1 |
| 6 | Confirm booking valid | ✗ FAIL | HTTP 500 from search |
| 7 | Confirm without guest name | ✓ PASS | Correctly rejected |
| 8 | Confirm invalid email | ⚠ WARNING | Accepts invalid email format |
| 9 | Book invalid room type | ✓ PASS | Correctly rejected |
| 10 | Cancel page loads | ✓ PASS | |
| 11 | Cancel invalid reference | ✓ PASS | Correctly rejected |

---

## ADDITIONAL OBSERVATIONS

### Positive Findings:
- ✓ Home page renders correctly
- ✓ Form validation for missing fields works
- ✓ Invalid room type is properly rejected
- ✓ Reference number uniqueness is maintained
- ✓ Cancel page loads properly
- ✓ Mobile-responsive design is in place
- ✓ Blue accent color matches spec

### Minor Issues:
- Flash messages work for some errors but not all (search validation)
- No confirmation dialog for cancellations
- No email confirmation/verification system (spec doesn't require but recommended)

---

## TESTING METHODOLOGY

Tests performed:
1. Manual API calls using `curl` and `requests` library
2. Date validation scenarios (past dates, same-day, future dates)
3. Form field validation (empty fields, invalid types)
4. Booking creation and confirmation flow
5. Cancellation workflow
6. Reference number handling

---

## RECOMMENDATION

**BLOCKER:** Fix Issue #1 immediately - it blocks the entire search feature.  
**HIGH:** Fix Issues #2 and #3 before production deployment.

---

Generated: 2026-04-03  
Tester: TESTER Agent
