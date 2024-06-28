# This is a sample Python script.
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import numpy as np
import pygame
from pygame import display, draw, Color
import random as rnd

WIDTH = 1200
HEIGHT = 720
center = np.array([WIDTH / 2, HEIGHT / 2])
ROOM_LIMIT = 120
MAX_ROOMS = ROOM_LIMIT - 10
PULL_DIST = 40
PULL_POWER = 1
PULL_KS = 1e-3
PUSH_CONSTANT = 5e4
MAX_PUSH = 1200
UPDATE_SCALE = 1

portals = np.zeros((ROOM_LIMIT, ROOM_LIMIT), dtype=np.int8)
position = np.zeros((ROOM_LIMIT, 2))
velocity = np.zeros((ROOM_LIMIT, 2))
spacing = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
x_dir = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
y_dir = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
t1 = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
tr = np.zeros((1, ROOM_LIMIT))
tc = np.zeros((ROOM_LIMIT, 1))
mask = np.zeros((ROOM_LIMIT, 1))
n_rooms = 0
middle = np.zeros(2)
xy_scale = 1.0


def init():
    global position, portals, n_rooms, mask, velocity, spacing, x_dir, y_dir, t1, tr, tc, middle, xy_scale
    portals = np.zeros((ROOM_LIMIT, ROOM_LIMIT), dtype=np.int8)
    position = np.zeros((ROOM_LIMIT, 2))
    velocity = np.zeros((ROOM_LIMIT, 2))
    spacing = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
    x_dir = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
    y_dir = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
    t1 = np.zeros((ROOM_LIMIT, ROOM_LIMIT))
    tr = np.zeros((1, ROOM_LIMIT))
    tc = np.zeros((ROOM_LIMIT, 1))
    mask = np.zeros((ROOM_LIMIT, 1))
    middle = np.zeros(2)
    xy_scale = 1.0
    n_rooms = 2
    position[0, :] = [-100, 0]
    position[1, :] = [100, 0]
    portals[0, 1] = 1
    portals[1, 0] = 1
    mask[0:2, 0] = 1


def add_room(a=-1, b=-1) -> int:
    global n_rooms, position
    if a >= 0 and b >= 0:
        position[n_rooms, :] = (position[a, :] + position[b, :]) / 2.0
    else:
        position[n_rooms, :] = [0, 0]

    position[n_rooms, 0] += (rnd.randint(0, 1) * 2 - 1) * rnd.randint(10, 20)
    position[n_rooms, 1] += (rnd.randint(0, 1) * 2 - 1) * rnd.randint(10, 20)
    mask[n_rooms] = 1
    n_rooms += 1
    return n_rooms - 1


def add_portal(a, b):
    global portals
    portals[a, b] = 1
    portals[b, a] = 1


def remove_portal(a, b):
    global portals
    portals[a, b] = 0
    portals[b, a] = 0


def portals_for_room(i):
    return portals[i, :]


def distance(a: int, b: int) -> float:
    global spacing
    return np.maximum(spacing[a, b], 1.0)


def compute_spacing_and_direction():
    global position, spacing, x_dir, y_dir, tr, tc, n_rooms
    tc[:, 0] = position[:, 0]
    tr[0, :] = position[:, 0]
    x_dir[:, :] = tr - tc
    spacing[:, :] = x_dir * x_dir
    tc[:, 0] = position[:, 1]
    tr[0, :] = position[:, 1]
    y_dir[:, :] = tr - tc
    spacing[:, :] += y_dir * y_dir
    spacing[:, :] = np.maximum(np.sqrt(spacing), 1)
    x_dir[:, :] /= spacing[:, :]
    y_dir[:, :] /= spacing[:, :]
    # spacing[:, n_rooms:] = 1e5
    # spacing[n_rooms:, :] = 1e5


def push():
    global spacing, x_dir, y_dir, n_rooms

    velocity[:, 0] -= PUSH_CONSTANT * (x_dir / np.power(spacing, 2.5)).sum(axis=1)
    velocity[:, 1] -= PUSH_CONSTANT * (y_dir / np.power(spacing, 2.5)).sum(axis=1)
    # temp1 = PUSH_CONSTANT * (x_dir / np.power(spacing, 2)).sum(axis=1)
    # temp2 = PUSH_CONSTANT * (y_dir / np.power(spacing, 2)).sum(axis=1)
    # temp1 = np.minimum(np.maximum(temp1, -25), 25)
    # temp2 = np.minimum(np.maximum(temp2, -25), 25)
    # if np.abs(temp1).max() > 50:
    #     print("Push issue 1")
    # if np.abs(temp1).max() > 50:
    #     print("Push issue 2")
    # velocity[:, 0] -= temp1
    # velocity[:, 1] -= temp2


