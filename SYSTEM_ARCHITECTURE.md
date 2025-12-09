# System Architecture - Fee Management Modular System

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Any Page (e.g., student_list.html)       │
│  {% import fee_drawer %}  {% import fee_transaction_modal %}    │
└────────────────────────┬──────────────────────────────────────┬─┘
                         │                                      │
                    ┌────▼─────┐                         ┌──────▼─────┐
                    │           │                         │            │
                    │ Fee Drawer│                         │ Transaction│
                    │  Modal    │                         │   Modal    │
                    │           │                         │            │
                    └────┬──────┘                         └──────┬─────┘
                         │                                      │
          ┌──────────────┴──────────────┐         ┌────────────┴─────────────┐
          │                             │         │                          │
      Button: Pay   Button: View Trans  │         │  User Actions            │
                         │              │         │  - View Transactions     │
                         └──────┬───────┘         │  - Delete Transaction    │
                                │                 │  - Restore Transaction   │
                                │                 └───────────────────────────┘
                    ┌───────────▼──────────────┐
                    │   JavaScript APIs        │
                    │  - openDrawer()          │
                    │  - init()                │
                    │  - openTransactionModal()│
                    └───────────┬──────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  Backend API     │  │  Backend API    │  │  Backend API     │
│  get_fee_api     │  │  pay_fee_api    │  │  get_transactions│
│  /api/get_fee    │  │  /api/pay_fee   │  │  /api/...        │
└────────┬─────────┘  └────────┬────────┘  └────────┬─────────┘
         │                    │                    │
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌─────────▼────────┐
                    │   Database       │
                    │  - FeeData       │
                    │  - FeeTransaction│
                    │  - Students      │
                    └──────────────────┘
```

---

## File Dependency Graph

```
student_list.html
├─ imports: fees_modal.html
│           └─ requires: watsappMessage.js
│           └─ requires: FeeTransaction model
│           └─ requires: FeeSessionData model
│
├─ imports: fee_transaction_modal_modular.html
│           └─ standalone (no external JS files)
│
├─ calls: openDrawer(studentSessionID, phoneNumber)
│         └─ internally calls: init(students, studentSessionId)
│           └─ internally calls: setupEventListeners()
│             └─ handles View Transactions click
│               └─ calls: feeTransactionModalManager.open()
│                 └─ calls: feeTransactionModalManager.loadTransactions()
│
└─ renders:
   ├─ fee_drawer container
   └─ fee_transaction_modal container
```

---

## API Flow Diagram

```
┌─────────────────────────────┐
│   User Action               │
│   Click "Pay Fees" Button   │
└────────────┬────────────────┘
             │
             ▼
    ┌────────────────────────┐
    │  openDrawer(ssID, ph)  │
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────────────────────┐
    │  GET /api/get_fee                      │
    │  Parameters:                           │
    │  - student_session_id: ssID            │
    │  - phone: phoneNumber                  │
    └────────────┬─────────────────────────┬─┘
                 │                         │
             ✅  │                         │ ❌ Error
                 ▼                         ▼
    ┌─────────────────────────┐  ┌─────────────────┐
    │  init(data, ssID)       │  │ showAlert(error)│
    │  Render student info    │  │ closeDrawer()   │
    │  Render fees            │  └─────────────────┘
    │ Store studentSessionId  │
    └────────────┬────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ User Selects Fees          │
    │ User Selects Payment Mode  │
    │ User Enters Discount       │
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Click "Proceed to Pay"│
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────────────────────┐
    │  POST /api/pay_fee                     │
    │  Body:                                 │
    │  - students: selectedFees[]            │
    │  - discount: amount                    │
    │  - payment_mode: mode                  │
    │  - paymentDate: date                   │
    └────────────┬──────────────────────────┬─┘
                 │                          │
             ✅  │                          │ ❌ Error
                 ▼                          ▼
    ┌──────────────────────────┐ ┌────────────────┐
    │ generateReceipt()        │ │ showAlert()    │
    │ showReceipt()            │ │ Highlight form │
    │ Close drawer             │ │ Errors         │
    │ Show print/WhatsApp btns │ └────────────────┘
    └─────────────────────────┘


┌────────────────────────────────────┐
│  User Action (In Fee Drawer)       │
│  Click "View Transactions" Button  │
└────────────┬───────────────────────┘
             │
             ▼
    ┌────────────────────────────────────┐
    │  openTransactionModal()            │
    │  - feeTransactionModalManager      │
    │  .open()                           │
    │  .loadTransactions(studentSessionId)
    └────────────┬─────────────────────┬─┘
                 │                     │
                 ▼                     ▼
    ┌──────────────────────┐  ┌─────────────────┐
    │ Render Loading State │  │ Show Skeleton   │
    │ (after 300ms)        │  │ Loader          │
    └──────────────────────┘  └─────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │  GET /api/get_fee_transactions      │
    │  Parameters:                         │
    │  - student_session_id: ssID          │
    └────────────┬──────────────────────┬──┘
                 │                      │
             ✅  │                      │ ❌ Error
                 ▼                      ▼
    ┌──────────────────────┐  ┌──────────────┐
    │ render()             │  │ showStatus() │
    │ Show transactions    │  │ Error msg    │
    │ Setup event          │  └──────────────┘
    │ listeners            │
    └──────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │  User Action                 │
    │  Expand transaction / Delete │
    │  or Restore                  │
    └────────────┬─────────────────┘
                 │
          ┌──────┴──────┐
          │             │
          ▼             ▼
    ┌──────────┐  ┌─────────────────────────┐
    │ Expand   │  │ Delete/Restore Action   │
    │ Show     │  └────────────┬─────────────┘
    │ Details  │               │
    └──────────┘               ▼
                   ┌─────────────────────────────┐
                   │ POST /api/delete_fee_txn    │
                   │ or restore_fee_txn          │
                   │ Body:                       │
                   │ - transaction_id: id        │
                   └────────────┬────────────────┬─┘
                                │                │
                            ✅  │                │ ❌
                                ▼                ▼
                   ┌──────────────────────┐ ┌────────────┐
                   │ state.softDelete()   │ │ showStatus │
                   │ or state.restore()   │ │ Error msg  │
                   │ render()             │ └────────────┘
                   │ showStatus(success)  │
                   └──────────────────────┘
