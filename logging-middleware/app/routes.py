from flask import Blueprint, jsonify
from app.logger import log

main = Blueprint("main", __name__)


@main.route("/")
def home():
    log(
        stack="backend",
        level="info",
        package="route",
        message="Home route accessed"
    )

    return jsonify({
        "message": "Logging Middleware Working"
    })