def pull():
    global portals, spacing, x_dir, y_dir, t1, n_rooms
    t1[:, :] = portals * PULL_KS * np.power(spacing[:, :] / PULL_DIST, PULL_POWER)
    velocity[:, 0] += (t1 * x_dir).sum(axis=1)
    velocity[:, 1] += (t1 * y_dir).sum(axis=1)


def lerp(a, b, x):
    return a + (b - a) * x


def center_and_scale():
    global position, middle, xy_scale
    EPS = 1e-3
    max_pos = position[0:n_rooms, :].max(axis=0)
    min_pos = position[0:n_rooms, :].min(axis=0)
    diff = max_pos - min_pos
    middle = (max_pos + min_pos) / 2.0
    xy_scale = lerp(xy_scale,
                    np.minimum(np.minimum(1.0, (WIDTH - 100.0) / np.maximum(diff[0], EPS)),
                               np.minimum(1.0, (HEIGHT - 100.0) / np.maximum(diff[1], EPS))),
                    0.01)
    position = position - middle
    position[:, 0] *= xy_scale
    position[:, 1] *= xy_scale


def update(scale=1.0):
    global velocity, position, spacing
    compute_spacing_and_direction()
    push()
    pull()
    damping = 0.05
    velocity *= mask
    velocity = np.minimum(np.maximum(velocity, -20), 20)
    if np.abs(velocity).max() > 50:
        print("Eeek!")
    velocity *= scale
    position += velocity
    velocity *= damping
    center_and_scale()


def split_portal(a, b):
    """
    Old: A <--> B
    New: A <--> C <--> B
         A <--> D <--> B
    :param a: from room
    :param b: to room
    :return: void
    """
    global n_rooms, portals
    assert portals[a, b] == 1 and portals[b, a] == 1
    c = add_room(a, b)
    d = add_room(a, b)
    remove_portal(a, b)
    add_portal(a, c)
    add_portal(c, b)
    add_portal(a, d)
    add_portal(d, b)


def extend_portal(a, b):
    """
    Old: A <--> B
    New: A <--> C <--> B
    :param a: from room
    :param b: to room
    :return: void
    """
    global n_rooms, portals
    assert portals[a, b] == 1 and portals[b, a] == 1
    c = add_room(a, b)
    remove_portal(a, b)
    add_portal(a, c)
    add_portal(c, b)


def add_offshoot(a):
    """
    Old: A
    New: A <--> C
    :param a: from room
    :return: void
    """
    global n_rooms, portals
    c = add_room(a, a)
    add_portal(a, c)


def add_loop(a):
    """
    Old: A
    New: A <--> C <--> B
         A <--> D <--> B
    :param a: from room
    :return: void
    """
    global n_rooms, portals
    b = add_room(a, a)
    c = add_room(a, b)
    d = add_room(a, b)
    add_portal(a, c)
    add_portal(c, b)
    add_portal(a, d)
    add_portal(d, b)


def augment():
    global n_rooms, portals
    if n_rooms < 8:
        choice = rnd.choices(range(4), [10, 90, 0, 0])[0]
    elif n_rooms < 30:
        choice = rnd.choices(range(4), [75, 15, 7, 3])[0]
    elif n_rooms < 80:
        choice = rnd.choices(range(4), [35, 35, 20, 10])[0]
    else:
        choice = rnd.choices(range(4), [25, 25, 25, 25])[0]

    if choice == 0:
        port_list = np.where(portals)
        p = rnd.randint(0, port_list[0].shape[0] - 1)
        split_portal(port_list[0][p], port_list[1][p])
    elif choice == 1:
        port_list = np.where(portals)
        p = rnd.randint(0, port_list[0].shape[0] - 1)
        extend_portal(port_list[0][p], port_list[1][p])
    elif choice == 2:
        if n_rooms > 2:
            r = rnd.randint(2, n_rooms - 1)
            add_offshoot(r)
    elif choice == 3:
        if n_rooms > 2:
            r = rnd.randint(2, n_rooms - 1)
            add_loop(r)


