# TODO: Implement Roll Number Restrictions and Auto-Fill for Promote Student Modal

## Current Status
- Modal opens when Update or Promote button is clicked
- Class selection dropdown exists
- Roll number input is currently free-form text input

## Required Changes

### Frontend Changes (promote_student.html)
- [ ] Modify roll number input to show available options (gapped rolls + max+1)
- [ ] Add display area below roll input to show gapped roll numbers
- [ ] Implement auto-fill logic when class is selected
- [ ] Restrict user input to only valid roll numbers
- [ ] Update JavaScript functions to fetch and display roll options

### Backend Changes
- [ ] Ensure promote_student_api.py returns gapped rolls data
- [ ] Ensure update_promotion_api.py returns gapped rolls data
- [ ] Verify get_gapped_rolls utility is working correctly

### API Modifications
- [ ] Add endpoint to get available rolls for a class
- [ ] Update existing promotion data APIs to include roll information

### Testing
- [ ] Test class selection auto-fill functionality
- [ ] Test roll number validation on submit
- [ ] Test both promote and update scenarios
- [ ] Verify error handling for invalid roll selections
