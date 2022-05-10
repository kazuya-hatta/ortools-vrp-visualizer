from typing import Dict

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from ortools_viz_backend import types
from ortools_viz_backend import gmaps
from ortools_viz_backend import sample_data


def solve_vrp_simple(
    num_vehicles: int, depot: str, waypoints: Dict[str, str], debug: bool = False
) -> types.RoutingSolution:

    keys, values = zip(*waypoints.items())
    addresses = [depot, *values]

    if debug:
        distance_matrix = sample_data.SAMPLE_DISTANCE_MATRIX
    else:
        gmaps_client = gmaps.get_client()
        distance_matrix = gmaps_client.distance_matrix(
            origins=addresses, destinations=addresses
        )

    # Parse duration matrix
    duration_matrix = []
    for row in distance_matrix["rows"]:
        durations = []
        for elem in row["elements"]:
            if elem["status"] != "OK":
                raise Exception(
                    f"Error parsing gmap distance matrix element. Status: {elem['status']}"
                )
            durations.append(elem["duration"]["value"])
        duration_matrix.append(durations)

    # Calculate VRP
    # Create manager/model
    manager = pywrapcp.RoutingIndexManager(len(duration_matrix), num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Set callback
    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return duration_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add dimension
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        60 * 60 * 8,  # vehicle maximum travel time
        True,  # start cumul to zero
        "Duration",
    )
    routing.GetDimensionOrDie("Duration").SetGlobalSpanCostCoefficient(100)

    # Create parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve
    solution = routing.SolveWithParameters(search_parameters)

    # Parse solution
    if solution:
        res: types.RoutingSolution = []
        for vehicle_id in range(num_vehicles):

            vehicle: types.RoutingSolutionElem = {"route": [], "total_time": 0}
            index = routing.Start(vehicle_id)

            while not routing.IsEnd(index):
                waypoint = distance_matrix["destination_addresses"][
                    manager.IndexToNode(index)
                ]
                vehicle["route"].append(waypoint)

                previous_index = index
                index = solution.Value(routing.NextVar(index))

                vehicle["total_time"] += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )

            depot_address = distance_matrix["destination_addresses"][
                manager.IndexToNode(index)
            ]
            vehicle["route"].append(depot_address)
            res.append(vehicle)

        return res

    else:
        raise Exception("No solution found")
