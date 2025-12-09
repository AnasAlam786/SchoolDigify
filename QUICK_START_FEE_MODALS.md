# Quick Start Guide - Fee Modals Integration

## 5-Step Integration

### Step 1: Import Components
Add these imports at the top of your template:
```html
{% from "/fee/fees_modal.html" import fee_drawer %}
{% from "/fee/fee_transaction_modal_modular.html" import fee_transaction_modal %}
```

### Step 2: Render Components
Add these to your template (usually before the closing content block):
```html
{{ fee_drawer() }}
{{ fee_transaction_modal() }}
```

### Step 3: Create a Button
Add a button to trigger the fee drawer:
```html
<button onclick="openDrawer(studentSessionID, phoneNumber)" class="btn btn-primary">
    <i class="fas fa-money-check"></i> Pay Fees
</button>
```

### Step 4: Get Required Data
Collect the `studentSessionID` from your student list or modal:
```javascript
const studentSessionID = student.student_session_id; // from your data
const phoneNumber = student.phone; // from your data
```

### Step 5: That's It!
The fee payment and transaction management system is now fully functional on your page.

---

## Key Functions

### Open Fee Drawer
```javascript
openDrawer(studentSessionID, phoneNumber);
```

### Open Transaction Modal
(Called automatically when "View Transactions" is clicked in the fee drawer)
```javascript
feeTransactionModalManager.open();
feeTransactionModalManager.loadTransactions(studentSessionID);
```

---

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/get_fee?student_session_id=X&phone=Y` | Fetch student fees |
| POST | `/api/pay_fee` | Process payment |
| GET | `/api/get_fee_transactions?student_session_id=X` | Fetch transactions |
| POST | `/api/delete_fee_transaction` | Delete transaction |
| POST | `/api/restore_fee_transaction` | Restore transaction |

---

## Example: Add to Student List Page

```html
<!-- Add button in student card -->
<button class="btn btn-sm btn-primary" 
    onclick="openDrawer({{ student.student_session_id }}, '{{ student.phone }}')">
    <i class="fas fa-credit-card"></i> Pay Fees
</button>

<!-- Add transaction view button -->
<button class="btn btn-sm btn-info" 
    onclick="feeTransactionModalManager.open(); feeTransactionModalManager.loadTransactions({{ student.student_session_id }})">
    <i class="fas fa-history"></i> View Transactions
</button>
```

---

## Permissions Required in Database

Add these permissions to your `Permissions` table:
- `view_fee_data`
- `pay_fees`

Assign them to your staff roles in `RolePermissions` table.

---

## Styling

Both modals use Tailwind CSS dark theme. They will automatically match your existing SchoolDigify theme.

### Customize Colors:
Edit the CSS in:
- `fees_modal.html` - Fee drawer styles
- `fee_transaction_modal_modular.html` - Transaction modal styles

---

## Common Customizations

### Change button colors
In `fees_modal.html`, find:
```html
<button id="proceedButton" class="w-full bg-blue-600...">
```
Change `bg-blue-600` to any Tailwind color.

### Add more payment modes
In `fees_modal.html`, duplicate a payment mode div and change the `data-mode` attribute.

### Customize transaction display
In `fee_transaction_modal_modular.html`, modify the `createTransactionCardHTML()` method.

---

## Testing Checklist

- [ ] Import both components on your page
- [ ] Button to open fee drawer appears and is clickable
- [ ] Fee drawer opens with student data
- [ ] Can select fees and apply discount
- [ ] Can select payment mode and date
- [ ] "Proceed to Pay" button works
- [ ] Receipt is displayed after payment
- [ ] "View Transactions" button opens transaction modal
- [ ] Transactions load in the modal
- [ ] Can delete and restore transactions
- [ ] All permissions are properly assigned

---

## Need Help?

Refer to `FEE_MODALS_DOCUMENTATION.md` for detailed documentation.
