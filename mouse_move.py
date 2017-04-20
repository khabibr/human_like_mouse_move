#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import time
import subprocess

import math
import random
import numpy as np
from scipy.misc import comb

DEFAULT_MIN_SPEED = 60  # [1..100]
DEFAULT_MAX_SPEED = 90  # [1..100]

DEFAULT_MAX_X = 639
DEFAULT_MAX_Y = 479

DEFAULT_MIN_PAUSE = 0.5
DEFAULT_MAX_PAUSE = 4

USING_STR = (
    '\nUsage:\n'
    '{0} [COORDINATES] [PARAMS] [KEYS]\n'
    '\n'
    'COORDINATES: x1:y1 x2:y2 ... xM:yM\n'
    '\tMove cursor sequentially along the COORDINATES\n'
    '\tendless random movements if no COORDINATES\n'

    'PARAMS: param1:val1 param2:val2 ... paramN:valN\n'
    '\tSet of params:\n'
    '\tcount - count of random movement\n'
    '\tmin_pause, max_pause - pause between movements (seconds)\n'
    '\tmin_speed, max_speed - speed of movements (1..100)\n'
    '\ttop_left, bottom_right - movements range (top_left:x:y or bottom_right:x:y)\n'
    'KEYS:\n'
    '\t--debug_show_curve : Show mouse path curve (matplotlib figure)\n'
    '\t--autopilot : Use autopilot mouse move method (default)\n'
    '\t  (https://developer.ubuntu.com/api/autopilot/python/1.5.0/autopilot.input)\n'
    '\t--xdotool : Use xdotool mouse move method\n'
    'Example:\n'
    '\t{0} 100:100 500:100 300:250 100:100 max_speed:50\n'
    '\t{0} count:10 count:10 max_pause:1 top_left:0:0 bottom_right:639:199\n'
)
# MOUSE METHODS
"""
    XDOTOOL method
    Linux universal tool.
    (medium speed. a lot of process calls).
"""


class xdotool(object):

    def get_mouse_location(self):
        spitted = subprocess.Popen(
            "xdotool getmouselocation",
            shell=True,
            stdout=subprocess.PIPE
        ).stdout.read().decode().split()
        if len(spitted) > 1 and 'x:' in spitted[0] and 'y:' in spitted[1]:
            x = int(spitted[0].partition(':')[2])
            y = int(spitted[1].partition(':')[2])
        else:
            x, y = 0, 0

        return x, y

    def move_mouse(self, x_pos, y_pos, speed):
        subprocess.call(["xdotool", "mousemove", str(
            x_pos), str(y_pos)])  # ignore speed


"""
    AUTOPILOT method
    https://developer.ubuntu.com/api/autopilot/python/1.5.0/autopilot.input/
    (high speed, great velocity, low resource consumption).
"""


class autopilot(object):

    def __init__(self):
        from autopilot.input import Mouse  # apt-get install python3-autopilot
        self.mouse = Mouse.create()

    def get_mouse_location(self):
        return self.mouse.position()

    def move_mouse(self, x_pos, y_pos, speed):
        # time_between_events [0.02 (slowest) ..  0.0001 (fastest)]
        self.mouse.move(x_pos, y_pos, animate=False,
                        time_between_events=(2 - 0.02 * speed) / 99)
        if speed < 90:
            # additional random slow down
            time.sleep(random.uniform(0.001, 0.01))

# BEZIER CURVE


def bernstein_poly(i, n, t):
    """
        The Bernstein polynomial of n, i as a function of t
    """
    return comb(n, i) * (t**(n - i)) * (1 - t)**i


def bezier_curve(points, dots_cnt):
    """
       Given a set of control points, return the
       bezier curve defined by the control points.

       points should be a list of lists, or list of tuples
       such as [ [1,1],
                 [2,3],
                 [4,5], ..[Xn, Yn] ]
        dots_cnt is the number of steps
        See http://processingjs.nihongoresources.com/bezierinfo/
    """
    nPoints = len(points)
    xPoints = np.array([p[0] for p in points])
    yPoints = np.array([p[1] for p in points])
    t = np.linspace(0.0, 1.0, dots_cnt)
    polynomial_array = np.array(
        [bernstein_poly(i, nPoints - 1, t) for i in range(0, nPoints)])
    xvals = np.dot(xPoints, polynomial_array)
    yvals = np.dot(yPoints, polynomial_array)
    return xvals, yvals

# HUMAN LIKE MOVE


