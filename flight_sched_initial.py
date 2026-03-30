#Flight Booking & Route Optimization System
#Proof of concept implementation for data structures and core logic of the flight scheduling system.
"""
Implements the three data structures defined in Phase 1:
  1. AirportRegistry  — Hash table for O(1) airport lookup
  2. FlightGraph      — Weighted directed graph (adjacency list)
  3. MinHeap          — Binary min-heap priority queue
 
Each class is self-contained and independently testable.
"""

import re
 
import heapq
from typing import Optional
 
 
# ══════════════════════════════════════════════════════════════
# Airport Registry  —  Hash Table for quick airport metadata lookup
#Implemented using python's built-in dict for O(1) average-case complexity on insertions and lookups.
#Easy and simple, since we don't need to implement a heap based on the hash table

 
class AirportRegistry:
    """
    Hash table that maps IATA airport codes to airport metadata.
 
    Keys   : IATA code (str), e.g. "00SC"
    Values : list of metadata fields (name, city, country)  

    """
 
    def __init__(self):
        self._table: dict[str, tuple[str, str, str]] = {}
 
    #Add new airport or update existing one
 
    def add_airport(self, code: str, name: str, city: str, country: str) -> None:
        """Register an airport
        If the code already exists, it will be overwritten with the new metadata.
        Make sure to use uppercase IATA codes for consistency.
        """
        self._table[code.upper()] = (name, city, country)

    #Remove airport by code
 
    def remove_airport(self, code: str) -> bool:
        """Remove an airport by code. Returns True if it existed."""
        return self._table.pop(code.upper(), None) is not None
 
    #Lookup by code
    #Might return the metadata tuple (name, city, country) or None if the code is not found
 
    def get_airport(self, code: str) -> Optional[dict]:
        """ookup by IATA code. Returns None if not found."""
        return self._table.get(code.upper())
    
    #Reverse lookup by name
    #Expect to be used only during initial user query parsing 
    #Match for regex and may return multiple matches. Will ask user to disambiguate if multiple matches
    #Return code, name, city, country for each match
    def get_codes_by_name(self, query: str) -> list[tuple[str, str, str, str]]:
        """
        Reverse lookup: regex query → list of matching IATA codes from airport name 
        """
        matches = []
        for code, info in self._table.items():
            name = info[0]
            if re.search(query, name, re.IGNORECASE):
                matches.append((code, info[0], info[1], info[2]))
        return matches

    
    #Reverse lookup by city 
    #Return code, name, city, country for each match
    def get_codes_by_city(self, city: str) -> list[tuple[str, str, str, str]]:
        """
        Reverse lookup: city name → list of matching IATA codes from city name 
        """
        matches = []
        for code, info in self._table.items():
            city_name = info[1]
            if re.search(city, city_name, re.IGNORECASE):
                matches.append((code, info[0], info[1], info[2]))
        return matches
    
    def exists(self, code: str) -> bool:
        """existence check."""
        return code.upper() in self._table
 
    def all_codes(self) -> list[str]:
        """Return all registered IATA codes."""
        return list(self._table.keys())
 
    def all_airports(self) -> list[tuple[str, tuple[str, str, str] ]]:
        """Return list of (code, metadata) pairs."""
        return list(self._table.items())

""" 
    # ── Helpers ───────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._table)
 
    def __repr__(self) -> str:
        return f"AirportRegistry({len(self)} airports)"

""" 

 
# ══════════════════════════════════════════════════════════════
#flight grap: constrtuct the graph based on nodes with a list of edges, and each edge having the target, travel time, cost and flight id

class FlightEdge:
    """
    Represents a destination airport 
  
    destination  : IATA code of the arrival airport
    travel_time  : flight duration in minutes
    cost         : one-way ticket price in USD
    flight_id    : unique flight identifier 
    """
 
    __slots__ = ("destination", "travel_time", "cost", "flight_id")

    #Create node on initialization, no overloads 
 
    def __init__(self, destination: str, travel_time: int,
                 cost: float, flight_id: str):
        self.destination = destination
        self.travel_time = travel_time   # minutes
        self.cost        = cost          # USD
        self.flight_id   = flight_id

    #Return weight based on optimization mode 
 
    def weight(self, mode: str) -> float:
        """
        Return the  weight based on cost function.
 
  
        time  → minimize total flight minutes
        cost  → minimize total ticket price (USD)
        connections  → minimize number of connections (weight = 1 per hop)
        """
        if mode == "time":
            return float(self.travel_time)
        if mode == "cost":
            return float(self.cost)
        if mode == "connections":
            return 1.0
        raise ValueError(f"Unknown optimization mode: '{mode}'. "
                         f"Choose 'time', 'cost', or 'connections'.")
 

