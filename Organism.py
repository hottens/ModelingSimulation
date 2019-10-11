from scipy.spatial import distance
import enum
import copy
import numpy as np
import random


'''
Every object in the environment has a position
'''
class Object:
    def __init__(self, position):
        self.position = position

'''
Possible states of Organisms
'''
class State(enum.Enum):
    FIND_FOOD = 0
    GO_BACK = 1

'''
Organism class inherits from a regular Object
'''
class Organism(Object):
    PREDATOR_PREY_RATIO = 1.6
    SENSE_FACTOR = 1
    color = (255, 255, 255)
    food_found = 0
    state = State.FIND_FOOD
    energy = 0

    '''
    Initialize an Organism with its size, speed and sense.
    It also needs to know the boundaries of its environment.
    Upon initialization, a random location at the borders of this environment is
    generated. Also, a random direction is generated in which the Organism will
    move.
    '''
    def __init__(self, size, speed, sense, max_w, max_h):
        # Organism starts at a border
        if random.random() > 0.5:
            x = random.uniform(0, max_w-1)
            y = 0
            if random.random() > 0.5:
                y = max_h-1
        else:
            y = random.uniform(0, max_h-1)
            x = 0
            if random.random() > 0.5:
                x = max_w-1
        super().__init__(np.array([x, y]))

        self.size = size
        self.speed = speed
        self.sense = sense

        self.max_w = max_w
        self.max_h = max_h

        # Create a normalized direction vector
        direction = [np.random.uniform(-1,1), np.random.uniform(-1,1)]
        self.direction = direction/np.linalg.norm(direction)

    '''
    Calculates the energy cost for every time step
    '''
    def energy_cost(self):
        return ((self.size**3)*self.speed**2)+self.sense

    '''
    Returns an Organisms position
    '''
    def get_coordinates(self):
        return self.position

    '''
    Returns a possibly mutated copy of the Organism
    '''
    def reproduce(self, energy):
        offspring = copy.deepcopy(self)
        mutation_chance = 0.1

        offspring.size  += (mutation_chance>random.random())*random.uniform(0.1, 0.5)*random.choice([-1,1])
        offspring.speed += (mutation_chance>random.random())*random.uniform(0.1, 0.5)*random.choice([-1,1])
        offspring.sense += (mutation_chance>random.random())*random.uniform(0.1, 0.5)*random.choice([-1,1])

        offspring.energy = energy
        offspring.state = State.FIND_FOOD

        return offspring

    '''
    Returns the Organisms size, speed and sense as a vector
    '''
    def attributes(self):
        return np.array([self.size, self.speed, self.sense])

    '''
	Returns the distance to the closest border, together with its coordinates
	'''
    def closest_border(self):
        borders = [[self.position[0], 0], [self.max_w, self.position[1]], [self.position[0], self.max_h],[0, self.position[1]]]
        distances = distance.cdist([self.get_coordinates()], borders, 'euclidean')[0]
        closest_idx = np.argmin(distances)

        return distances[closest_idx], borders[closest_idx][0], borders[closest_idx][1]

    '''
	Returns whether or not an Organism can eat another
	'''
    def can_eat(self, other):
        return self.size>= self.PREDATOR_PREY_RATIO*other.size

    '''
	Performs a step in a chosen or random direction
	'''
    def walk(self, env, indexKD):
        distances = []
        step_size = self.speed
        direction = self.direction

        food = []
        close_predators = []

		# Get all the objects the Organism can perceive
        close_obj_idx = indexKD.query_ball_point(self.position, self.sense * self.SENSE_FACTOR)
        for obj in np.array(env)[close_obj_idx]:
			# Its me, do nothing
            if obj == self: continue

			# I see something i can eat!
            if (not isinstance(obj, Organism)) or self.can_eat(obj):
                food.append(obj.position)

			# I see something that can eat me!
            elif obj.can_eat(self):
                close_predators.append(obj.position)

		# Run away from predators
        if len(close_predators) > 0:
            pr_distances = distance.cdist([self.position], close_predators, 'euclidean')[0]
            pr_idx = np.argmin(pr_distances)

            d = (close_predators[pr_idx] + self.position)*-1
            norm = np.linalg.norm(d)
            if norm == 0:
                return
            direction = d/norm
		# Otherwise, go to the nearest border when I'm ready
        elif self.state == State.GO_BACK:
            dist, x, y = self.closest_border()
            step_size = dist if abs(dist) < step_size else step_size

            d = np.array([x, y]) - self.position
            norm = np.linalg.norm(d)
            if norm == 0:
                return
            direction = d/norm
		# Or go towards food if visible
        elif len(food) > 0:
            distances = distance.cdist([self.position], food, 'euclidean')[0]
            closest_idx = np.argmin(distances)
            step_size = distances[closest_idx] if abs(distances[closest_idx]) < step_size else step_size

            d = food[closest_idx] - self.position
            norm = np.linalg.norm(d)
            if norm == 0:
                return
            direction = d/norm
		# Default is a step in a modified direction
        else:
            # x2=cosβx1−sinβy1,
			# y2=sinβx1+cosβy1

			# Pick a random angle within a range
			# and adapt the Organisms direction
            r = random.uniform(-.5, .5)
            direction = np.array([np.cos(r)*direction[0] - np.sin(r)*direction[1],
                                  np.sin(r)*direction[0] + np.cos(r)*direction[1]])
            self.direction = direction/np.linalg.norm(direction)

		# Take the step if sufficient energy is available,
		# then subtract the energy after a step is taken
        if self.energy >= self.energy_cost():
            self.position += step_size*direction

        self.energy -= self.energy_cost()
