from typing import TypedDict, List, Dict, Tuple


class VRPSimpleInputData(TypedDict):
    distance_matrix: List[List[int]]
    num_vehicles: int
    depot: int
    max_cost_per_vehicle: int


class VRPSimpleOutputSingleRoute(TypedDict):
    origin: int
    destination: int
    route_cost: int


class VRPSimpleOutputElem(TypedDict):
    vehicle_id: int
    vehicle_color: str
    routes: List[VRPSimpleOutputSingleRoute]
    route_total_cost: int


VRPSimpleOutput = List[VRPSimpleOutputElem]


class VRPSimpleOutputParams(TypedDict):
    vehicles: int
    vehicle_hours: int
    depot: Tuple[str, str]
    waypoints: Dict[str, Tuple[str, str]]
