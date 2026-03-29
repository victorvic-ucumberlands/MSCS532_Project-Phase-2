"""Randomized tests for core functionality in flight_sched_initial.py.

This script:
1) Loads airport rows from airport-codes.csv
2) Randomly selects a subset of airports
3) Generates random directed flights between selected airports
4) Runs assertion-based checks for AirportRegistry, FlightGraph, MinHeap,
   and RouteCalculation

Usage:
  python flight_sched_tester.py
  python flight_sched_tester.py --seed 42 --airports 25 --flights 70
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from flight_sched_initial import (
	AirportRegistry,
	FlightGraph,
	MinHeap,
	RouteCalculation,
)


def load_airports(csv_path: Path) -> list[dict[str, str]]:
	"""Load airports that have a non-empty iata_code."""
	airports: list[dict[str, str]] = []
	with csv_path.open(newline="", encoding="utf-8") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			code = (row.get("iata_code") or "").strip().upper()
			if not code:
				continue
			airports.append(
				{
					"code": code,
					"name": (row.get("name") or "Unknown").strip(),
					"city": (row.get("municipality") or "Unknown").strip(),
					"country": (row.get("iso_country") or "Unknown").strip(),
				}
			)
	return airports


def choose_airport_subset(
	airports: list[dict[str, str]],
	count: int,
	rng: random.Random,
) -> list[dict[str, str]]:
	"""Choose a unique random subset of airports."""
	unique_by_code: dict[str, dict[str, str]] = {}
	for ap in airports:
		unique_by_code[ap["code"]] = ap

	deduped = list(unique_by_code.values())
	if len(deduped) < count:
		raise ValueError(
			f"Not enough unique airports with iata_code. Requested={count}, "
			f"available={len(deduped)}"
		)
	return rng.sample(deduped, count)


def generate_random_routes(
	subset: list[dict[str, str]],
	route_count: int,
	rng: random.Random,
) -> list[dict[str, str | int | float]]:
	"""Generate random directed routes with flight code, travel time, and cost."""
	codes = [ap["code"] for ap in subset]
	routes: list[dict[str, str | int | float]] = []

	for i in range(route_count):
		origin, destination = rng.sample(codes, 2)
		routes.append(
			{
				"flight_id": f"FL{i + 1:04d}",
				"origin_code": origin,
				"destination_code": destination,
				"travel_time": rng.randint(45, 600),
				"cost": round(rng.uniform(60.0, 1500.0), 2),
			}
		)

	return routes


def build_data_structures(
	subset: list[dict[str, str]],
	routes: list[dict[str, str | int | float]],
) -> tuple[AirportRegistry, FlightGraph]:
	"""Construct AirportRegistry and FlightGraph from generated data."""
	registry = AirportRegistry()
	graph = FlightGraph()

	for ap in subset:
		registry.add_airport(ap["code"], ap["name"], ap["city"], ap["country"])
		graph.add_node(ap["code"])

	for route in routes:
		graph.add_edge(
			str(route["origin_code"]),
			str(route["destination_code"]),
			int(route["travel_time"]),
			float(route["cost"]),
			str(route["flight_id"]),
		)

	return registry, graph


def test_airport_registry(registry: AirportRegistry, subset: list[dict[str, str]]) -> None:
	"""Validate add/get/existence/remove functionality."""
	sample = subset[0]
	code = sample["code"]

	metadata = registry.get_airport(code)
	assert metadata is not None, "Airport should be present after insertion"
	assert metadata[0] == sample["name"], "Airport name mismatch"
	assert metadata[1] == sample["city"], "Airport city mismatch"
	assert metadata[2] == sample["country"], "Airport country mismatch"

	assert registry.exists(code), "exists() should return True for inserted airport"
	assert code in registry.all_codes(), "all_codes() should include inserted code"

	matches = registry.get_codes_by_city(sample["city"])
	assert any(m[0] == code for m in matches), "City reverse lookup should find airport"

	# Add and remove a temporary airport to validate deletion behavior.
	registry.add_airport("ZZZ", "Unit Test Airport", "Test City", "TS")
	assert registry.remove_airport("ZZZ"), "remove_airport should succeed for existing code"
	assert not registry.remove_airport("ZZZ"), "remove_airport should fail for missing code"


def test_flight_graph(
	graph: FlightGraph,
	subset: list[dict[str, str]],
	routes: list[dict[str, str | int | float]],
) -> None:
	"""Validate graph node/edge insertion, lookup, and edge removal."""
	assert graph.node_count == len(subset), "Node count should match selected airport count"
	assert graph.edge_count == len(routes), "Edge count should match generated routes"

	first_route = routes[0]
	origin = str(first_route["origin_code"])
	first_flight_id = str(first_route["flight_id"])

	neighbors = graph.neighbors(origin)
	assert neighbors, "Origin should have at least one outgoing edge"

	pre_count = graph.edge_count
	removed = graph.remove_edge(origin, first_flight_id)
	assert removed, "remove_edge should remove an existing flight id from origin"
	assert graph.edge_count == pre_count - 1, "Edge count should decrement after removal"

	graph.add_edge(
		origin,
		str(first_route["destination_code"]),
		int(first_route["travel_time"]),
		float(first_route["cost"]),
		first_flight_id,
	)
	assert graph.edge_count == pre_count, "Reinsertion should restore edge count"


def test_min_heap() -> None:
	"""Validate min-heap ordering by repeatedly extracting minimum."""
	heap = MinHeap()
	heap.insert(9.0, "A", ["A"])
	heap.insert(3.0, "B", ["B"])
	heap.insert(7.0, "C", ["C"])
	heap.insert(1.0, "D", ["D"])

	extracted_weights: list[float] = []
	while not heap.is_empty():
		_, weight, _ = heap.extract_min()
		extracted_weights.append(weight)

	assert extracted_weights == sorted(extracted_weights), "Heap extraction should be non-decreasing"


def test_route_calculation_modes(graph: FlightGraph) -> None:
	"""Validate RouteCalculation for all optimization modes on a known mini-graph."""
	g = FlightGraph()
	g.add_edge("AAA", "BBB", 50, 500.0, "T1")
	g.add_edge("BBB", "DDD", 50, 500.0, "T2")
	g.add_edge("AAA", "CCC", 80, 50.0, "T3")
	g.add_edge("CCC", "DDD", 80, 50.0, "T4")
	g.add_edge("AAA", "DDD", 300, 1000.0, "T5")

	result_time = RouteCalculation(g, "AAA", "DDD", "time")
	assert result_time is not None
	weight_time, path_time = result_time
	assert weight_time == 100.0 and path_time == ["AAA", "BBB", "DDD"], "Time mode route mismatch"

	result_cost = RouteCalculation(g, "AAA", "DDD", "cost")
	assert result_cost is not None
	weight_cost, path_cost = result_cost
	assert weight_cost == 100.0 and path_cost == ["AAA", "CCC", "DDD"], "Cost mode route mismatch"

	result_conn = RouteCalculation(g, "AAA", "DDD", "connections")
	assert result_conn is not None
	weight_conn, path_conn = result_conn
	assert weight_conn == 1.0 and path_conn == ["AAA", "DDD"], "Connections mode route mismatch"

	# If the destination does not exist in the graph, function should return None.
	assert RouteCalculation(graph, "XXX", "YYY", "time") is None


def run_all_tests(
	csv_path: Path,
	airport_count: int,
	route_count: int,
	seed: int,
) -> None:
	"""Build randomized input and run all core assertions."""
	rng = random.Random(seed)

	all_airports = load_airports(csv_path)
	subset = choose_airport_subset(all_airports, airport_count, rng)
	routes = generate_random_routes(subset, route_count, rng)
	registry, graph = build_data_structures(subset, routes)

	test_airport_registry(registry, subset)
	test_flight_graph(graph, subset, routes)
	test_min_heap()
	test_route_calculation_modes(graph)

	print("All core functionality tests passed.")
	print(f"Seed: {seed}")
	print(f"Sampled airports: {airport_count}")
	print(f"Generated routes: {route_count}")
	print(f"Graph summary: {graph.summary()}")


def parse_args() -> argparse.Namespace:
	"""Parse command-line options for randomized test generation."""
	parser = argparse.ArgumentParser(description="Randomized tester for flight_sched_initial.py")
	parser.add_argument(
		"--airports-csv",
		type=Path,
		default=Path("airport-codes.csv"),
		help="Path to airport CSV file (default: airport-codes.csv)",
	)
	parser.add_argument(
		"--airports",
		type=int,
		default=20,
		help="Number of random airports to sample (default: 20)",
	)
	parser.add_argument(
		"--flights",
		type=int,
		default=60,
		help="Number of random flights to generate (default: 60)",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=42,
		help="Random seed for reproducibility (default: 42)",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	run_all_tests(
		csv_path=args.airports_csv,
		airport_count=args.airports,
		route_count=args.flights,
		seed=args.seed,
	)
