import numpy as np
import random
import pygame as pg
from pygame.locals import *
from scipy.spatial import cKDTree
import pickle
import time
from Organism import *

'''
Setting some simulation variables
'''

SCREEN_WIDTH, SCREEN_HEIGHT = 800,600
ENV_WIDTH, ENV_HEIGHT = 100, 80

BACK_COLOR = (100, 100, 100)

BLOCK_SIZE = 5  # Pixel size

ENV_WIDTH_PX = BLOCK_SIZE * ENV_WIDTH
ENV_HEIGHT_PX = BLOCK_SIZE * ENV_HEIGHT
ENV_TOP_LEFT_CORNER = (SCREEN_WIDTH // 2 - ENV_WIDTH_PX // 2, SCREEN_HEIGHT // 2 - ENV_HEIGHT_PX // 2)

'''
Setting some environment variables
'''
MINUTES_PER_DAY = 100
DAY_ENERGY = 25*MINUTES_PER_DAY
REMOVE_EXCESS_FOOD = True

INITIAL_POPULATION_COMPOSITION = [
    (2, (1, 3, 5)),
    (1, (2, 1.5, 5)),
    (1, (1, 2, 10))
]

FOOD_INITIAL_AMOUNT = 50
FOOD_DECREASE = True
FOOD_DECREASE_RATE = 0.1 # %
FOOD_DECREASE_TIME = 10  # days

screen = None

'''
Draw a square representing an Object
'''
def draw(color, x, y, factor = 1):
    pg.draw.rect(screen, color, (x, y, factor*BLOCK_SIZE, factor*BLOCK_SIZE))

'''
Draw the environment and its contents
'''
def draw_environment(screen, env):
        screen.fill(BACK_COLOR)
        pg.draw.rect(screen, (0,0,0), (ENV_TOP_LEFT_CORNER[0], ENV_TOP_LEFT_CORNER[1],
                                               ENV_WIDTH_PX, ENV_HEIGHT_PX))
        draw_xy, color = np.array([0,0]), None
        for o in env:
            color = (0,255,0) if not isinstance(o, Organism) else o.color
            draw_xy = o.position*BLOCK_SIZE + ENV_TOP_LEFT_CORNER
            factor = 1 if not isinstance(o, Organism) else o.size
            draw(color, draw_xy[0], draw_xy[1], factor)

'''
Initialize the initial composition of organisms
'''
def init_organisms(n, attr):
    organisms = []
    for _ in range(n):
        o = Organism(attr[0], attr[1], attr[2], ENV_WIDTH, ENV_HEIGHT)
        o.energy = DAY_ENERGY
        organisms.append(o)
    return organisms

'''
Kill all Organisms which couldn't find enough food
or couldn't reach the border in time
'''
def kill(env):
    kill_counter = 0

    for o in env.copy():
        if not isinstance(o, Organism): continue
        dist_to_border, _, _ = o.closest_border()
        if (o.energy <= 0) or (dist_to_border > 1):
            env.remove(o)
            kill_counter += 1
    #print("{} organisms killed".format(kill_counter))

'''
Make Organisms which found two pieces of food reproduce
and supply each Organism with new energy for the next day
'''
def sleep_and_reproduce(env):
    babies = []
    for o in env:
        if not isinstance(o, Organism): continue
        if o.food_found >= 2:
            babies.append(o.reproduce(DAY_ENERGY))
        o.food_found = 0
        o.energy = DAY_ENERGY
        o.state = State.FIND_FOOD
    env.extend(babies)
    #print("{} babies born".format(len(babies)))

'''
This is what happens in a minute in the enviroment
'''
def do_one_step(env, m):
    minutes_left = MINUTES_PER_DAY - m

    attributes = np.array([o.attributes() for o in env if isinstance(o, Organism)])
    max_attr = np.max(attributes)

    env_copy = env.copy()

	# Create an efficient kD-tree for faster range calculations
    coords = np.array([o.position for o in env])
    indexKD = cKDTree(coords, leafsize=16)

	# Make every Organism do 1 step
    for o in env:
        if not isinstance(o, Organism): continue
        o.walk(env, indexKD)

	# Recalculate the kD-tree
    coords = np.array([o.position for o in env])
    indexKD = cKDTree(coords, leafsize=16)

	# Make every Organism eat if it's close enough to food
    for o in env_copy:
        if not isinstance(o, Organism): continue
        close_obj_idx = indexKD.query_ball_point(o.position, o.sense*o.SENSE_FACTOR)

        for obj in np.array(env_copy)[close_obj_idx]:
            if obj == o: continue
            if not np.linalg.norm(obj.position-o.position) <= 0.01: continue
            if not isinstance(obj, Organism) or o.can_eat(obj):
                if obj in env:
                    env.remove(obj)
                    o.food_found += 1
                    dist_to_border, _, _ = o.closest_border()
                    if (o.food_found > 1) or (dist_to_border/o.speed >= minutes_left-5):
                        o.state = State.GO_BACK
                    break

		# Periodic boundaries
        pos = o.get_coordinates()%np.array([ENV_WIDTH+1, ENV_HEIGHT+1])
        o.position = pos
        o.color = o.attributes()*255/max_attr

'''
Code to run the simulation
'''
def run_simulation(num_days=None, display=True):
    if not display and not num_days:
        num_days = 100
    if display:
        global screen
        pg.init()
        screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.update()

    raw_data = canvas = None
    env = []
    n_food = FOOD_INITIAL_AMOUNT
    for f in range(n_food):
        x, y = random.randrange(1,ENV_WIDTH-1), random.randrange(1,ENV_HEIGHT-1)
        env.append(Object(np.array([x, y])))

    for n, org in INITIAL_POPULATION_COMPOSITION:
        env.extend(init_organisms(n, org))

    # Main game loop
    run = True

    time_keeper = {"day":0, "minute":0}
    attributes = np.array([o.attributes() for o in env if isinstance(o, Organism)])
    stats = {"population":[len(attributes)], "attributes":[attributes], "food": [n_food]}
    while run:
        if display:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    run = False

        if len([o for o in env if isinstance(o, Organism)]) == 0:
            run = False
            continue

        if num_days and time_keeper["day"] >= num_days:
            run = False
            continue

        # do one simulation step
        do_one_step(env, time_keeper["minute"])
        time_keeper["minute"] += 1
        if time_keeper["minute"] >= MINUTES_PER_DAY:
            print("Day {} is over.".format(time_keeper["day"]))
            time_keeper["minute"] = 0
            time_keeper["day"] += 1
            kill(env)
            sleep_and_reproduce(env)

            if FOOD_DECREASE and time_keeper["day"]%FOOD_DECREASE_TIME == 0:
                n_food = int(n_food*(1-FOOD_DECREASE_RATE))
                print("decreased food to {}".format(n_food))
            if REMOVE_EXCESS_FOOD:
                for i, o in enumerate(env):
                    if not isinstance(o, Organism):
                        env.pop(i)
            for f in range(n_food):
                x, y = random.randrange(1,ENV_WIDTH-1), random.randrange(1,ENV_HEIGHT-1)
                env.append(Object(np.array([x, y])))

            if display:
                pg.time.wait(500)

            attributes = np.array([o.attributes() for o in env if isinstance(o, Organism)])

            ## Save stats
            stats["population"].append(len(attributes))
            stats["food"].append(n_food)
            if len(stats["attributes"]) > 0:
                stats["attributes"].append(attributes)

        if display:
            draw_environment(screen, env)
            pg.display.update()
            pg.time.wait(10)
            pg.event.pump()

    pg.quit()
    return stats

stats = run_simulation(display=True)

with open('stats_{}.pickle'.format(time.time()), 'wb') as handle:
    pickle.dump(stats, handle, protocol=pickle.HIGHEST_PROTOCOL)
