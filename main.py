
from copy import deepcopy as copy
import termios
import random
import shutil
import time
import sys

CLEAR = "\x1b[2J\x1b[H"
COLOR = "\x1b[{0}m"
POSITION = "\x1b[{1};{0}H"

def setup_terminal(fd):
    orig = termios.tcgetattr(fd)
    modded = copy(orig)

    modded[6][termios.VTIME] = 0
    modded[6][termios.VMIN] = 0
    modded[3] = ~(termios.ICANON | termios.ECHO)

    termios.tcsetattr(fd, termios.TCSANOW, modded)
    return orig

def reset_terminal(fdr, fdw, orig):
    fdw.write("\x1b[0m\x1b[?25h" + CLEAR)
    termios.tcsetattr(fdr, termios.TCSADRAIN, orig)
    fdr.flush()
    fdw.flush()

def move_snake(snake, new_pos, extend = False):
    cv = []
    if not extend:
        cv.append((snake[0], 0))
        snake.pop(0)
    if len(snake) > 0:
        cv.append((snake[-1], 1))
    cv.append((new_pos, 2))
    snake.append(new_pos)
    return cv

def find_apple_position(snake, width, height):
    while True:
        apple = (random.randrange(0, width), random.randrange(0, height))
        for i in snake:
            if i == apple:
                break
        else:
            return apple

def get_dir(dir, exception):
    match sys.stdin.read(1):
        case "w":
            if dir != 2 or exception:
                return 0, 0
        case "d":
            if dir != 3 or exception:
                return 1, 0
        case "s":
            if dir != 0 or exception:
                return 2, 0
        case "a":
            if dir != 1 or exception:
                return 3, 0
        case "p":
            return dir, 1
        case "q":
            return dir, 2
        case "i":
            return dir, 3
        case "m":
            return dir, 4
        case "r":
            return dir, 5
        case "c":
            return dir, 6
    return dir, 0

def get_next_pos(snake, apple, width, height, direction):
    
    x = snake[-1][0]
    y = snake[-1][1]

    nx = x + (1 if direction == 1 else (-1 if direction == 3 else 0))
    ny = y + (1 if direction == 2 else (-1 if direction == 0 else 0))

    # if nx >= width: nx = 0
    # if ny >= height: ny = 0
    # if nx < 0: nx = width - 1
    # if ny < 0: ny = height - 1
    if (nx >= width) or (ny >= height) or (nx < 0) or (ny < 0):
        return (x, y), False, False

    if (nx, ny) in snake: return (x, y), False, False

    return (nx, ny), (nx, ny) == apple, True

def get_computer(dir, snake, apple, width, height, solution):
    # return get_computer_a(dir, snake, apple, width, height), []
    if len(solution) < 1:
        solution = get_computer_b(dir, snake, apple, width, height)
    dir = solution.pop(0)
    return dir, solution

def get_computer_b(dir, snake, apple, width, height):
    
    tree = {"": snake}
    complexities = {"": 0}

    while True:
        current = ""
        b = -1
        for k,v in complexities.items():
            if (v < b) or (b == -1):
                current = k
                b = v
        if b == -1:
            return 0, []

        if len(current) < 1: current_raw = []
        else: current_raw = [int(i) for i in current.split(":")]
        current_snake = tree.pop(current)
        complexities.pop(current)

        for i in range(4):
            next_pos, found, moved = get_next_pos(current_snake, apple, width, height, i)
            if not moved: continue
            next_node = copy(current_raw)
            next_node.append(i)
            if found: return [int(j) for j in next_node]
            next_node = ":".join([str(j) for j in next_node])
            next_snake = copy(current_snake)
            next_snake.pop(0)
            next_snake.append(next_pos)
            tree[next_node] = next_snake
            complexities[next_node] = heuristic(next_pos, apple, current_snake, (width, height))

def get_diff(a, b, m):
    c = abs(a - b)
    cd = abs(((a + (m >> 1)) % m) - ((b + (m >> 1)) % m))
    return c if c < cd else cd

def dist(p, t, s):
    return abs(p[1] - t[1]) + abs(p[0] - t[0])
    return get_diff(p[0], t[0], s[0]) + get_diff(p[1], t[1], s[1])

def heuristic(p, t, snake, size):
    md = dist(p, t, size)

    penalty = 0
    snake = copy(snake)

    for i in range(len(snake) - 1, -1, -1):
        if (not is_blocking(snake[i], p, t)): snake.pop(i) # or (dist(p, snake[i], size) > (len(snake) - i - 1)): snake.pop(i)
    
    penalty += 0 if is_solvable((0, 0), (abs(t[0] - p[0]), abs(t[1] - p[1])), [(abs(i[0] - p[0]), abs(i[1] - p[1])) for i in snake], (abs(p[0] - t[0]), abs(p[1] - t[1]))) else 2

    return md + penalty

def is_solvable(p, t, b, size):
    v = [p]
    pl = 0
    while pl != len(v):
        pl = len(v)
        for i in v:
            if i == t: return True
            for j in [(i[0] + 1, i[1]), (i[0], i[1] + 1), (i[0] - 1, i[1]), (i[0], i[1] - 1)]:
                if (j[0] < 0) or (j[1] < 0) or (j[0] >= size[0]) or (j[1] >= size[1]) or (j in b) or (j in v):
                    continue
                v.append(j)
    return False


