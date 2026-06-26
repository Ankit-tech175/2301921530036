import requests
from app.config import DEPOT_API, VEHICLE_API, ACCESS_TOKEN


headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}


def get_depots():
    response = requests.get(
        DEPOT_API,
        headers=headers
    )

    return response.json()


def get_vehicles():
    response = requests.get(
        VEHICLE_API,
        headers=headers
    )

    return response.json()