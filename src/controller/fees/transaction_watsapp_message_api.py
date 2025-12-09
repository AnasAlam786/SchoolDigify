from flask import Blueprint, request, jsonify
from .utils.watsapp_messages import transaction_whatsapp_message

transaction_whatsapp_message_bp = Blueprint( 'transaction_whatsapp_message_bp',   __name__)


@transaction_whatsapp_message_bp.route('/api/transaction_whatsapp_message', methods=['POST'])
def get_demand_fee_message():
    try:
        data = request.get_json()  # Parse JSON body
        if not data or 'transaction' not in data:
            return jsonify({"message": "transaction data is required"}), 400

        transaction = data['transaction']

        # Generate WhatsApp demand message
        whatsapp_message = transaction_whatsapp_message(transaction)

        print(whatsapp_message)

        return jsonify({
            "whatsapp_message": whatsapp_message,
            "status": "success"
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500