def is_blocking(b, p, t):
    return (p[0] <= t[0] <= b[0]) or (p[1] <= t[1] <= b[1]) or (p[0] >= t[0] >= b[0]) or (p[1] >= t[1] >= b[1])


def get_computer_a(dir, snake, apple, width, height):
    x = snake[-1][0]
    y = snake[-1][1]
    tx = apple[0]
    ty = apple[1]


    match dir % 2:
        case 0:
            if x > tx:
                dir = 3
            elif x < tx:
                dir = 1
        case 1:
            if y > ty:
                dir = 0
            elif y < ty:
                dir = 2
    
    dirs = [0, 1, 2, 3]
    while not get_next_pos(snake, apple, width, height, dir)[2]:
        if len(dirs) > 0:
            dir = dirs.pop(random.randrange(len(dirs)))
        else:
            dir = 0
            break

    return dir

def main():
    orig = setup_terminal(sys.stdin)
    
    width, height = shutil.get_terminal_size()
    width >>= 1

    colors = [100, 42, 44, 41]

    snake = []

    frame = CLEAR + COLOR.format(colors[0]) + height * width * "  " + "\x1b[?25l"

    cv = move_snake(snake, (width >> 1, height >> 1), True)


    speed = 10
    maxfps = -1
    direction = 1

    di = {}
    ad = lambda x, p: [di.__setitem__((p[0] + i, p[1]), x[i]) for i in range(len(x))]
    ispeed = 1 / speed
    imaxfps = 1 / maxfps
    stime = 0
    mt = 0
    screen = {}
    cn = []
    ft = 0
    rfps = 0
    rfpsd = 0
    fpsd = 0
    generation = 0
    cmem = []
    computer_plays = True
    apple = find_apple_position(snake, width, height)
    cv.append((apple, 3))
    while True:
        etime = time.time()
        dt = etime - stime
        stime = etime
        fps = 1 / dt
        pts = imaxfps - dt
        if pts > 0: time.sleep(pts)
        mt += dt
        ft += dt
        rfps += 1


        for i in cv:
            screen[i[0]] = i[1]

            pos = (i[0][0] << 1, i[0][1])
            frame += POSITION.format(pos[0] + 1, pos[1] + 1) + COLOR.format(colors[i[1]]) + COLOR.format("35;1")

            f = " "
            l = " "


            if pos in di:
                f = di.pop(pos)
            if (pos[0] + 1, pos[1]) in di:
                l = di.pop((pos[0] + 1, pos[1]))
            
            frame += f + l

        for i,v in di.items():
            for j in range(len(cn) - 1, -1, -1):
                if i == cn[j]: cn.pop(j)
            pos = (i[0] >> 1, i[1])
            color = colors[screen.get(pos, 0)]
            frame += POSITION.format(i[0] + 1, i[1] + 1) + COLOR.format(color) + COLOR.format("35;1") + v

        for i in cn:
            pos = (i[0] >> 1, i[1])
            color = colors[screen.get(pos, 0)]
            frame += POSITION.format(i[0] + 1, i[1] + 1) + COLOR.format(color) + " "

        sys.stdout.write(frame)
        sys.stdout.flush()
        frame = ""
        cn = list(di.keys())
        di = {}

        ad("RFPS: " + str(rfps), (0, 0))
        ad("FPS: " + str(int(fps)), (0, 1))
        ad("RFPSD: " + str(rfpsd), (0, 2))
        ad("FPSD: " + str(int(fpsd)), (0, 3))
        ad("Apple: " + str(apple), (0, 4))
        ad("Generation: " + str(generation), (0, 5))
        pos_copy = copy(snake[-1])
        # ad(str(direction) * 2, (pos_copy[0] << 1, pos_copy[1]))
        pos_copy, _, _ = get_next_pos([pos_copy], apple, width, height, direction)
        for i in range(len(cmem)):
            ad((" " if len(str(i + 1)) < 2 else "") + str(i + 1), (pos_copy[0] << 1, pos_copy[1]))
            pos_copy, _, _ = get_next_pos([pos_copy], apple, width, height, cmem[i])

        if ft >= 1:
            ft = 0
            rfpsd = rfps
            rfps = 0
            fpsd = fps

        cv = []
        if (mt >= ispeed) or (ispeed == -1):
            generation += 1
            
            new_pos, found, moved = get_next_pos(snake, apple, width, height, direction)
            
            if moved:
                cv = move_snake(snake, new_pos, found)
                
                if found:
                    apple = find_apple_position(snake, width, height)
                    sys.stdout.write(POSITION.format(apple[0] * 2 + 1, apple[1] + 1) + COLOR.format(46) + "  ")
                    sys.stdout.flush()
                    cv.append((apple, 3))

                mt = 0
            else:
                break
        
            hdir, special = get_dir(direction, len(snake) < 2)
            if special == 1:
                while sys.stdin.read(1) != "r": pass
            elif special == 2:
                break
            elif special == 3:
                speed += 1
            elif special == 4:
                speed -= 1
            elif special == 5:
                speed = 10
            elif special == 6:
                computer_plays = not computer_plays
            if 3 <= special <= 5:
                ispeed = 1 / speed
            cdir, cmem = get_computer(direction, snake, apple, width, height, cmem)
            direction = [hdir, cdir][computer_plays]
            if not computer_plays: cmem = []

    reset_terminal(sys.stdin, sys.stdout, orig)
    print(f"You survived for {generation} generations.")

if __name__ == "__main__": main()
