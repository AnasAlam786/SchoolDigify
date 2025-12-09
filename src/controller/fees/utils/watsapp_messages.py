
def fee_demand_message(data):
    msg_lines = []

    msg_lines.append("🏫 *स्कूल शुल्क की सूचना*\n")
    msg_lines.append("प्रिय अभिभावक जी,\n")
    msg_lines.append("आपके बच्चे/बच्चों का *कुछ शुल्क अभी बकाया* है।")
    msg_lines.append("कृपया इसे *जल्द जमा कर दें*, ताकि कोई दिक्कत न हो.\n")

    overall_total = 0

    msg_lines.append("====================================")

    for student in data:
        name = student['name']
        class_ = student['class']
        roll = student['rollNo']

        msg_lines.append(f"👧 *नाम: {name}*")
        msg_lines.append(f"📚 कक्षा: {class_} | 🎫 रोल नं.: {roll}")
        msg_lines.append("------------------------------------")

        # -----------------------------
        # Monthly Fees (due only)
        # -----------------------------
        due_monthly = []
        for fee in student['monthlyFees']:
            if fee['status'] == 'due':
                due_monthly.append((fee['period_name'], fee['amount']))

        msg_lines.append("📌 *बकाया मासिक शुल्क:*")
        if due_monthly:
            for month, amount in due_monthly:
                msg_lines.append(f"{month} – ₹{amount}")
        else:
            msg_lines.append("कोई बकाया नहीं")

        # -----------------------------
        # Other Fees (due only)
        # -----------------------------
        due_other = []
        for fee in student['otherFees']:
            if fee['status'] == 'due':
                due_other.append((fee['period_name'], fee['amount']))

        msg_lines.append("\n📌 *अन्य बकाया शुल्क:*")
        if due_other:
            for name_other, amount in due_other:
                msg_lines.append(f"{name_other} – ₹{amount}")
        else:
            msg_lines.append("सब जमा")

        # -----------------------------
        # Student total
        # -----------------------------
        student_total = sum(amount for _, amount in due_monthly) + \
                        sum(amount for _, amount in due_other)

        overall_total += student_total

        msg_lines.append(f"\n💰 *कुल बकाया:* **₹{student_total}**")
        msg_lines.append("====================================")

    # ---------------------------------
    # Final Total
    # ---------------------------------
    msg_lines.append(f"🟦 *कुल बकाया (सभी बच्चों का):* **₹{overall_total}**\n")
    msg_lines.append("कृपया *शुल्क जल्द से जल्द जमा करें*।")
    msg_lines.append("किसी भी सवाल के लिए स्कूल से संपर्क करें.\n")
    msg_lines.append("धन्यवाद।")
    msg_lines.append("🏫 *SchoolDigify*")

    # Join all lines into final message
    return "\n".join(msg_lines)


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
