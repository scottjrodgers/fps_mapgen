# This is a sample Python script.
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

# import numpy as np
import pygame
from pygame import display, draw, Color
from typing import *
import random as rnd


MAX_ROOMS = 250
ENDPOINT_DIST = 800
PUSH_DIST = 40
PUSH_POWER = 2
PUSH_KD = 1e-3
PULL_DIST = 20
PULL_POWER = 2
PULL_KS = 5e-3
BOUNDARY_DIST = 30
BOUNDARY_POWER = 1.2
BOUNDARY_KD = 0.1
UPDATE_SCALE = 2.0


def main():
    pygame.init()

    screen = display.set_mode((1280, 720))
    cx = 1280 / 2
    cy = 720 / 2

    clock = pygame.time.Clock()
    level = Level()
    counter = 0

    while True:
        # Process player inputs.
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    level.augment()
                if event.key == pygame.K_RETURN:
                    level.jog()
                if event.key == pygame.K_BACKSPACE:
                    level = Level()

        counter += 1
        if counter > 10 and level.count_rooms() < MAX_ROOMS:
            counter = 0
            level.augment()

        # Push Rooms apart
        n = level.count_rooms()
        for i in range(n - 1):
            for j in range(i + 1, n):
                target_dist = PUSH_DIST
                names = [level.rooms[i].name, level.rooms[j].name]
                if "Start" in names and "Finish" in names:
                    target_dist = ENDPOINT_DIST
                level.rooms[i].push(level.rooms[j], target_dist, PUSH_POWER, PUSH_KD)

        num_p = level.count_portals()
        for p in range(num_p):
            level.portals[p].overlapping = False
        for p in range(num_p):
            portal = level.portals[p]
            portal.pull(PULL_DIST, PULL_POWER, PULL_KS)
            if p < num_p - 1:
                for q in range(p + 1, num_p):
                    if portal.check_overlap(level.portals[q]):
                        portal.overlapping = True
                        level.portals[q].overlapping = True

        for room in level.rooms:
            room.check_boundaries(1280, 720, BOUNDARY_DIST, BOUNDARY_POWER, BOUNDARY_KD)
            room.update()

        screen.fill("black")  # Fill the display with a solid color

        # Render the graphics here.
        for portal in level.portals:
            xs = portal.start.x + cx
            ys = portal.start.y + cy
            xe = portal.end.x + cx
            ye = portal.end.y + cy
            color = Color("0x66BBFF")
            if portal.overlapping:
                color = Color("0xDD5555")
            draw.line(screen, color, (xs, ys), (xe, ye), width=1)

        for room in level.rooms:
            x = room.x + cx
            y = room.y + cy
            radius = 3
            if room.name == 'Start':
                color = "yellow"
                radius = 5
            elif room.name == 'Finish':
                color = 'green'
                radius = 5
            else:
                color = 'white'
            draw.circle(screen, color, (x, y), radius)

        display.flip()  # Refresh on-screen display
        clock.tick(60)         # wait until next frame (at 60 FPS)


# ======================================================
#                       ROOM
# ======================================================
class Room:
    def __init__(self, name="", x=0, y=0, offset=False):
        self.name = name
        self.id = -1
        self.portals: List[Portal] = []
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        if name not in ("Start", "Finish") or offset:
            self.x += rnd.random() * 25 - rnd.random() * 25
            self.y += rnd.random() * 25 - rnd.random() * 25

    def add_portal(self, p):
        assert p not in self.portals
        self.portals.append(p)

    def update(self):
        damping = 0.2
        self.x += self.dx * UPDATE_SCALE
        self.y += self.dy * UPDATE_SCALE
        self.dx *= damping
        self.dy *= damping

    def direction(self, other):
        dst = self.dist(other)
        return (other.x - self.x) / dst, (other.y - self.y) / dst

    def dist(self, other):
        x1 = self.x
        y1 = self.y
        x2 = other.x
        y2 = other.y
        d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        if d < 1:
            d = 1
        return d

    def spring(self, other, target_length, ks):
        s_limit = 80
        length = self.dist(other)
        d_len = target_length - length
        d_len = d_len / abs(d_len) ** 0.5
        if d_len > s_limit:
            d_len = s_limit
        elif d_len < -s_limit:
            d_len = -s_limit
        dx, dy = self.direction(other)
        self.dx -= dx * d_len * ks
        self.dy -= dy * d_len * ks
        other.dx += dx * d_len * ks
        other.dy += dy * d_len * ks

    def push(self, other, target_dist, power=3, kd=1e-3):
        length = self.dist(other)
        p_factor = min([100 * (target_dist / max([length, 1])) ** power, 500.0])
        dx, dy = self.direction(other)
        self.dx -= dx * p_factor * kd
        self.dy -= dy * p_factor * kd
        other.dx += dx * p_factor * kd
        other.dy += dy * p_factor * kd

    def pull(self, other, target_dist, power=3, kd=1e-3):
        length = self.dist(other)
        p_factor = min([100 * (max([length, 1]) / target_dist) ** power, 500.0])
        dx, dy = self.direction(other)
        self.dx += dx * p_factor * kd
        self.dy += dy * p_factor * kd
        other.dx -= dx * p_factor * kd
        other.dy -= dy * p_factor * kd

    def check_boundaries(self, width, height, target_dist, power, kd):
        half_width = width / 2
        half_height = height / 2
        if self.x > 0:
            h_length = half_width - self.x
            h_dir = -1
        else:
            h_length = self.x + half_width
            h_dir = 1
        if self.y > 0:
            v_length = half_height - self.y
            v_dir = -1
        else:
            v_length = self.y + half_height
            v_dir = 1

        h_factor = min([10 * (target_dist / max([h_length, 0.1])) ** power, 100.0])
        v_factor = min([10 * (target_dist / max([v_length, 0.1])) ** power, 100.0])
        self.dx += h_dir * h_factor * kd
        self.dy += v_dir * v_factor * kd


