
from datetime import datetime

def fee_demand_message(data):
    student = data[0]

    today = datetime.now().strftime("%d %B %Y")

    name = student["name"]
    class_name = student["class"]
    roll = student["rollNo"]
    phone = student["phone"]

    total_due = student["total_due_amount"]
    total_terms = student["total_due_terms"]

    due_months = [
        f["period_name"]
        for f in student["monthlyFees"]
        if f["status"] == "due"
    ]

    other_due_fees = [
        f for f in student["otherFees"] if f["status"] == "due"
    ]

    message = f"""
📌 *Fee Due Notice*

📅 *Date:* {today}

Dear Parent/Guardian,

This is to inform you regarding the *pending school fee* for your ward:

👦 *Student Name:* {name}
🏫 *Class:* {class_name}
🎓 *Roll No:* {roll}
📞 *Registered Mobile:* {phone}

────────────────────

💰 *Fee Summary (Academic Session 2025–26)*

🔴 *Total Due Amount:* ₹{total_due:.0f}/-
📆 *Total Pending Months / Terms:* {total_terms}

────────────────────

📚 *Monthly Tuition Fee (₹300 per month) – Due*
"""

    for month in due_months:
        message += f"• {month}\n"

    message += "\n🧾 *Other Due Fees*\n"

    for fee in other_due_fees:
        message += (
            f"• {fee['fee_type']} – {fee['period_name']}: "
            f"₹{fee['amount']:.0f} (Due Date: {fee['dueDate']})\n"
        )

    message += """
────────────────────

⚠️ *Important Note:*
Kindly clear the pending dues at the earliest to avoid inconvenience related to examinations, results, or other academic activities.

For any clarification, please contact the school office.

🙏 Thank you for your cooperation.

Warm regards,  
🏫 *School Administration*  
*SchoolDigify*
"""

    return message.strip()

def transaction_whatsapp_message(data):
    message = "✅ *फीस भुगतान की पुष्टि*\n\n"
    message += f"📅 भुगतान की तारीख: {data['payment_date']}\n"
    message += f"💳 भुगतान का तरीका: {data['payment_mode'].title()}\n"
    message += f"💰 कुल भुगतान राशि: ₹{data['paid_amount']}\n"
    message += f"🧾 लेन-देन संख्या: {data['transaction_no']}\n\n"
    message += "👨‍👩‍👧‍👦 विद्यार्थियों का विवरण:\n"

    for sibling in data['siblings']:
        message += f"\n🔹 नाम: {sibling['studentName']}\n"
        message += f"   🏫 कक्षा: {sibling['className']}\n"
        message += f"   🎓 रोल नंबर: {sibling['rollNo']}\n"
        message += f"   📌 {sibling['fees']['monthly']['label']}: {', '.join(sibling['fees']['monthly']['months'])} (₹{sibling['fees']['monthly']['total']})\n"
        for ot_fee in sibling['fees'].get('oneTime', []):
            message += f"   📌 {ot_fee['name']}: ₹{ot_fee['amount']}\n"

    message += "\nआपके समय पर भुगतान के लिए धन्यवाद!"
    return message