```

---

## Data Flow

### Fee Payment Flow
```
Student Data {
  id: number
  name: string
  class: string
  rollNo: number
  monthlyFees: [
    {
      id: string
      amount: number
      status: 'paid' | 'due' | 'upcoming'
      dueDate: string
      period_name: string
    }
  ]
  otherFees: [
    {
      id: string
      name: string
      amount: number
      status: 'paid' | 'due' | 'upcoming'
      dueDate: string
    }
  ]
  selectedFees: []  // Updated by user selection
}

Payment Request {
  students: [StudentData]
  discount: number
  payment_mode: 'cash' | 'upi' | 'card' | 'netbanking'
  paymentDate: string (DD/MM/YYYY)
}

Payment Response {
  message: string
  transaction_no: string
  whatsapp_message: string
  phone_number: string
}
```

### Transaction Data Flow
```
Transaction {
  id: number
  transaction_no: string
  paid_amount: number
  payment_date: string (ISO)
  payment_mode: string
  discount: number
  remark: string | null
  created_at: string (ISO)
  fees: [
    {
      id: number
      name: string
      amount: number
      status: string
    }
  ]
  is_deleted: boolean
}

API Response {
  message: string
  transactions: Transaction[]
}
```

---

## State Management

### Fee Drawer State
```javascript
{
  students: StudentData[]           // Array of students
  currentStudent: number            // Index of active student
  discount: number                  // Applied discount amount
  paymentMode: string               // Selected payment mode
  paymentDate: string               // Selected payment date
  currentStudentSessionId: string   // For transaction modal
}
```

### Transaction Modal State
```javascript
{
  transactions: Transaction[]       // All transactions
  expandedCards: Set<number>        // IDs of expanded cards
  activePopover: string | null      // Active popover ID
  deletedSectionExpanded: boolean   // Show deleted section?
  isLoading: boolean                // Loading state
  studentSessionId: string          // Current student session ID
}
```

---

## Module Dependencies

```
fee_drawer() macro
├─ Requires: watsappMessage.js
├─ Database: FeeTransaction model
├─ Database: FeeSessionData model
├─ Permissions: 'view_fee_data'
├─ Permissions: 'pay_fees'
└─ APIs:
   ├─ GET /api/get_fee
   └─ POST /api/pay_fee

fee_transaction_modal() macro
├─ No external JS dependencies
├─ Database: FeeTransaction model
├─ Database: FeeData model
├─ Database: FeeSessionData model
├─ Permissions: 'view_fee_data'
├─ Permissions: 'pay_fees'
└─ APIs:
   ├─ GET /api/get_fee_transactions
   ├─ POST /api/delete_fee_transaction
   └─ POST /api/restore_fee_transaction
```

---

## Error Handling Flow

```
┌─────────────────────────────┐
│  Error Occurs               │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  API Returns Error Status   │
│  - 400: Bad Request         │
│  - 401: Unauthorized        │
│  - 403: Forbidden           │
│  - 404: Not Found           │
│  - 500: Server Error        │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  JS Exception Handler       │
│  try-catch block            │
│  or fetch .catch()          │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  showStatus() or showAlert()│
│  Display user-friendly msg  │
│  Log to console for dev     │
└─────────────────────────────┘
```

---

## Integration Points

```
Any HTML Page
      │
      ├─ Import fee_drawer()
      │  └─ Can call openDrawer(ssID, phone)
      │
      ├─ Import fee_transaction_modal()
      │  └─ Can call feeTransactionModalManager API
      │
      └─ Both modals are completely independent
         yet can interact through:
         - Shared database
         - Shared APIs
         - Global state (when needed)
```

---

## Security Flow

```
┌─────────────────────────────┐
│  User Action                │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Check Session              │
│  (login_required decorator) │
└────────────┬────────────────┘
             │
        ┌────┴────┐
        │          │
    ✅  │          │ ❌ Session Invalid
        │          ├─ Redirect to login
        ▼          │
┌─────────────────┐│
│ Check Permissions
│ (permission_     │
│  required)       │
└────────┬─────────┘
         │
    ┌────┴──────┐
    │           │
✅  │           │ ❌ No Permission
    │           ├─ Return 403 Error
    ▼           │
Process Request │
                │
             └──┘
```

---

**Last Updated:** December 7, 2025
**Status:** Complete and Ready for Production
