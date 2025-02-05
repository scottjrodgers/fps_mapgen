# This is a sample Python script.
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import pygame
from pygame import display, draw, Color
from typing import *
import random as rnd
from graph import MapGraph, Portal
import numpy as np


MAX_ROOMS = 10
BIN_SIZE = 200
ENDPOINT_DIST = 200
MOMENTUM = 0.05
PUSH_DIST = 100
PUSH_POWER = 0.5
K_PUSH = 2.5
PULL_DIST = 40
PULL_POWER = 2
K_PULL = 0.4
BOUNDARY_DIST = 50
BOUNDARY_POWER = 1
BOUNDARY_KD = 0.5
UPDATE_SCALE = 2
UPDATE_FRAMES = 5


def extend_portal(g: MapGraph, portal: Optional[Portal] = None):
    if portal is None:
        portal = g.random_portal()
    new_room = g.add_room(g.portal_center(portal))
    end_point = portal.b
    portal.b = new_room
    g.add_portal(new_room, end_point)


def split_portal(g: MapGraph, portal: Optional[Portal] = None):
    if portal is None:
        portal = g.random_portal()
    new_portal = g.add_portal(portal.a, portal.b)
    extend_portal(g, portal)
    extend_portal(g, new_portal)


def add_offshoot(g: MapGraph, r: Optional[int] = None):
    if r is None:
        r = g.random_room()
    pos = g.room_pos[r, :]
    q = g.add_room(pos[0], pos[1])
    g.add_portal(r, q)


def add_loop(g: MapGraph, r: Optional[int] = None):
    pass


def random_level_addition(g, p_extend, p_split, p_offshoot, p_loop):
    x = rnd.random() * (p_extend + p_split + p_offshoot + p_loop)
    base = 0.0
    if x <= base + p_extend:
        extend_portal(g)
        return
    base += p_extend
    if x <= base + p_split:
        split_portal(g)
        return
    base += p_split
    if x <= base + p_offshoot:
        add_offshoot(g)
        return
    base += p_extend
    if x <= base + p_loop:
        add_loop(g)
        return


def level_build_schedule(g: MapGraph):
    schedule = [[4, [90, 10, 0, 0]],
                [5, [50, 20, 30, 0]],
                [10, [30, 50, 30, 0]],
                [10, [20, 20, 50, 10]],
                [999, [30, 30, 40, 0]],
                ]
    n = g.room_count()
    for steps, weights in schedule:
        if n < steps:
            random_level_addition(g, *weights)
            return
        n -= steps


