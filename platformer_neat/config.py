# config.py
import math

# --- NEAT CONFIGURATION ---
POPULATION_SIZE = 50       # Taille raisonnable pour une convergence pas trop lente
MAX_GENERATIONS = 100       # Nombre de générations
INPUTS = 4                  # PosX, PosY, DistX_Goal, DistY_Goal
OUTPUTS = 9                 # Les 9 actions possibles définies dans rules.py

# Probabilités de mutation
PROB_MUTATE_WEIGHT = 0.8
PROB_ADD_CONNECTION = 0.1   # Un peu réduit pour éviter des réseaux trop lourds trop vite
PROB_ADD_NODE = 0.05

# Poids
WEIGHT_RANDOM_STRENGTH = 2.5

def sigmoid(x):
    try:
        return 1 / (1 + math.exp(-4.9 * x))
    except OverflowError:
        return 0 if x < 0 else 1