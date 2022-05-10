import googlemaps

from ortools_viz_backend.config import GMAPS_KEY

_client: googlemaps.Client = None


def get_client() -> googlemaps.Client:
    global _client
    if _client is None:
        _client = googlemaps.Client(key=GMAPS_KEY)
    return _client
