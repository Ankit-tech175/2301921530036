import requests
from app.config import DEPOT_API, VEHICLE_API, ACCESS_TOKEN

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


def get_depots():
    response = requests.get(
        DEPOT_API,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def get_vehicles():
    response = requests.get(
        VEHICLE_API,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()
    return response.json()