class human_like_mouse_move(object):

    def __init__(self,
                 mouse_method,
                 top_left_corner,
                 bottom_right_corner,
                 min_spd,
                 max_spd,
                 show_curve):

        self.mouse_method = mouse_method
        self.min_spd = min_spd
        self.max_spd = max_spd
        self.show_curve = show_curve
        self.get_resolution()
        if top_left_corner:
            self.min_x, self.min_y = top_left_corner
        if bottom_right_corner:
            self.max_x, self.max_y = bottom_right_corner

    def rand_coords(self):
        """ Infinite random coordinates generator"""
        while True:
            yield (
                random.randrange(self.min_x, self.max_x),
                random.randrange(self.min_y, self.max_y)
            )

    def get_resolution(self):
        spitted = subprocess.Popen(
            "xrandr | grep '*' | head -1",
            shell=True,
            stdout=subprocess.PIPE
        ).stdout.read().decode().split()
        self.min_x, self.min_y = 0, 0
        if spitted and 'x' in spitted[0]:
            x, y = spitted[0].split('x')
            self.res_x, self.res_y = int(x), int(y)
        else:
            self.res_x, self.res_y = DEFAULT_MAX_X, DEFAULT_MAX_Y
        self.max_x, self.max_y = self.res_x, self.res_y

    def get_move_curve(self, d_to):
        d_from = self.mouse_method.get_mouse_location()
        x_dist = d_to[0] - d_from[0]
        y_dist = d_to[1] - d_from[1]
        dist = math.hypot(x_dist, y_dist)

        # first approx
        deviation = dist * \
            random.uniform(0.1, 0.3) * \
            (random.randint(0, 1) * 2 - 1)  # -1 or +1
        middle = ((d_from[0] + d_to[0]) / 2,
                  (d_from[1] + d_to[1]) / 2 + deviation)
        points = [d_to, middle, d_from]
        dots_cnt = int(self.dots_per_100 * dist / (100 * 5))
        if dots_cnt <= 3:
            dots_cnt = 4
        xvals, yvals = bezier_curve(points, dots_cnt)
        xvals = [int(p) for p in xvals[1:-1]]
        yvals = yvals[1:-1]

        # second approx
        delta_y = y_dist / dots_cnt
        if self.show_curve:
            points = [d_from]
        rev_points = [d_to]  # reveresed points

        if y_dist == 0:
            coef = 1
        else:
            coef = abs(x_dist / y_dist)
            if coef > 1:
                coef = 1
            elif coef < 0.1:
                coef = 0.1

        for i, xval in enumerate(xvals):
            deviation = delta_y * coef * \
                random.uniform(0.5, 5) * \
                (random.randint(0, 1) * 2 - 1)  # -1 or +1
            if self.show_curve:
                points.append((xval, int(yvals[i] + deviation)))
            rev_points.insert(1, (xval, int(yvals[i] + deviation)))
        points.append(d_to)
        rev_points.append(d_from)

        if self.show_curve:
            xpoints = [p[0] for p in points]
            ypoints = [p[1] for p in points]
            from matplotlib import pyplot as plt
            ax = plt.gca()
            ax.set_xlim([0, self.res_x])
            ax.set_ylim([0, self.res_y])
            ax.invert_yaxis()
            # dots and text
            plt.plot(xpoints, ypoints, "ro")
            for nr in range(len(points)):
                plt.text(points[nr][0], points[nr][1], nr)

        dots_cnt = int(self.dots_per_100 * dist / (100))
        xvals, yvals = bezier_curve(rev_points, dots_cnt)  # rev_points
        if self.show_curve:
            plt.plot(xvals, yvals)
            plt.show()
        return xvals, yvals, dots_cnt

    def move_to(self, point_to):
        speed = random.uniform(self.min_spd, self.max_spd)
        # dots_per_100 comfort diapason 5 .. 25
        self.dots_per_100 = round((2495 - 20 * speed) / 99)
        try:
            xvals, yvals, dots_cnt = self.get_move_curve(point_to)
        except TypeError:
            return

        for idx, xval in enumerate(xvals):
            self.mouse_method.move_mouse(xval, yvals[idx], speed)

    def pause_between_moves(self):
        time.sleep(random.uniform(min_pause, max_pause))


def signal_handler(signal, frame):
    print(' Cancelled...')
    exit(0)


# MAIN
if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl-C signal handler

    # parse_params
    move_cnt = 0
    top_left_corner = None
    bottom_right_corner = None
    min_spd = DEFAULT_MIN_SPEED
    max_spd = DEFAULT_MAX_SPEED
    min_pause = DEFAULT_MIN_PAUSE
    max_pause = DEFAULT_MAX_PAUSE
    coords = []
    show_curve = False
    use_xdotool = False
    if len(sys.argv) > 1:
        try:
            for arg in sys.argv[1:]:
                if arg == '--debug_show_curve':
                    show_curve = True
                    continue
                elif arg == '--autopilot':
                    continue
                elif arg == '--xdotool':
                    use_xdotool = True
                    continue
                elif ':' not in arg:
                    raise Exception(arg)
                par_name, par_val, *par_extra = arg.split(':')
                if par_name == 'count':
                    move_cnt = int(par_val)
                elif par_name == 'min_pause':
                    min_pause = float(par_val)
                    if max_pause < min_pause:
                        max_pause = min_pause
                elif par_name == 'max_pause':
                    max_pause = float(par_val)
                    if min_pause > max_pause:
                        min_pause = max_pause
                elif par_name == 'min_speed':
                    min_spd = int(par_val)
                    if min_spd < 1:
                        min_spd = 1
                    elif min_spd > 100:
                        min_spd = 100
                    if max_spd < min_spd:
                        max_spd = min_spd
                elif par_name == 'max_speed':
                    max_spd = int(par_val)
                    if max_spd < 1:
                        max_spd = 1
                    elif max_spd > 100:
                        max_spd = 100
                    if min_spd > max_spd:
                        min_spd = max_spd
                elif par_name == 'top_left':
                    top_left_corner = (int(par_val), int(par_extra[0]))
                elif par_name == 'bottom_right':
                    bottom_right_corner = (int(par_val), int(par_extra[0]))
                else:  # just coord
                    coords.append((int(par_name), int(par_val)))
        except Exception:
            print(USING_STR.format(sys.argv[0]))
            sys.exit()

    if use_xdotool:
        method = xdotool()
    else:
        method = autopilot()

    human_like = human_like_mouse_move(
        method,
        top_left_corner,
        bottom_right_corner,
        min_spd,
        max_spd,
        show_curve)
    if not coords:
        coords = human_like.rand_coords()
    cnt = 0
    for dot in coords:
        human_like.move_to(dot)
        cnt += 1
        if move_cnt and move_cnt == cnt:
            break
        human_like.pause_between_moves()
