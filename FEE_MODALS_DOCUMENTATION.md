# Fee Management Modular Components - Integration Guide

## Overview
This document describes the modular fee payment and transaction management system built for SchoolDigify. The system is fully modular and can be used on any page in your application.

## Components

### 1. **Fee Payment Modal** (`fees_modal.html`)
A modular Jinja2 macro that provides a complete fee payment interface.

**Location:** `src/view/templates/fee/fees_modal.html`

**Features:**
- Select multiple students (siblings)
- View monthly and other fees
- Multi-student payment selection
- Apply discounts
- Choose payment method (Cash, UPI, Card, Net Banking)
- Generate and download receipts
- Send WhatsApp notifications
- View transaction history (integrated)

### 2. **Fee Transaction Modal** (`fee_transaction_modal_modular.html`)
A modular Jinja2 macro for viewing, managing, and deleting fee transactions.

**Location:** `src/view/templates/fee/fee_transaction_modal_modular.html`

**Features:**
- View all fee transactions for a student
- Expand/collapse transaction details
- Delete transactions (soft delete)
- Restore deleted transactions
- Filter active vs deleted transactions
- Real-time loading states

---

## How to Use

### Import on Any Page

```html
{% from "/fee/fees_modal.html" import fee_drawer %}
{% from "/fee/fee_transaction_modal_modular.html" import fee_transaction_modal %}

<!-- Render the modular components -->
{{ fee_drawer() }}
{{ fee_transaction_modal() }}
```

### Open Fee Payment Drawer

Call this JavaScript function with the student's session ID and phone number:

```javascript
openDrawer(studentSessionID, phoneNumber);
```

**Parameters:**
- `studentSessionID` (string): The unique ID of the student session
- `phoneNumber` (string): Student's phone number (optional, used for WhatsApp)

**Example:**
```javascript
openDrawer(123, "9876543210");
```

---

## Backend APIs

### 1. Get Fee Data
**Endpoint:** `GET /api/get_fee`

**Parameters:**
- `student_session_id` (required): Student session ID
- `phone` (optional): Phone number for WhatsApp

**Response:**
```json
{
  "student_id": 1,
  "name": "John Doe",
  "class": "10-A",
  "rollNo": 25,
  "monthlyFees": [...],
  "otherFees": [...]
}
```

---

### 2. Process Payment
**Endpoint:** `POST /api/pay_fee`

**Request Body:**
```json
{
  "students": [
    {
      "student_id": 1,
      "selectedFees": [
        {
          "id": "fee_1",
          "amount": 2500
        }
      ]
    }
  ],
  "discount": 500,
  "payment_mode": "cash",
  "paymentDate": "15/12/2025"
}
```

**Response:**
```json
{
  "message": "Payment successful",
  "transaction_no": "TXN001",
  "whatsapp_message": "Fees Paid Successfully!",
  "phone_number": "9876543210"
}
```

---

### 3. Get Fee Transactions
**Endpoint:** `GET /api/get_fee_transactions`

**Parameters:**
- `student_session_id` (required): Student session ID

**Response:**
```json
{
  "message": "Transactions retrieved successfully",
  "transactions": [
    {
      "id": 1,
      "transaction_no": "TXN001",
      "paid_amount": 5000,
      "payment_date": "2025-12-15",
      "payment_mode": "cash",
      "discount": 0,
      "fees": [
        {
          "id": 1,
          "name": "Monthly Fee",
          "amount": 2500,
          "status": "paid"
        }
      ],
      "is_deleted": false
    }
  ]
}
```

---

### 4. Delete Fee Transaction
**Endpoint:** `POST /api/delete_fee_transaction`

**Request Body:**
```json
{
  "transaction_id": 1
}
```

**Response:**
```json
{
  "message": "Transaction deleted successfully",
  "transaction_id": 1
}
```

---

### 5. Restore Fee Transaction
**Endpoint:** `POST /api/restore_fee_transaction`

**Request Body:**
```json
{
  "transaction_id": 1
}
```

**Response:**
```json
{
  "message": "Transaction restored successfully",
  "transaction_id": 1
}
```

---

## JavaScript API

### Fee Drawer Functions

**`openDrawer(studentSessionID, phoneNumber)`**
Opens the fee payment drawer and loads student fee data.

**`closeDrawer()`**
Closes the fee payment drawer.