def main():
    pygame.init()

    width, height = 1280, 720
    screen = display.set_mode((width, height), flags=pygame.RESIZABLE)

    clock = pygame.time.Clock()
    level = MapGraph(width, height, momentum=MOMENTUM, bin_size=BIN_SIZE,
                     push_dist=PUSH_DIST, push_power=PUSH_POWER, k_push=K_PUSH,
                     pull_dist=PULL_DIST, pull_power=PULL_POWER, k_pull=K_PULL,
                     boundary_dist=BOUNDARY_DIST, boundary_power=BOUNDARY_POWER, k_boundary=BOUNDARY_KD)
    counter = 0

    show_forces = False

    while True:
        # Process player inputs.
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                raise SystemExit
            if event.type == pygame.WINDOWRESIZED:
                level.update_screen_size(event.x, event.y)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # random augmentation
                    show_forces = not show_forces
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    # Reset the Graph with current settings
                    pass
                elif event.key == pygame.K_b:
                    # extend portal (build)
                    pass
                elif event.key == pygame.K_k:
                    # klip / cut high-tension overlapping portals
                    pass
                elif event.key == pygame.K_j:
                    # clip shortest overlapping portal
                    pass
                elif event.key == pygame.K_s:
                    # split?
                    pass
                elif event.key == pygame.K_o:
                    # offshoot
                    pass
                elif event.key == pygame.K_l:
                    # loop
                    pass
                elif event.key == pygame.K_p:
                    # prune long trains of dead-ends
                    pass
                elif event.key == pygame.K_f:
                    # fix graph by re-attaching a separated subgraph
                    pass

        counter += 1
        if counter > UPDATE_FRAMES and level.room_count() < MAX_ROOMS:
            counter = 0
            level_build_schedule(level)

        # Compute Forces and Move Rooms
        level.all_pushes()
        level.all_pulls()
        level.update_all_rooms()

        # Display
        screen.fill("black")  # Fill the display with a solid color

        if True:
            for i in range(level.h_bins):
                x = i * level.bin_size
                draw.line(screen, Color("0x444444"), [x, 0], [x, level.screen_height])
            for j in range(level.v_bins):
                y = j * level.bin_size
                draw.line(screen, Color("0x444444"), [0, y], [level.screen_width, y])

        # Render the graphics here.
        for portal in level.portals:
            p1 = level.room_pos[portal.a] + level.center
            p2 = level.room_pos[portal.b] + level.center
            color = Color("0x99CCFF")
            if portal.overlapping:
                color = Color("0xDD5555")
            draw.line(screen, color, p1, p2, width=1)

        if show_forces:
            forces = np.where(level.dbg_has_force == 1)
            for a, b in zip(forces[0], forces[1]):
                p1 = level.room_pos[a] + level.center
                p2 = level.room_pos[b] + level.center
                color = Color("0x881100")
                draw.line(screen, color, p1, p2, width=2)

        for room in range(level.n_rooms):
            if room not in level.free_rooms:
                pos = level.room_pos[room] + level.center
                radius = 3
                if room == 0:
                    color = "green"
                    radius = 5
                elif room == 1:
                    color = 'red'
                    radius = 5
                else:
                    color = 'white'
                draw.circle(screen, color, pos, radius)

        display.flip()  # Refresh on-screen display
        clock.tick(10)  # wait until next frame (at 60 FPS)


