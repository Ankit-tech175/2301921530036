from flask import Blueprint, jsonify
from app.services import get_depots, get_vehicles

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return jsonify({
        "message": "Vehicle Scheduler Backend Running"
    })


@main.route("/depots")
def depots():
    try:
        data = get_depots()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@main.route("/vehicles")
def vehicles():
    try:
        data = get_vehicles()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500