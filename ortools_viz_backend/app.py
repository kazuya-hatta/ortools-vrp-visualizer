from urllib.parse import parse_qs
from typing import Optional
from datetime import timedelta

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.templating import Jinja2Templates, _TemplateResponse
from starlette.routing import Route

from ortools_viz_backend.config import DEBUG
from ortools_viz_backend import vrp, types, gmaps


templates = Jinja2Templates(directory="templates")


async def index(request: Request) -> Optional[_TemplateResponse]:
    if request.method == "GET":
        print("GET")
        return templates.TemplateResponse("index.html", {"request": request})

    elif request.method == "POST":
        print("POST")

        # Parse form body
        body = await request.body()
        body_parsed = parse_qs(body.decode("utf-8"))
        vehicles = int(body_parsed["vehicles"][0])
        depot = body_parsed["depot"][0]
        vehicle_hours = float(body_parsed["vehicle-hours"][0])
        waypoints = [v[0] for k, v in body_parsed.items() if k.startswith("waypoint-")]

        # Format addresses
        orig_addresses = [depot, *waypoints]
        formatted_addresses = gmaps.get_formatted_addresses(orig_addresses)
        print(dict(zip(orig_addresses, formatted_addresses)))

        # Instantiate the data problem.
        data: types.VRPSimpleInputData = {}
        data["distance_matrix"] = gmaps.get_distance_matrix(
            addresses=formatted_addresses,
            key="duration",
        )
        data["num_vehicles"] = vehicles
        data["depot"] = 0
        data["max_cost_per_vehicle"] = int(vehicle_hours * 60 * 60)
        print(data)

        # Solve
        result = vrp.solve_vrp_simple(data)

        # Compile return params
        params: types.VRPSimpleOutputParams = {}
        params["vehicles"] = vehicles
        params["vehicle_hours"] = vehicle_hours
        params["depot"] = (orig_addresses[0], formatted_addresses[0])
        params["waypoints"] = {
            f"Waypoint-{i}": v
            for i, v in enumerate(zip(orig_addresses[1:], formatted_addresses[1:]), 1)
        }

        if not result:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": "no result", "params": params},
            )

        # Populate result for route info rendering
        # TODO: cleanup
        # fmt: off
        labels = ["depot", *(f"Waypoint-{i+1}" for i in range(len(waypoints)))]
        result = [
            {
                **elem,
                "route_total_cost_formatted": str(timedelta(seconds=elem["route_total_cost"])),
                "routes": [
                    {
                        **route,
                        "origin_label": labels[route["origin"]],
                        "destination_label": labels[route["destination"]],
                        "origin_formatted_address": formatted_addresses[route["origin"]],
                        "destination_formatted_address": formatted_addresses[route["destination"]],
                        "route_cost_formatted": str(timedelta(seconds=route["route_cost"])),
                    }
                    for route in elem["routes"]
                ],
            }
            for elem in result
        ]
        print(result)
        # fmt: on

        # Map result
        map_image = await gmaps.get_static_map(
            result, formatted_addresses, size=(700, 300)
        )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "map_image": map_image,
                "result": result,
                "params": params,
            },
        )


app = Starlette(
    debug=DEBUG,
    routes=[Route("/", index, methods=["GET", "POST"])],
)