#FLight grap: Add a node for each airport and a directed edge for each flight 
#Use dict since we want fast lookup and there is a one node for each airport 
 
class FlightGraph:
    """
    Weighted directed graph representing the airline route network.
 
    Representation : adjacency list
        _adj[origin_code] = [FlightEdge, FlightEdge, ...]
 
    Each FlightEdge stores TWO weights (travel_time and cost) so that
    the same graph structure can serve all three optimization modes
    without duplication. 

    """
 
    def __init__(self):
        self._adj: dict[str, list[FlightEdge]] = {}
        self._edge_count: int = 0
 
    #add airport node 
 
    def add_node(self, code: str) -> None:
        """Register an airport node. No-op if already present."""
        code = code.upper()
        if code not in self._adj:
            self._adj[code] = []

    #Add directed edge between airports 
 
    def add_edge(self, origin: str, destination: str,
                 travel_time: int, cost: float, flight_id: str) -> None:
        """
        Add a directed flight edge origin → destination.
        creates nodes for both airports if not already present.
        """
        origin      = origin.upper()
        destination = destination.upper()
        self.add_node(origin)
        self.add_node(destination)
        edge = FlightEdge(destination, travel_time, cost, flight_id)
        self._adj[origin].append(edge)
        self._edge_count += 1

    #Remove edge by flight id
 
    def remove_edge(self, origin: str, flight_id: str) -> bool:
        """Remove the first edge with the given flight_id from origin."""
        origin = origin.upper()
        edges = self._adj.get(origin, [])
        for i, e in enumerate(edges):
            if e.flight_id == flight_id:
                edges.pop(i)
                self._edge_count -= 1
                return True
        return False
    
    #Return all edges from a given airport node
 
 
    def neighbors(self, code: str) -> list[FlightEdge]:
        """Return all outgoing FlightEdge objects from the given airport."""
        return self._adj.get(code.upper(), [])
    
    #Check if airport node exists in the graph
 
    def has_node(self, code: str) -> bool:
        return code.upper() in self._adj
    
    #Return all airport nodes in the graph
 
    def all_nodes(self) -> list[str]:
        return list(self._adj.keys())
 
    @property
    def node_count(self) -> int:
        return len(self._adj)
 
    @property
    def edge_count(self) -> int:
        return self._edge_count
    
    #Print stats, total number of nodes equals total number of airports, total number of edges equals total number of flights
   
    def summary(self) -> dict:
        """Return basic graph statistics."""
        return {
            "nodes":      self.node_count,
            "edges":      self.edge_count,
        }
 

#Structures for route calculation algorithm 
#A min-heap structure based on the accumulated weights of the partial routes is the base for the route calculation
# Node for the heap 
#Key: airport code
#Weight: accumulated cost/time/connections to reach this node from the origin
#Path: list of IATA codes representing the path taken to reach this node, assume only one path connects two nodes directly