# ======================================================
#                       PORTAL
# ======================================================
class Portal:
    def __init__(self, a, b):
        self.start = None
        self.end = None
        self.set_start(a)
        self.set_end(b)
        self.overlapping = False

    def set_start(self, room):
        if self.start is not None:
            self.start.portals.delete(self)
        self.start = room
        room.add_portal(self)

    def set_end(self, room):
        if self.end is not None:
            self.end.portals.delete(self)
        self.end = room
        room.add_portal(self)

    def pull(self, target_length, power=3, ks=1e-3):
        self.start.pull(self.end, target_length, power, ks)

    def check_overlap(self, other) -> bool:
        if self.start == other.start or self.start == other.end:
            return False
        if self.end == other.start or self.end == other.end:
            return False

        x1 = self.start.x
        x2 = self.end.x
        y1 = self.start.y
        y2 = self.end.y
        x3 = other.start.x
        x4 = other.end.x
        y3 = other.start.y
        y4 = other.end.y

        # Bounding Box rejection tests
        if min([x1, x2]) > max([x3, x4]) or min([x3, x4]) > max([x1, x2]):
            return False
        if min([y1, y2]) > max([y3, y4]) or min([y3, y4]) > max([y1, y2]):
            return False

        # Straddle Test
        z1 = (x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)
        z2 = (x4 - x1) * (y2 - y1) - (y4 - y1) * (x2 - x1)

        # if signs of z1 and z2 are different or either zero, the segments straddle
        if z1 * z2 <= 0:
            # when segments straddle and BB's overlap, it's an intersection
            return True

        # reject by default
        return False


# ======================================================
#                       LEVEL
# ======================================================
class Level:
    def __init__(self):
        self.rooms: List[Room] = []
        self.portals: List[Portal] = []
        self.first: Room = Room("Start", -100, 0)
        self.last: Room = Room("Finish", 100, 0)
        self.rooms.append(self.first)
        self.rooms.append(self.last)
        self.portals.append(Portal(self.first, self.last))

    def count_portals(self):
        return len(self.portals)

    def count_rooms(self):
        return len(self.rooms)

    def balance(self):
        n = 0
        x_sum = 0
        y_sum = 0
        for room in self.rooms:
            n += 1
            x_sum += room.x
            y_sum += room.y

        x_avg = x_sum / n
        y_avg = y_sum / n

        for room in self.rooms:
            room.x -= x_avg
            room.y -= y_avg

    def jog(self):
        for portal in self.portals:
            if portal.overlapping:
                for room in [portal.start, portal.end]:
                    if rnd.random() < 0.55:
                        room.x += rnd.normalvariate(0, 25)
                        room.y += rnd.normalvariate(0, 25)
        self.balance()

    def split_portal(self, portal):
        print("split_portal")
        new_portal = Portal(portal.start, portal.end)
        self.portals.append(new_portal)
        self.add_room(portal)
        self.add_room(new_portal)

    def add_room(self, portal):
        print("add room")
        room1 = portal.start
        room2 = portal.end
        new_x = (room1.x + room2.x) / 2
        new_y = (room1.y + room2.y) / 2
        new_room = Room("", new_x, new_y)
        room2 = portal.end
        portal.end = new_room
        new_portal = Portal(room2, new_room)
        self.rooms.append(new_room)
        self.portals.append(new_portal)

    def add_offshoot(self, room):
        print("add offshoot")
        room1 = Room("", room.x, room.y, offset=True)
        self.rooms.append(room1)
        self.portals.append(Portal(room, room1))

    def add_loop(self, room):
        print("add loop")
        room1 = Room("", room.x, room.y, offset=True)
        new_x = (room1.x + room.x) / 2
        new_y = (room1.y + room.y) / 2
        room2 = Room("", new_x, new_y, offset=True)
        new_x = (room1.x + room.x) / 2
        new_y = (room1.y + room.y) / 2
        room3 = Room("", new_x, new_y, offset=True)

        self.rooms.append(room1)
        self.rooms.append(room2)
        self.rooms.append(room3)

        self.portals.append(Portal(room, room2))
        self.portals.append(Portal(room, room3))
        self.portals.append(Portal(room2, room1))
        self.portals.append(Portal(room3, room1))

    def augment(self):
        if self.count_rooms() < 7:
            choice = rnd.choices(range(4), [10, 90, 0, 0])[0]
        elif self.count_rooms() < 10:
            choice = rnd.choices(range(4), [20, 50, 30, 0])[0]
        elif self.count_rooms() < 40:
            choice = rnd.choices(range(4), [60, 30, 7, 3])[0]
        elif self.count_rooms() < 80:
            choice = rnd.choices(range(4), [35, 40, 15, 10])[0]
        else:
            choice = rnd.choices(range(4), [30, 25, 30, 15])[0]
        if choice == 0:
            p = rnd.randint(0, len(self.portals) - 1)
            self.split_portal(self.portals[p])
        elif choice == 1:
            p = rnd.randint(0, len(self.portals) - 1)
            self.add_room(self.portals[p])
        elif choice == 2:
            r = rnd.randint(0, len(self.rooms) - 1)
            if self.rooms[r].name != 'Finish':
                self.add_offshoot(self.rooms[r])
        elif choice == 3:
            r = rnd.randint(0, len(self.rooms) - 1)
            if self.rooms[r].name != 'Finish':
                self.add_loop(self.rooms[r])


if __name__ == "__main__":
    main()
