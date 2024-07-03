"""
A Graph class for storing our level as a graph
"""
import numpy as np
import random as rnd

# Row, column / Y-delta, X-delta
BIN_OFFSETS = [[0, 0], [0, 1], [0, 2], [0, 3],
               [1, -3], [1, -2], [1, -1], [1, 0], [1, 1], [1, 2], [1, 3],
               [2, -2], [2, -1], [2, 0], [2, 1], [2, 2],
               [3, -1], [3, 0], [3, 1]]


MAX_FORCE = 64


class Portal:
    def __init__(self, a: int, b: int):
        self.a: int = a
        self.b: int = b
        self.overlapping = False


class MapGraph:
    def __init__(self, width, height, momentum=0.05, bin_size=150, endpoint_dist=1000,
                 push_dist=50, pull_dist=30, push_power=2, pull_power=2,
                 k_push=0.1, k_pull=0.5, boundary_dist=30, boundary_power=1.2, k_boundary=0.1):
        # Config parameters
        self.endpoint_dist = endpoint_dist
        self.momentum = momentum
        self.bin_size = bin_size
        self.push_dist = push_dist
        self.pull_dist = pull_dist
        self.boundary_dist = boundary_dist
        self.push_power = push_power
        self.pull_power = pull_power
        self.boundary_power = boundary_power
        self.k_push = k_push
        self.k_pull = k_pull
        self.k_boundary = k_boundary
        self.prev_count = 0

        # Core Stuff
        self.n_rooms: int = 0
        self.room_pos = np.array([[0,0, 0.0]])
        self.room_vel = np.zeros((2, 2))
        self.room_bin = np.zeros(2, dtype=np.int32)
        self.bins = []
        self.portals = []
        self.free_rooms = set()
        self.h_bins: int = 0
        self.v_bins: int = 0
        self.n_bins: int = 0
        self.screen_width = 0
        self.screen_height = 0
        self.center = np.zeros(2)
        self.update_screen_size(width, height)
        r1 = self.add_room([-50, 0], offset=False)
        r2 = self.add_room([50, 0], offset=False)
        self.add_portal(r1, r2)

        self.dbg_has_force = np.zeros((100, 100), dtype=np.int8)
        self.dbg_had_force = np.zeros((100, 100), dtype=np.int8)
        self.dbg_force = np.zeros((100, 100))

    def room_count(self):
        return self.n_rooms - len(self.free_rooms)

    def portal_count(self):
        return len(self.portals)

    def choose_bin(self, room: int) -> int:
        pos = self.center + self.room_pos[room, :]
        rx = pos[0]
        ry = pos[1]
        rh_bin: int = int(np.floor(rx / self.bin_size))
        rv_bin: int = int(np.floor(ry / self.bin_size))
        if rh_bin < 0:
            rh_bin = 0
        if rv_bin < 0:
            rv_bin = 0
        if rh_bin >= self.h_bins:
            rh_bin = self.h_bins - 1
        if rv_bin >= self.v_bins:
            rv_bin = self.v_bins - 1
        r_bin = rv_bin * self.h_bins + rh_bin
        return r_bin

    def create_bins(self) -> None:
        self.h_bins = int(np.ceil(self.screen_width / self.bin_size))
        self.v_bins = int(np.ceil(self.screen_height / self.bin_size))
        self.n_bins = self.h_bins * self.v_bins
        self.bins = [set() for _ in range(self.n_bins)]
        for r in range(self.n_rooms):
            r_bin = self.choose_bin(r)
            self.room_bin[r] = r_bin
            self.bins[r_bin].add(r)

    def update_screen_size(self, width, height) -> None:
        self.screen_width = width
        self.screen_height = height
        self.center = np.array([width / 2, height / 2])
        self.create_bins()

    def add_room(self, pos, offset=True) -> int:
        if len(self.free_rooms) > 0:
            new_room = list(self.free_rooms)[0]
            self.free_rooms.remove(new_room)
        else:
            new_room = self.n_rooms
            self.room_pos.resize([self.n_rooms + 1, 2], refcheck=False)
            self.room_vel.resize([self.n_rooms + 1, 2], refcheck=False)
            self.room_bin.resize(self.n_rooms + 1, refcheck=False)
            self.n_rooms += 1
        self.room_pos[new_room, :] = pos
        if offset:
            self.room_pos[new_room, :] += np.random.normal(0, 10, 2)
        self.room_vel[new_room, :] = [0, 0]
        r_bin = self.choose_bin(new_room)
        self.room_bin[new_room] = r_bin
        self.bins[r_bin].add(new_room)
        return new_room

    def remove_room(self, room) -> None:
        assert room > 1, "Can't remove the start or ending rooms."
        self.free_rooms.add(room)
        self.bins[self.room_bin[room]].remove(room)
        self.portals = [x for x in self.portals if x.a != room and x.b != room]

    def add_portal(self, a, b) -> Portal:
        portal = Portal(a, b)
        self.portals.append(portal)
        return portal

    def remove_portal(self, a, b) -> None:
        self.portals = [x for x in self.portals if (x.a != a and x.b != a) or (x.a != b and x.b != b)]

    def portal_center(self, p):
        return (self.room_pos[p.a, :] + self.room_pos[p.b, :]) / 2.0

    def random_room(self) -> int:
        done = False
        r = -1
        while not done:
            r = rnd.randint(0, self.n_rooms - 1)
            if r not in self.free_rooms:
                done = True
        return r

    def random_portal(self) -> Portal:
        p = rnd.randint(0, len(self.portals) - 1)
        return self.portals[p]

    @classmethod
    def calc_force(cls, dist_1, dist_2, pwr, k) -> float:
        force = k * (dist_1 / dist_2) ** pwr
        if force > MAX_FORCE:
            force = MAX_FORCE
        return force

    def pull(self, a, b):
        if a == b:
            return
        delta = self.room_pos[b] - self.room_pos[a]
        dist = np.sqrt((delta * delta).sum())
        force = self.calc_force(dist, self.pull_dist, self.pull_power, self.k_pull)
        direction = delta / dist
        self.room_vel[a, :] += direction * force
        self.room_vel[b, :] -= direction * force

    def push(self, a, b):
        if a == b:
            return
        delta = self.room_pos[b] - self.room_pos[a]
        dist = np.sqrt((delta * delta).sum())
        force = self.calc_force(self.push_dist, dist, self.push_power, self.k_push)
        if dist > self.bin_size:
            scale = np.maximum(0, 1 - (2 * (dist - self.bin_size) / self.bin_size))
            force *= scale
        if a < 2 and b < 2:
            force += self.calc_force(self.endpoint_dist, dist, self.push_power, self.k_push)
        else:
            if dist >= self.bin_size * 1.5 and force > 0:
                print(f"error: dist: {dist}, force: {force}")
        if force < 0:
            print("error: negative force")
        direction = delta / dist
        self.room_vel[a, :] -= direction * force
        self.room_vel[b, :] += direction * force
        # print(f"push: {a}, {b}: {force:0.4f}")
        return force

    def all_pulls(self):
        for portal in self.portals:
            self.pull(portal.a, portal.b)

    def all_pushes(self) -> int:
        # This will use bins to prevent the N^2 complexity as we add rooms
        push_count = 0
        cum_force = 0.0
        self.dbg_has_force[:, :] = 0
        self.dbg_force[:, :] = 0
        for v1 in range(self.v_bins):
            for h1 in range(self.h_bins):
                bin1 = v1 * self.h_bins + h1
                for a in self.bins[bin1]:
                    for v_offset, h_offset in BIN_OFFSETS:
                        v2 = v1 + v_offset
                        h2 = h1 + h_offset
                        if h2 < self.h_bins and v2 < self.v_bins:
                            bin2 = v2 * self.h_bins + h2
                            for b in self.bins[bin2]:
                                if a != b:
                                    push_count += 1
                                    f = self.push(a, b)
                                    self.dbg_has_force[a, b] = 1
                                    self.dbg_force[a, b] = f
                                    cum_force += f
        # cum_force += self.push(0, 1)
        if push_count != self.prev_count:
            print(f"---- pushes: {push_count}  Force: = {cum_force:0.3f}")
        self.prev_count = push_count
        return push_count

    @classmethod
    def cross_product(cls, d1, d2) -> float:
        # a1 * b2 - a2 * b1
        return d1[0] * d2[1] - d1[1] * d2[0]

    def check_portal_intersect(self, s1, s2):
        """
        Intersect if one of the following two conditions are true:
            * Described as (p1, q1, p2) and (p1, q1, q2) have diff signs
            *          AND (p2, q2, p1) and (p2, q2, q1) have diff signs
            * OR (p1, q1, p2), (p1, q1, q2), (p2, q2, p1), and (p2, q2, q1) are all collinear
            *    AND the x and y projections of (p1, q1) and (p2, q2) interect
            1. (q1 - p1) x (p2 - q1) and (q1 - p1) x (q2 - q1) have different signs
               AND (q2 - p2) x (p1 - q2) and (q2 - p2) x (q1 - q2) have different signs
        """
        pass

    def check_boundary(self, room):
        x, y = self.room_pos[room]
        sx, sy = self.room_pos[room] + self.center
        if x > 0:
            dx = np.maximum(self.screen_width - sx, 5)
            x_dir = -1
        else:
            dx = np.maximum(sx, 5)
            x_dir = 1
        if y > 0:
            dy = np.maximum(self.screen_height - sy, 5)
            y_dir = -1
        else:
            dy = np.maximum(sy, 5)
            y_dir = 1
        x_force = self.calc_force(self.boundary_dist, dx, self.boundary_power, self.k_boundary)
        y_force = self.calc_force(self.boundary_dist, dy, self.boundary_power, self.k_boundary)
        self.room_vel[room, :] += [x_dir * x_force, y_dir * y_force]

    def update_room(self, room, scale=1.0) -> None:
        self.check_boundary(room)
        self.room_pos[room, :] += self.room_vel[room, :] * scale
        self.room_vel[room, :] *= self.momentum
        old_bin = self.room_bin[room]
        new_bin = self.choose_bin(room)
        if old_bin != new_bin:
            self.bins[old_bin].remove(room)
            self.bins[new_bin].add(room)
            self.room_bin[room] = new_bin

    def update_all_rooms(self, scale=1.0):
        for r in range(self.n_rooms):
            self.update_room(r, scale)