class MinHeap:
    """
    Min-heap priority queue for route calculation.
    Each element is a tuple of (weight, airport_code, path).
    The heap is implemented as a list, and the hash table maps airport codes to their index in the heap for O(1) access during key updates.
    """
    def __init__(self, initial_data=None):
        self.heap = [] #List of tuples (weight, airport_code, path)
        self.size = 0
        #If initial data is provided, insert it into the heap
        #initial_data is a list of tuples (weight, airport_code, path)
        if initial_data is not None:
            for element in initial_data:
                self.insert(element[0], element[1], element[2])
    
    #Decrese key function: Update the weight of an element in the heap and maintain the heap priority
    def decrease_key(self, index, new_weight):
        #Update the weight in the heap array
        airport_code = self.heap[index][1]
        path = self.heap[index][2]
        self.heap[index] = (new_weight, airport_code, path)
        while index > 0:
            parent_index = (index - 1) // 2
            if self.heap[index][0] < self.heap[parent_index][0]:
                #Swap the current element with its parent
                tmp_val = self.heap[index]
                self.heap[index] = self.heap[parent_index]
                self.heap[parent_index] = tmp_val
                #Update the index to the parent's index for the next iteration
                index = parent_index
            else:
                break
    #insert function: First insert it in the heap array and return the index, then maintain the heap property by decreasing the key
    # new element is always inserted at the end of the heap array, then we decrease the key to maintain the heap property
    def insert(self, weight, airport_code, path):
        #Insert the weight, airport_code, path tuple into the heap array
        #If the heap size is greater than self.size, it means that we may have some empty slots in the heap array due to previous extractions, so we can reuse those slots instead of appending to the end of the array
        if self.size < len(self.heap):
            self.heap[self.size] = (weight, airport_code, path)
        else:
            self.heap.append((weight, airport_code, path))
        self.size += 1
        #Decrease the key of the new element to maintain the heap property
        self.decrease_key(self.size - 1, weight)

    #extract min function: Remove and return the element with the smallest weight (the root of the heap), then maintain the heap property by decreasing the key of the last element and heapifying the root
    # Return the airport code, weight, and path of the extracted element
    def extract_min(self):
        if self.size == 0:
            return None #Heap is empty
        min_element = self.heap[0]
        weight, airport_code, path = min_element[0], min_element[1], min_element[2]
        #Make the weight of the root element positive infinity and swap it with the last element in the heap array, then heapify the root to maintain the heap property
        self.heap[0] = (float('inf'), airport_code, path)
        #Swap the root with the last element in the heap array
        tmp_val = self.heap[0]
        self.heap[0] = self.heap[self.size - 1]
        self.heap[self.size - 1] = tmp_val
        #Heapify the root to maintain the heap property
        self.size -= 1
        self.heapify(self.heap, self.size, 0)
        return airport_code, weight, path #Return the airport code, weight, and path of the extracted element     
    
    #increase key function: Update the weight of an element in the heap and maintain the heap priority
    def increase_key_element(self, index, new_weight):
        #Update the weight in the heap array
        airport_code = self.heap[index][1]
        path = self.heap[index][2]
        self.heap[index] = (new_weight, airport_code, path)
        #Heapify the element at the given index to maintain the heap property
        self.heapify(self.heap, self.size, index)
    
    #decrease key function: Update the weight of an element in the heap and maintain the heap priority
    def decrease_key_element(self, index, new_weight):
        #Update the weight in the heap array
        airport_code = self.heap[index][1]
        path = self.heap[index][2]
        self.heap[index] = (new_weight, airport_code, path)
        #Decrease the key of the element at the given index to maintain the heap property
        self.decrease_key(index, new_weight)

    #Check if the heap is empty
    def is_empty(self):
        return self.size == 0
    
    #Heapify function: Maintain the heap property by heapifying the element at the given index
    def heapify(self, arr, n, i):
        #Start with i as the smallest element (the element to be heapified)
        smallest = i 
        l = 2 * i + 1 # left = 2*i + 1
        r = 2 * i + 2 # right = 2*i + 2

        
        # If left child is smaller than root
        if l < n and arr[l][0] < arr[smallest][0]:
            smallest = l

        # If right child is smaller than smallest so far
        if r < n and arr[r][0] < arr[smallest][0]:
            smallest = r

        # If smallest is not root
        if smallest != i:
            # Swap elements in heap
            tmp_val = arr[i]
            arr[i] = arr[smallest]
            arr[smallest] = tmp_val
            
            #smallest keeps the swapped element's index, so we need to heapify the affected sub-tree
            self.heapify(arr, n, smallest)


#Initial route calculation algorithm: Dijkstra's algorithm using the MinHeap for the priority queue and the FlightGraph for the graph representation.
# The algorithm will be implemented in a separate function that takes the FlightGraph,  origin code, destination code, and optimization mode as input and returns the optimal route and its total weight.

def RouteCalculation(graph: FlightGraph, origin: str, destination: str, mode: str) -> Optional[tuple[float, list[str]]]:
    """
    Calculate the optimal route from origin to destination based on the given optimization mode.
    Returns a tuple of (total_weight, path) where total_weight is the accumulated weight of the optimal route and path is a list of IATA codes representing the route taken.
    If no route exists, returns None.
    """

    destination = destination.upper()
    origin = origin.upper()
    #Check if origin and destination airports exist in the graph
    if not graph.has_node(origin):
        print(f"Origin airport '{origin}' does not exist in the graph.")
        return None
    if not graph.has_node(destination):
        print(f"Destination airport '{destination}' does not exist in the graph.")
        return None
    
    #Initialize the min-heap priority queue with the origin airport
    min_heap = MinHeap()
    min_heap.insert(0.0, origin, [origin]) # (weight, airport_code, path)
    
    #Initialize a dictionary to keep track of visited airports and their best known weights
    visited = {}
    
    while not min_heap.is_empty():
        current_airport, current_weight, current_path = min_heap.extract_min()
        
        #If we have reached the destination airport, return the total weight and path
        if current_airport == destination:
            return current_weight, current_path
        
        #If we have already visited this airport with a better weight, skip it
        if current_airport in visited and visited[current_airport] <= current_weight:
            continue
        
        #Mark the current airport as visited with its best known weight
        visited[current_airport] = current_weight
        
        #Explore neighbors (outgoing flights) from the current airport
        for edge in graph.neighbors(current_airport):
            next_airport = edge.destination
            edge_weight = edge.weight(mode)
            new_weight = current_weight + edge_weight
            
            #If we have already visited the next airport with a better weight, skip it
            if (next_airport in visited) and (visited[next_airport] <= new_weight):
                continue
            
            #Insert the next airport into the min-heap with its new accumulated weight and updated path
            new_path = current_path + [next_airport]
            min_heap.insert(new_weight, next_airport, new_path)
    
    #If we exhaust the heap without reaching the destination, it means there is no route available
    print(f"No route found from '{origin}' to '{destination}'.")
    return None


