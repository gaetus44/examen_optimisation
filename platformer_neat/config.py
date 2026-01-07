# config.py
import math

# --- NEAT CONFIGURATION ---
POPULATION_SIZE = 60
MAX_GENERATIONS = 150
INPUTS = 5                  # PosX, PosY, DistX_Goal, DistY_Goal, BIAIS (Fixe à 1.0)
OUTPUTS = 9

# Probabilités de mutation
PROB_MUTATE_WEIGHT = 0.8
PROB_ADD_CONNECTION = 0.15
PROB_ADD_NODE = 0.05
WEIGHT_RANDOM_STRENGTH = 2.5

# --- SPÉCIATION ---
DISTANCE_THRESHOLD = 1.2 # si < 1.2 => mis dans l'espèce sinon espece suivante
COEFF_EXCESS = 1.0
COEFF_DISJOINT = 1.0
COEFF_WEIGHT = 0.4
STAGNATION_LIMIT = 15

# --- MUTATION INTER-ESPÈCES ---
PROB_INTERSPECIES_MATE = 0.02

def sigmoid(x):
    try:
        return 1 / (1 + math.exp(-4.9 * x))
    except OverflowError:
        return 0 if x < 0 else 1