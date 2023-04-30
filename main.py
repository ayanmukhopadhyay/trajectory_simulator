import numpy as np
from enum import Enum
from math import ceil

status = Enum('status', 'waiting assigned in_transit dropped_off')
global decision_making_state
states = []
console_log = True
record_only_decision_states = True


class Vehicle:

    def __init__(self, num=0, seats=2):
        self.id = num
        self.capacity = seats
        self.passengers = []
        self.passengers_assigned = []
        self.route = []
        self.position = None
        self.next_time = None
        self.current_location = 0

    def assign_to_vehicle(self, p, t):
        if len(self.passengers_assigned) + len(self.passengers) > self.capacity:
            raise "Error: capacity violated"
        if len(self.passengers_assigned) + len(self.passengers) == self.capacity:
            return False
        elif len(self.route) == 0:
            self.route.append(p.pickup_location)
            self.route.append(p.dropoff_location)
            self.next_time = int(t + calculate_distance(self.current_location, p.pickup_location))

        else:
            # find the point in the route where the vehicle is closest to passenger
            min_dist = 1e10
            closest_index = None
            for i in range(len(self.route)):
                cell = self.route[i]
                dist_temp = calculate_distance(cell, p.pickup_location)
                if dist_temp < min_dist:
                    closest_index = i
                    min_dist = dist_temp
            self.route.insert(closest_index + 1, p.pickup_location)
            self.route.append(p.dropoff_location)

        self.passengers_assigned.append(p)
        update_requests(p.id, status.assigned)
        return True

    def update_route_time(self, t):
        if len(self.route) == 0:
            return
        if self.next_time == t and len(self.route) == 1:
            self.route.pop(0)
            return
        if self.next_time == t:
            dist = calculate_distance(self.route[0], self.route[1])
            self.route.pop(0)
            self.next_time = int(t + ceil(dist))

    def pick_up_passenger(self, p):
        p.current_status = status.in_transit
        self.passengers.append(p)

    def dropoff_passenger(self, i):
        self.passengers.pop(i)

    def check_time(self, t):
        if self.next_time == t:
            global decision_making_state
            decision_making_state = True
            self.current_location = self.route[0]
        for i in range(len(self.passengers_assigned)):
            if self.passengers_assigned[i].pickup_location == self.current_location:
                update_requests(self.passengers_assigned[i].id, status.in_transit)
                self.pick_up_passenger(self.passengers_assigned[i])
                print_log("Passenger {} was picked up by vehicle {}".format(self.passengers_assigned[i].id, self.id))
                self.passengers_assigned.pop(i)
                break  # bad coding: assuming that one location only has one passenger
        for i in range(len(self.passengers)):
            if self.passengers[i].dropoff_location == self.current_location:
                print_log("Passenger {} was dropped off by vehicle {}".format(self.passengers[i].id, self.id))
                update_requests(self.passengers[i].id, status.dropped_off)
                self.dropoff_passenger(i)
                break  # bad coding: assuming that one location only has one passenger

        self.update_route_time(t)


class Passenger:

    def __init__(self, id_num=None, p_t=0, d_t=30, p_l=0, d_l=1, r_t=0):
        self.id = id_num
        self.pickup_time = p_t
        self.dropoff_time = d_t
        self.pickup_location = p_l
        self.dropoff_location = d_l
        self.current_status = status.waiting
        self.request_time = r_t


# helper methods

def calculate_distance(a, b):
    a = cell_location[a]
    b = cell_location[b]
    return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def check_requests(requests, t):
    for r in requests:
        if r.request_time == t:
            return r


def get_request_by_id(id):
    for i in range(len(requests)):
        if requests[i].id == id:
            return i


def update_requests(id, status):
    for i in range(len(requests)):
        if requests[i].id == id:
            requests[i].current_status = status


def print_log(statement):
    if console_log:
        print(statement)

cell_location = {}
grid = np.zeros([5, 5], dtype=int)
ind = 0
for i in range(len(grid)):
    for j in range(len(grid[0])):
        cell_location[ind] = (i, j)
        ind += 1

print_log("Total cells in the map are {}".format(ind))
travel_time_matrix = np.zeros([ind, ind], dtype=float)
for i in range(ind):
    for j in range(ind):
        travel_time_matrix[i, j] = calculate_distance(i, j)

print_log("Generated Travel Time Matrix")

vehicles = []
for i in range(2):
    vehicles.append(Vehicle(num=i))
passengers = []

requests_raw = [
    [1, 1, 5, 5, 9, 1],
    [2, 3, 6, 7, 11, 2],
    [3, 4, 20, 8, 20, 3],
    [4, 12, 19, 9, 24, 5],
    [5, 7, 10, 10, 20, 6],
    [5, 11, 18, 15, 25, 8]
]

requests = []
for i in range(len(requests_raw)):
    p = Passenger(
        id_num=requests_raw[i][0],
        p_t=requests_raw[i][3],
        d_t=requests_raw[i][4],
        p_l=requests_raw[i][1],
        d_l=requests_raw[i][2],
        r_t=requests_raw[i][5]
    )
    requests.append(p)

for t in range(35):
    decision_making_state = False
    print_log("*** TIME {} ***".format(t))

    # check if any vehicle has to pick up or drop off a passenger at this time
    for i in range(len(vehicles)):
        vehicles[i].check_time(t)

    # now check if any new requests have come at this time
    r = check_requests(requests, t)
    if r is not None:
        decision_making_state = True
        print_log("There is a new request from {} to {}".format(r.pickup_time, r.dropoff_time))
        is_assign = False
        for i in range(len(vehicles)):
            is_assign = vehicles[i].assign_to_vehicle(r, t)
            if is_assign:
                print_log("The new request has been assigned to vehicle {}".format(i))
                break

    if record_only_decision_states and decision_making_state:
        states.append([t, vehicles, requests])
    else:
        states.append([t, vehicles, requests])


