from typing import TypedDict, List


class _GMapsDistanceMatrixRowElementItem(TypedDict):
    text: str
    value: int


class _GMapsDistanceMatrixRowElement(TypedDict):
    distance: _GMapsDistanceMatrixRowElementItem
    duration: _GMapsDistanceMatrixRowElementItem
    status: str


class _GMapsDistanceMatrixRow(TypedDict):
    elements: List[_GMapsDistanceMatrixRowElement]


class GMapsDistanceMatrix(TypedDict):
    destination_addresses: List[str]
    origin_addresses: List[str]
    rows: List[_GMapsDistanceMatrixRow]
    status: str


DurationMatrix = List[List[int]]


class RoutingSolutionElem(TypedDict):
    route: List[str]
    total_time: int


RoutingSolution = List[RoutingSolutionElem]
