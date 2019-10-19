from Simulation import *
import threading

def thread_function(name, population, display = False):
    print("Starting experiment {}".format(name))
    sim = Simulation(name, population=population, display = False)
    sim.start(500)

# 10 x perform experiment with same population
population = [
    (50, (1, 1, 1))
]
name = "same_pop50_"
for i in range(0,10):
    x = threading.Thread(target=thread_function, args=(name+str(i),population))
    x.start()

population = [
    (1, (1, 1, 1))
]
name = "same_pop1_"
for i in range(0,10):
    x = threading.Thread(target=thread_function, args=(name+str(i),population))
    x.start()

# do a simulation with different populations
populations = [
    [(1, (3, 1, 1))],
    [(1, (1, 3, 1))],
    [(1, (1, 1, 5))],
    [(50, (3, 1, 1))],
    [(50, (1, 3, 1))],
    [(50, (1, 1, 5))],
    [(10, (3, 3, 1)), (40, (1, 1, 5))],
    [(40, (3, 3, 1)), (10, (1, 1, 5))],
    [(25, (3, 3, 1)), (25, (1, 1, 5))],
]
names = ["1_size", "1_speed", "1_sense", "50_size", "50_speed", "50_sense", "10-large_40-vision", "40-large_10-vision", "25-large_25-vision"]

for idx, pop in enumerate(populations):
    name = names[idx]
    for i in range(0,3):
        x = threading.Thread(target=thread_function, args=("diff_pop"+name+"_"+str(i),population))
        x.start()


# experiment with dropping food supply