def main():
    global position, portals, velocity, n_rooms, center
    pygame.init()
    init()

    screen = display.set_mode((1280, 720))

    clock = pygame.time.Clock()
    counter = 0

    while True:
        # Process player inputs.
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    augment()
                if event.key == pygame.K_RETURN:
                    pass
                if event.key == pygame.K_BACKSPACE:
                    init()

        counter += 1
        if counter > 25 and n_rooms < MAX_ROOMS:
            counter = 0
            augment()

        update(scale=UPDATE_SCALE)

        #
        # num_p = level.count_portals()
        # for p in range(num_p):
        #     portal = level.portals[p]
        #     portal.pull(20, 1, 5e-3)
        #     if p < num_p - 1:
        #         for q in range(p + 1, num_p):
        #             if portal.check_overlap(level.portals[q]):
        #                 portal.overlapping = True
        #                 level.portals[q].overlapping = True
        # for room in level.rooms:
        #     room.check_boundaries(1280, 720, 50, 1.2, 0.1)
        #     room.update()

        screen.fill("black")  # Fill the display with a solid color

        # Render the graphics here.
        port_list = np.where(portals)
        for i in range(port_list[0].shape[0]):
            a = port_list[0][i]
            b = port_list[1][i]
            if a < b:
                ps = position[a, :] + center
                pf = position[b, :] + center
                color = Color("0x66BBFF")
                draw.line(screen, color, ps, pf, width=2)

        for room in range(n_rooms):
            pos = position[room, :] + center
            if room == 0:
                color = "yellow"
            elif room == 1:
                color = 'green'
            else:
                color = 'white'
            draw.circle(screen, color, pos, 6)

        display.flip()  # Refresh on-screen display
        clock.tick(60)         # wait until next frame (at 60 FPS)


# # ======================================================
# #                       ROOM
# # ======================================================
# class Room:
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
#             self.start.portals.delete(self)
#         self.start = room
#         room.add_portal(self)
#
#     def set_end(self, room):
#         if self.end is not None:
#             self.end.portals.delete(self)
#         self.end = room
#         room.add_portal(self)
#
#     def pull(self, target_length, power=3, ks=1e-3):
#         self.start.pull(self.end, target_length, power, ks)
#
#     def check_overlap(self, other) -> bool:
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
#         self.first: Room = Room("Start", -100, 0)
#         self.last: Room = Room("Finish", 100, 0)
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
#         for room in self.rooms:
#             d = rnd.random() * rnd.random() * 400
#             room.x += rnd.random() * d - rnd.random() * d
#             room.y += rnd.random() * d - rnd.random() * d
#         self.balance()
#
#     # def scramble(self, width, height):
#     #     for room in self.rooms:
#     #         room.x = rnd.random() * width
#     #         room.y = rnd.random() * height
#     #     self.balance()
#
#     def split_portal(self, portal):
#         # split one portal into two parallel portals
#         new_portal = Portal(portal.start, portal.end)
#         self.portals.append(new_portal)
#         self.add_room(portal)
#         self.add_room(new_portal)
#
#     def add_room(self, portal):
#         # adds a room in the middle of a current portal connection
#         room1 = portal.start
#         room2 = portal.end
#         new_x = (room1.x + room2.x) / 2
#         new_y = (room1.y + room2.y) / 2
#         new_room = Room("", new_x, new_y)
#         room2 = portal.end
#         portal.end = new_room
#         new_portal = Portal(room2, new_room)
#         self.rooms.append(new_room)
#         self.portals.append(new_portal)
#
#     def add_offshoot(self, room):
#         # from a room, add a portal to a new room, that's a dead end
#         new_room = Room("", room.x, room.y, offset=True)
#         new_portal = Portal(room, new_room)
#         self.rooms.append(new_room)
#         self.portals.append(new_portal)
#
#     def add_loop(self, room):
#         # from a room, add two portals to a room -- one there and one back.
#         new_room = Room("", room.x, room.y, offset=True)
#         new_portal = Portal(room, new_room)
#         new_portal2 = Portal(room, new_room)
#         self.rooms.append(new_room)
#         self.portals.append(new_portal)
#         self.portals.append(new_portal2)
#
#     def augment(self):
#         if self.count_rooms() < 8:
#             choice = rnd.choices(range(4), [10, 90, 0, 0])[0]
#         elif self.count_rooms() < 30:
#             choice = rnd.choices(range(4), [60, 30, 7, 3])[0]
#         elif self.count_rooms() < 80:
#             choice = rnd.choices(range(4), [20, 40, 30, 10])[0]
#         else:
#             choice = rnd.choices(range(4), [25, 25, 25, 25])[0]
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


if __name__ == "__main__":
    main()
