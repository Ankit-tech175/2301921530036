import requests
from app.config import LOG_API_URL, ACCESS_TOKEN


def log(
        stack="backend",
        level="info",
        package="middleware",
        message=""):
    """
    Send logs to AffordMed Logging Service

    stack:
        backend | frontend

    level:
        debug | info | warn | error | fatal

    package:
        controller | route | service | handler |
        repository | middleware | db
    """

    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            LOG_API_URL,
            json=payload,
            headers=headers,
            timeout=10
        )

        print("Log Status:", response.status_code)
        print("Log Response:", response.text)

        return response.json()

    except Exception as e:
        print("Logging Error:", str(e))