**`init(studentsData, studentSessionId)`**
Initializes the fee drawer with student data (called automatically by `openDrawer`).

---

### Fee Transaction Modal Functions

**`feeTransactionModalManager.open()`**
Opens the transaction modal.

**`feeTransactionModalManager.close()`**
Closes the transaction modal.

**`feeTransactionModalManager.loadTransactions(studentSessionId)`**
Loads transactions for a specific student session.

**`feeTransactionModalManager.deleteTransaction(txnId)`**
Marks a transaction as deleted.

**`feeTransactionModalManager.restoreTransaction(txnId)`**
Restores a deleted transaction.

---

## Integration Example

Here's a complete example of how to add the fee modals to a new page:

```html
{% extends "base.html" %}
{% block title %}My Page{% endblock %}
{% block content %}

<!-- Import the modular components -->
{% from "/fee/fees_modal.html" import fee_drawer %}
{% from "/fee/fee_transaction_modal_modular.html" import fee_transaction_modal %}

<!-- Render them -->
{{ fee_drawer() }}
{{ fee_transaction_modal() }}

<!-- Your page content -->
<div class="container">
  <h1>My Page</h1>
  
  <!-- Add a button that opens the fee drawer -->
  <button onclick="openDrawer(123, '9876543210')" class="btn btn-primary">
    Pay Fees
  </button>
</div>

{% endblock %}
```

---

## Workflow

### Fee Payment Workflow
1. User clicks "Pay Fees" button
2. `openDrawer(studentSessionID, phoneNumber)` is called
3. Fee payment drawer opens with loading skeleton
4. Student fee data is fetched from backend
5. User selects fees, discount, payment mode, and date
6. User clicks "Proceed to Pay" button
7. Payment is processed via backend API
8. Receipt is generated and displayed
9. User can print or send via WhatsApp

### View Transactions Workflow
1. Fee drawer is open
2. User clicks "View Transactions" button
3. Transaction modal opens
4. Transactions are loaded for the student
5. User can expand transaction details
6. User can delete or restore transactions
7. Changes are reflected in real-time

---

## Permissions Required

The following permissions must be assigned to user roles for fee operations:

- `view_fee_data`: View fee information
- `pay_fees`: Process fee payments and manage transactions

---

## Customization

### Modify Colors
Edit the CSS in the component files:
- Fee drawer: `#feeDrawer` and related styles
- Transaction modal: `.fee-modal-overlay` and related styles

### Add Custom Fees
Modify the `createFeeCard()` function in `fees_modal.html` to add custom fee display logic.

### Extend Transaction Actions
Edit the transaction card HTML in `fee_transaction_modal_modular.html` to add more action buttons.

---

## Troubleshooting

### Issue: "Fee transaction modal manager not initialized"
**Solution:** Ensure `fee_transaction_modal_modular.html` is imported before `fees_modal.html`:
```html
{{ fee_transaction_modal() }}
{{ fee_drawer() }}
```

### Issue: Transaction modal doesn't load data
**Solution:** 
1. Check browser console for errors
2. Verify `student_session_id` is valid
3. Check backend logs for API errors

### Issue: Discount not working
**Solution:** Ensure discount value is numeric and not negative.

---

## File Structure

```
src/
├── view/
│   └── templates/
│       ├── fee/
│       │   ├── fees_modal.html (Main fee payment modal)
│       │   ├── fee_transaction_modal_modular.html (Transaction modal)
│       │   └── fee_transaction_modal.html (Old non-modular version)
│       └── student_list.html (Example usage)
└── controller/
    └── fees/
        ├── get_fee_api.py (Fetch fee data)
        ├── pay_fee_api.py (Process payments)
        ├── get_transactions_api.py (Fetch transactions)
        └── transaction_action_api.py (Delete/restore transactions)
```

---

## Future Enhancements

1. **Soft Delete with Timestamp:** Track when transactions were deleted
2. **Transaction Refunds:** Issue partial/full refunds
3. **Bulk Operations:** Delete/restore multiple transactions at once
4. **Transaction Filters:** Filter by date range, amount, payment mode
5. **Export Transactions:** Download transaction reports as PDF/Excel
6. **Email Receipts:** Send receipts via email
7. **SMS Notifications:** Send payment confirmations via SMS

---

## Support

For issues or questions, contact the development team or refer to the backend API documentation.
