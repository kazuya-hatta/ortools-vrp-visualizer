import base64
import io
from urllib.parse import parse_qs
from typing import Optional, List

import googlemaps
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.templating import Jinja2Templates, _TemplateResponse
from starlette.routing import Route

from ortools_viz_backend.config import DEBUG
from ortools_viz_backend import vrp, gmaps


templates = Jinja2Templates(directory="templates")
colors = [
    "red",
    "blue",
    "green",
    "purple",
    "orange",
    "white",
    "black",
    "yellow",
    "aliceblue",
    "gray",
]


async def index(request: Request) -> Optional[_TemplateResponse]:
    if request.method == "GET":
        return templates.TemplateResponse("index.html", {"request": request})

    elif request.method == "POST":
        body = await request.body()
        body_parsed = parse_qs(body.decode("utf-8"))
        vehicles = int(body_parsed["vehicles"][0])
        depot = body_parsed["depot"][0]
        waypoints = {
            k: v[0] for k, v in body_parsed.items() if k.startswith("waypoint-")
        }

        try:
            result = vrp.solve_vrp_simple(
                min(vehicles, len(waypoints)), depot, waypoints
            )

            markers: List[googlemaps.maps.StaticMapMarker] = []
            paths: List[googlemaps.maps.StaticMapPath] = []

            markers.append(googlemaps.maps.StaticMapMarker([depot], color=colors[0], label="D"))
            for i, v in enumerate(result, 1):
                markers.append(googlemaps.maps.StaticMapMarker(v["route"][:-1], color=colors[i], label=str(i)))
                paths.append(googlemaps.maps.StaticMapPath([depot, *v["route"]], color=colors[i]))

            map_data = gmaps.get_client().static_map(
                size=(1200, 1000), markers=markers, path=paths
            )

            f = io.BytesIO()
            for chunk in map_data:
                if chunk:
                    f.write(chunk)
            img = base64.b64encode(f.getvalue()).decode("utf8")

            return templates.TemplateResponse(
                "index.html", {"request": request, "image": img}
            )

        except Exception as e:
            return templates.TemplateResponse(
                "index.html", {"request": request, "error": e}
            )

    else:
        return None


app = Starlette(
    debug=DEBUG,
    routes=[Route("/", index, methods=["GET", "POST"])],
)