# # ======================================================
# #                       ROOM
# # ======================================================
# class Room:
#     def __init__(self, name="", x=0, y=0, offset=False):
#         self.name = name
#         self.id = -1
#         self.portals: List[Portal] = []
#         self.x = x
#         self.y = y
#         self.dx = 0
#         self.dy = 0
#         if name not in ("Start", "Finish") or offset:
#             self.x += rnd.random() * 25 - rnd.random() * 25
#             self.y += rnd.random() * 25 - rnd.random() * 25
#
#     def add_portal(self, p):
#         assert p not in self.portals
#         self.portals.append(p)
#
#     def update(self):
#         damping = 0.2
#         self.x += self.dx * UPDATE_SCALE
#         self.y += self.dy * UPDATE_SCALE
#         self.dx *= damping
#         self.dy *= damping
#
#     def direction(self, other):
#         dst = self.dist(other)
#         return (other.x - self.x) / dst, (other.y - self.y) / dst
#
#     def dist(self, other):
#         x1 = self.x
#         y1 = self.y
#         x2 = other.x
#         y2 = other.y
#         d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
#         if d < 1:
#             d = 1
#         return d
#
#     def spring(self, other, target_length, ks):
#         s_limit = 80
#         length = self.dist(other)
#         d_len = target_length - length
#         d_len = d_len / abs(d_len) ** 0.5
#         if d_len > s_limit:
#             d_len = s_limit
#         elif d_len < -s_limit:
#             d_len = -s_limit
#         dx, dy = self.direction(other)
#         self.dx -= dx * d_len * ks
#         self.dy -= dy * d_len * ks
#         other.dx += dx * d_len * ks
#         other.dy += dy * d_len * ks
#
#     def push(self, other, target_dist, power=3, kd=1e-3):
#         length = self.dist(other)
#         p_factor = min([100 * (target_dist / max([length, 1])) ** power, 500.0])
#         dx, dy = self.direction(other)
#         self.dx -= dx * p_factor * kd
#         self.dy -= dy * p_factor * kd
#         other.dx += dx * p_factor * kd
#         other.dy += dy * p_factor * kd
#
#     def pull(self, other, target_dist, power=3, kd=1e-3):
#         length = self.dist(other)
#         p_factor = min([100 * (max([length, 1]) / target_dist) ** power, 500.0])
#         dx, dy = self.direction(other)
#         self.dx += dx * p_factor * kd
#         self.dy += dy * p_factor * kd
#         other.dx -= dx * p_factor * kd
#         other.dy -= dy * p_factor * kd
#
#     def check_boundaries(self, width, height, target_dist, power, kd):
#         half_width = width / 2
#         half_height = height / 2
#         if self.x > 0:
#             h_length = half_width - self.x
#             h_dir = -1
#         else:
#             h_length = self.x + half_width
#             h_dir = 1
#         if self.y > 0:
#             v_length = half_height - self.y
#             v_dir = -1
#         else:
#             v_length = self.y + half_height
#             v_dir = 1
#
#         h_factor = min([10 * (target_dist / max([h_length, 0.1])) ** power, 100.0])
#         v_factor = min([10 * (target_dist / max([v_length, 0.1])) ** power, 100.0])
#         self.dx += h_dir * h_factor * kd
#         self.dy += v_dir * v_factor * kd
#
#
# # ======================================================
# #                       PORTAL
# # ======================================================
# class Portal:
#     def __init__(self, a, b):
#         self.start = None
#         self.end = None
#         self.set_start(a)
#         self.set_end(b)
#         self.overlapping = False
#
#     def set_start(self, room):
#         if self.start is not None:
#             self.start.portals.remove(self)
#         self.start = room
#         room.add_portal(self)
#
#     def set_end(self, room):
#         if self.end is not None:
#             self.end.portals.remove(self)
#         self.end = room
#         room.add_portal(self)
#
#     def unhook(self):
#         if self.start is not None:
#             self.start.portals.remove(self)
#             self.start = None
#         if self.end is not None:
#             self.end.portals.remove(self)
#             self.end = None
#
#     def pull(self, target_length, power=3, ks=1e-3):
#         self.start.pull(self.end, target_length, power, ks)
#
#     def check_overlap(self, other) -> bool:
#         if self.start == other.start or self.start == other.end:
#             return False
#         if self.end == other.start or self.end == other.end:
#             return False
#
#         x1 = self.start.x
#         x2 = self.end.x
#         y1 = self.start.y
#         y2 = self.end.y
#         x3 = other.start.x
#         x4 = other.end.x
#         y3 = other.start.y
#         y4 = other.end.y
#
#         # Bounding Box rejection tests
#         if min([x1, x2]) > max([x3, x4]) or min([x3, x4]) > max([x1, x2]):
#             return False
#         if min([y1, y2]) > max([y3, y4]) or min([y3, y4]) > max([y1, y2]):
#             return False
#
#         # Straddle Test
#         z1 = (x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)
#         z2 = (x4 - x1) * (y2 - y1) - (y4 - y1) * (x2 - x1)
#
#         # if signs of z1 and z2 are different or either zero, the segments straddle
#         if z1 * z2 <= 0:
#             # when segments straddle and BB's overlap, it's an intersection
#             return True
#
#         # reject by default
#         return False
#
#
# # ======================================================
# #                       LEVEL
# # ======================================================
# class Level:
#     def __init__(self):
#         self.rooms: List[Room] = []
#         self.portals: List[Portal] = []
#         self.first: Room = Room("Start", -30, 0)
#         self.last: Room = Room("Finish", 30, 0)
#         self.rooms.append(self.first)
#         self.rooms.append(self.last)
#         self.portals.append(Portal(self.first, self.last))
#
#     def count_portals(self):
#         return len(self.portals)
#
#     def count_rooms(self):
#         return len(self.rooms)
#
#     def balance(self):
#         n = 0
#         x_sum = 0
#         y_sum = 0
#         for room in self.rooms:
#             n += 1
#             x_sum += room.x
#             y_sum += room.y
#
#         x_avg = x_sum / n
#         y_avg = y_sum / n
#
#         for room in self.rooms:
#             room.x -= x_avg
#             room.y -= y_avg
#
#     def jog(self):
#         for portal in self.portals:
#             if portal.overlapping:
#                 for room in [portal.start, portal.end]:
#                     if rnd.random() < 0.55:
#                         room.x += rnd.normalvariate(0, 25)
#                         room.y += rnd.normalvariate(0, 25)
#         self.balance()
#
#     def split_portal(self, portal):
#         # print("split_portal")
#         new_portal = Portal(portal.start, portal.end)
#         self.portals.append(new_portal)
#         self.add_room(portal)
#         self.add_room(new_portal)
#
#     def add_room(self, portal):
#         # print("add room")
#         room1 = portal.start
#         room2 = portal.end
#         new_x = (room1.x + room2.x) / 2
#         new_y = (room1.y + room2.y) / 2
#         new_room = Room("", new_x, new_y)
#         room2 = portal.end
#         portal.set_end(new_room)
#         new_portal = Portal(new_room, room2)
#         self.rooms.append(new_room)
#         self.portals.append(new_portal)
#
#     def add_offshoot(self, room):
#         # print("add offshoot")
#         room1 = Room("", room.x, room.y, offset=True)
#         self.rooms.append(room1)
#         self.portals.append(Portal(room, room1))
#
#     def add_loop(self, room):
#         # print("add loop")
#         room1 = Room("", room.x, room.y, offset=True)
#         new_x = (room1.x + room.x) / 2
#         new_y = (room1.y + room.y) / 2
#         room2 = Room("", new_x, new_y, offset=True)
#         new_x = (room1.x + room.x) / 2
#         new_y = (room1.y + room.y) / 2
#         room3 = Room("", new_x, new_y, offset=True)
#
#         self.rooms.append(room1)
#         self.rooms.append(room2)
#         self.rooms.append(room3)
#
#         self.portals.append(Portal(room, room2))
#         self.portals.append(Portal(room, room3))
#         self.portals.append(Portal(room2, room1))
#         self.portals.append(Portal(room3, room1))
#
#     def augment(self):
#         if self.count_rooms() < 7:
#             choice = rnd.choices([0, 1, 2, 3], [10, 90, 0, 0])[0]
#         elif self.count_rooms() < 10:
#             choice = rnd.choices([0, 1, 2, 3], [50, 30, 20, 0])[0]
#         elif self.count_rooms() < 20:
#             choice = rnd.choices([0, 1, 2, 3], [30, 30, 40, 0])[0]
#         elif self.count_rooms() < 80:
#             choice = rnd.choices([0, 1, 2, 3], [35, 40, 25, 5])[0]
#         else:
#             choice = rnd.choices([0, 1, 2, 3], [30, 25, 30, 15])[0]
#         if choice == 0:
#             p = rnd.randint(0, len(self.portals) - 1)
#             self.split_portal(self.portals[p])
#         elif choice == 1:
#             p = rnd.randint(0, len(self.portals) - 1)
#             self.add_room(self.portals[p])
#         elif choice == 2:
#             r = rnd.randint(0, len(self.rooms) - 1)
#             if self.rooms[r].name != 'Finish':
#                 self.add_offshoot(self.rooms[r])
#         elif choice == 3:
#             r = rnd.randint(0, len(self.rooms) - 1)
#             if self.rooms[r].name != 'Finish':
#                 self.add_loop(self.rooms[r])
#
#     def fix_overlap(self, clip: bool):
#         overlaps = []
#         for portal in self.portals:
#             if portal.overlapping:
#                 overlaps.append(portal)
#         if len(overlaps) == 0:
#             return
#
#         p = rnd.randint(0, len(overlaps) - 1)
#         portal = overlaps[p]
#         if clip:
#             portal.unhook()
#             self.portals.remove(portal)
#         else:
#             self.add_room(portal)


if __name__ == "__main__":
    main()