#Entry 
#The program takes the following argments:
# 1. A list of airports with their metadata (code, name, city, country)
# Format: ident,type,name,elevation_ft,continent,iso_country,iso_region,municipality,icao_code,iata_code,gps_code,local_code,coordinates
# 2. A list of flights with their details (origin code, destination code, travel time, cost, flight id)
# Format: flight_id,origin_code,destination_code,travel_time,cost
#Then, it prompts the user to input the origin and destination airports (by code, name, or city) and the optimization mode (time, cost, or connections), and it calculates and displays the optimal route based on the user's input.

if __name__ == "__main__":
    import csv
    import sys
    import os
    import argparse
    #Parse command-line arguments for input files
    parser = argparse.ArgumentParser(description="Flight Booking & Route Optimization System")
    parser.add_argument("--airports", required=True, help="Path to the airports CSV file")
    parser.add_argument("--flights", required=True, help="Path to the flights CSV file")
    args = parser.parse_args()

    #Check if input files exist and the headers are in the expected format. If not, print an error message and exit.
    if not os.path.isfile(args.airports):
        print(f"Error: Airports file '{args.airports}' does not exist.")
        sys.exit(1)
    else:
        with open(args.airports, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            expected_headers = ['ident', 'type', 'name', 'elevation_ft', 'continent', 'iso_country', 'iso_region', 'municipality', 'icao_code', 'iata_code', 'gps_code', 'local_code', 'coordinates']
            if headers != expected_headers:
                print(f"Error: Airports file '{args.airports}' has incorrect headers. Expected: {expected_headers}")
                sys.exit(1)

    
    if not os.path.isfile(args.flights):
        print(f"Error: Flights file '{args.flights}' does not exist.")
        sys.exit(1)
    else:
        with open(args.flights, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            expected_headers = ['flight_id', 'origin_code', 'destination_code', 'travel_time', 'cost']
            if headers != expected_headers:
                print(f"Error: Flights file '{args.flights}' has incorrect headers. Expected: {expected_headers}")
                sys.exit(1)
    
    #Initialize the airport registry and flight graph
    airport_registry = AirportRegistry()
    flight_graph = FlightGraph()

    #Load airports from the CSV file into the airport registry
    with open(args.airports, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            code = row['iata_code']
            name = row['name']
            city = row['municipality']
            country = row['iso_country']
            if code: #Only add airports with a valid IATA code
                airport_registry.add_airport(code, name, city, country)
    
    #Load flights from the CSV file into the flight graph
    with open(args.flights, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            flight_id = row['flight_id']
            origin_code = row['origin_code']
            destination_code = row['destination_code']
            travel_time = int(row['travel_time'])
            cost = float(row['cost'])
            flight_graph.add_edge(origin_code, destination_code, travel_time, cost, flight_id)

    #Prompt the user for input and calculate the optimal route
    #After every query, the user can choose to make another query or exit the program. 

    exit_program = False
    while not exit_program:

        #Select the origin airport by code, name, or city. If multiple matches are found, prompt the user to disambiguate by selecting from a list of matches.
        
        valid_input = False
        while not valid_input:
            origin_input = input("Enter the origin airport (code, name, or city): ")
            origin_codes = airport_registry.get_codes_by_name(origin_input) + airport_registry.get_codes_by_city(origin_input) + [(code, *airport_registry.get_airport(code)) for code in airport_registry.all_codes() if code == origin_input.upper()]
            if not origin_codes:
                print(f"No airports found matching '{origin_input}'. Please try again.")
            else:
                valid_input = True
                if len(origin_codes) > 1:
                    print(f"Multiple airports found matching '{origin_input}':")
                    for i, (code, name, city, country) in enumerate(origin_codes):
                        print(f"{i + 1}. {code} - {name}, {city}, {country}")
                    selected_index = int(input("Select the number corresponding to the correct origin airport: ")) - 1

                    valid_input_selected = False
                    while not valid_input_selected:
                        if 0 <= selected_index < len(origin_codes):
                            valid_input_selected = True
                        else:
                            print("Invalid selection. Please enter a number from the list.")
                            selected_index = int(input("Select the number corresponding to the correct origin airport: ")) - 1
                    origin_code = origin_codes[selected_index][0]
                
                else:
                    origin_code = origin_codes[0][0]
        
        print(f"Selected origin airport: {airport_registry.get_airport(origin_code)[0]} - {airport_registry.get_airport(origin_code)[1]}, {airport_registry.get_airport(origin_code)[2]}, {origin_code}")        
        

        #Select the destination airport by code, name, or city. If multiple matches are found, prompt the user to disambiguate by selecting from a list of matches.
        valid_input = False
        while not valid_input:
            destination_input = input("Enter the destination airport (code, name, or city): ")
            destination_codes = airport_registry.get_codes_by_name(destination_input) + airport_registry.get_codes_by_city(destination_input) + [(code, *airport_registry.get_airport(code)) for code in airport_registry.all_codes() if code == destination_input.upper()]
            if not destination_codes:
                print(f"No airports found matching '{destination_input}'. Please try again.")
            else:
                valid_input = True
                if len(destination_codes) > 1:
                    print(f"Multiple airports found matching '{destination_input}':")
                    for i, (code, name, city, country) in enumerate(destination_codes):
                        print(f"{i + 1}. {code} - {name}, {city}, {country}")
                    selected_index = int(input("Select the number corresponding to the correct destination airport: ")) - 1

                    valid_input_selected = False
                    while not valid_input_selected:
                        if 0 <= selected_index < len(destination_codes):
                            valid_input_selected = True
                        else:
                            print("Invalid selection. Please enter a number from the list.")
                            selected_index = int(input("Select the number corresponding to the correct destination airport: ")) - 1
                    destination_code = destination_codes[selected_index][0]
                
                else:
                    destination_code = destination_codes[0][0]
        
        print(f"Selected destination airport: {airport_registry.get_airport(destination_code)[0]} - {airport_registry.get_airport(destination_code)[1]}, {airport_registry.get_airport(destination_code)[2]}, {destination_code}")

        #Select the optimization mode (time, cost, or connections)
        valid_input = False
        while not valid_input:
            optimization_mode = input("Select what you prefer to prioritize (time, cost, connections): ").strip().lower()
            if optimization_mode in ['time', 'cost', 'connections']:
                valid_input = True
            else:
                print("Invalid input. Please enter 'time', 'cost', or 'connections'.")

        #At this point all inputs have been successfully validated and data is ready, proceed with route calculation      



        #Calculate the optimal route using the RouteCalculation function
        result = RouteCalculation(flight_graph, origin_code, destination_code, optimization_mode)
        if result is not None:
            total_weight, path = result
            match optimization_mode:
                case "time":
                    print(f"Optimal route from '{origin_code}' to '{destination_code}' minimizing total travel time:")
                    print(f"Total travel time: {total_weight} minutes")
                case "cost":
                    print(f"Optimal route from '{origin_code}' to '{destination_code}' minimizing total cost:")
                    print(f"Total cost: ${total_weight:.2f}")
                case "connections":
                    print(f"Optimal route from '{origin_code}' to '{destination_code}' minimizing number of connections:")
                    print(f"Total connections: {int(total_weight)}")
            #Print the detailed route with airport codes and names
            print("Travel summary:")
            for code in path:
                airport_info = airport_registry.get_airport(code)
                if airport_info:
                    name, city, country = airport_info
                    print(f"{code} - {name}, {city}, {country}")
                else:
                    print(f"{code} - Airport information not found.")




        else:
            print("No route found.")
        #Ask the user if they want to make another query or exit the program
        valid_input = False
        while not valid_input:
            continue_input = input("Do you want to make another query? (yes/no): ").strip().lower()
            if continue_input in ['yes', 'y']:
                valid_input = True
            elif continue_input in ['no', 'n']:
                valid_input = True
                exit_program = True
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")

        


    

    
















 
 
