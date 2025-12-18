# config.py
import math

# --- NEAT CONFIGURATION ---
POPULATION_SIZE = 100  # Augmenté pour plus de diversité
MAX_GENERATIONS = 200
INPUTS = 9             # PosX, PosY, DX, DY, BIAS + 4 Capteurs (H, B, G, D)
OUTPUTS = 9

# Probabilités de mutation
PROB_MUTATE_WEIGHT = 0.8
PROB_ADD_CONNECTION = 0.1
PROB_ADD_NODE = 0.03
WEIGHT_RANDOM_STRENGTH = 2.5

# --- SPÉCIATION ---
DISTANCE_THRESHOLD = 2.0 # Augmenté pour gérer plus d'entrées
COEFF_EXCESS = 1.0
COEFF_DISJOINT = 1.0
COEFF_WEIGHT = 0.5
STAGNATION_LIMIT = 20

# --- MUTATION INTER-ESPÈCES ---
PROB_INTERSPECIES_MATE = 0.02

def sigmoid(x):
    try:
        return 1 / (1 + math.exp(-4.9 * x))
    except OverflowError:
        return 0 if x < 0 else 1