import base64
import io
from typing import List, Tuple, Dict, Any
from datetime import datetime

import googlemaps
import httpx

from ortools_viz_backend import types
from ortools_viz_backend.config import GMAPS_KEY


_client: googlemaps.Client = None

colors = [
    ("0xFF0000B3", "red"),
    ("0x008000B3", "green"),
    ("0x0000FFB3", "blue"),
    ("0x800000B3", "maroon"),
    ("0xFFFF00B3", "yellow"),
    ("0x00FFFFB3", "cyan"),
    ("0xC0C0C0B3", "silver"),
    ("0x00FF00B3", "lime"),
    ("0xFF00FFB3", "magenta"),
    ("0x808000B3", "olive"),
    ("0x800080B3", "purple"),
    ("0x008080B3", "teal"),
    ("0x000080B3", "navy"),
]


def get_client() -> googlemaps.Client:
    global _client
    if _client is None:
        _client = googlemaps.Client(key=GMAPS_KEY)
    return _client


def get_distance_matrix(addresses: List[str], key: str = "distance", api_kwargs: Dict[Any, Any] = {}) -> List[List[int]]:
    """Get or-tools compatible distance matrix from GMaps Distance Matrix API"""

    assert key in (
        "distance",
        "duration",
    ), f"`key` must be either 'distance' or 'duration'. Received '{key}'"

    mtrx = get_client().distance_matrix(origins=addresses, destinations=addresses, **api_kwargs)

    distance_matrix = []
    for row in mtrx["rows"]:
        distances = []
        for elem in row["elements"]:
            if elem["status"] != "OK":
                raise Exception(
                    f"Error parsing gmap distance matrix element. Status: {elem['status']}"
                )
            distances.append(elem[key]["value"])
        distance_matrix.append(distances)

    return distance_matrix


def get_formatted_addresses(addresses: List[str]) -> List[str]:
    """Geocode addresses in list"""
    return [get_client().geocode(l)[0]["formatted_address"] for l in addresses]


async def get_static_map(
    result: types.VRPSimpleOutput,
    addresses: List[str],
    size: Tuple[int, int] = (700, 400),
) -> bytes:
    """Static Map + route polylines and depot/waypoint markers"""

    markers = ""
    paths = ""

    # depot
    depot = addresses[0]
    markers += f"&markers=color:{colors[0]}|label:D|{addresses[0]}"

    print(addresses)
    for elem in result:
        vehicle_id = elem["vehicle_id"]
        vehicle_color = colors[vehicle_id + 1][0]

        for route in elem["routes"][:-1]:  # no depot
            destination = addresses[route["destination"]]
            markers += (
                f"&markers=color:{vehicle_color}|label:{vehicle_id}|{destination}"
            )

        # Get Directions
        vehicle_waypoints = [
            addresses[route["destination"]] for route in elem["routes"][:-1]
        ]
        vehicle_directions = get_client().directions(
            depot, depot, mode="driving", waypoints=vehicle_waypoints
        )
        vehicle_polylines = [
            step["polyline"]["points"]
            for d in vehicle_directions
            for leg in d["legs"]
            for step in leg["steps"]
        ]
        for polyline in vehicle_polylines:
            paths += f"&path=weight:5|color:{vehicle_color}|enc:{polyline}"

    f = io.BytesIO()
    async with httpx.AsyncClient() as cl:
        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"size={size[0]}x{size[1]}" + markers + paths + f"&key={GMAPS_KEY}"
        )
        print(len(url))
        async with cl.stream("GET", url) as res:
            async for chunk in res.aiter_bytes():
                if chunk:
                    f.write(chunk)

    img = base64.b64encode(f.getvalue()).decode("utf8")

    return img
