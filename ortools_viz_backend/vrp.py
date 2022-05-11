from typing import Optional

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver.pywrapcp import (
    RoutingIndexManager,
    RoutingModel,
    DefaultRoutingSearchParameters,
    Assignment,
)

from ortools_viz_backend import types


def parse_solution(
    data: types.VRPSimpleInputData,
    manager: RoutingIndexManager,
    routing: RoutingModel,
    solution: Assignment,
) -> types.VRPSimpleOutput:

    output: types.VRPSimpleOutput = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        output_elem: types.VRPSimpleOutputElem = {
            "vehicle_id": vehicle_id,
            "route_total_cost": 0,
            "routes": [],
        }

        while not routing.IsEnd(index):
            prev_index = index
            index = solution.Value(routing.NextVar(index))

            single_route: types.VRPSimpleOutputSingleRoute = {}
            single_route["origin"] = manager.IndexToNode(prev_index)
            single_route["destination"] = manager.IndexToNode(index)
            single_route["route_cost"] = routing.GetArcCostForVehicle(
                prev_index, index, vehicle_id
            )

            output_elem["route_total_cost"] += single_route["route_cost"]
            output_elem["routes"].append(single_route)

        output.append(output_elem)

    return output


def solve_vrp_simple(data: types.VRPSimpleInputData) -> Optional[types.VRPSimpleOutput]:
    # Create the routing index manager.
    manager = RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    # Create Routing Model.
    routing = RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        data["max_cost_per_vehicle"],  # vehicle maximum cost
        True,  # start cumul to zero
        dimension_name,
    )
    routing.GetDimensionOrDie(dimension_name).SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console & return
    if solution:
        return parse_solution(data, manager, routing, solution)
    else:
        return print("No solution found !")
