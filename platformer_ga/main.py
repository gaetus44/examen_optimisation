import pygame
import sys
import random
import math
import os

# --- IMPORTATION DES RÈGLES ---
# Le fichier rules.py doit être dans le même dossier
from rules import Level, Creature, TILE_SIZE, WHITE, BLACK, GRAY, RED, GREEN, BLUE

# --- CONFIGURATION VISUELLE ---
TRANSPARENT_BLUE = (50, 100, 250, 50)

# --- PARAMÈTRES GÉNÉTIQUES ---
POPULATION_SIZE = 50
MUTATION_RATE = 0.05
ELITISM_COUNT = 5


# --- HELPER: CRÉATION FICHIER LEVEL ---
def create_default_level_if_missing(filename="level1.txt"):
    if not os.path.exists(filename):
        content = """60
20 15
1 1
18 8
5 0
5 1
5 2
5 3
8 14
8 13
8 12
12 0
12 1
12 2
12 3
12 4
14 7
15 7
16 7
"""
        with open(filename, "w") as f:
            f.write(content)
        print(f"Fichier '{filename}' créé par défaut.")


# --- ALGORITHME GÉNÉTIQUE ---

class DNA:
    """Représente les instructions d'une créature (Cerveau)."""

    def __init__(self, length):
        self.length = length
        # Une liste d'entiers aléatoires entre 0 et 100
        self.genes = [random.randint(0, 100) for _ in range(length)]

    def mutate(self, rate):
        """
        Applique une mutation standard + une chance de 'décalage temporel' (Shift).
        """
        # 1. Mutation Standard (Modification ponctuelle)
        # Permet de découvrir de nouveaux mouvements (Exploration)
        for i in range(self.length):
            if random.random() < rate:
                self.genes[i] = random.randint(0, 100)

        # 2. Mutation de Décalage (SHIFT) - Timing
        # Permet de recaler une bonne séquence (Exploitation/Correction)
        # 10% de chance qu'un décalage arrive sur cet individu
        if random.random() < 0.10:

            if random.random() < 0.5:
                # --- SHIFT GAUCHE (Agir plus tôt) ---
                # On enlève la première action (le début)
                # On ajoute une action aléatoire à la fin pour combler le vide
                self.genes.pop(0)
                self.genes.append(random.randint(0, 100))
            else:
                # --- SHIFT DROITE (Agir plus tard) ---
                # On enlève la dernière action (la fin)
                # On insère une action aléatoire au début pour repousser le reste
                self.genes.pop()  # Retire le dernier
                self.genes.insert(0, random.randint(0, 100))


class Agent:
    """Lien entre l'algo génétique et la créature (les règles)"""

    def __init__(self, level, dna=None):
        self.creature = Creature(level)
        self.dna = dna if dna else DNA(level.n_ticks)
        self.fitness = 0
        self.finished = False

    def update(self):
        if self.creature.reached_goal or self.creature.is_dead:
            self.finished = True
            return

        if self.creature.tick >= self.creature.level.n_ticks:
            self.finished = True
            return

        # 1. Obtenir les mouvements possibles VIA rules.py
        moves = self.creature.get_possible_moves()

        if not moves:
            self.creature.is_dead = True
            self.finished = True
            return

        # 2. Utiliser l'ADN pour choisir un mouvement
        gene_val = self.dna.genes[self.creature.tick]
        # Modulo permet de toujours avoir un index valide
        chosen_move = moves[gene_val % len(moves)]

        # 3. Appliquer le mouvement via la méthode de rules.py
        self.creature.apply_move(chosen_move)

    def calculate_fitness(self):
        # Distance euclidienne vers l'objectif
        d_x = self.creature.x - self.creature.level.goal_pos[0]
        d_y = self.creature.y - self.creature.level.goal_pos[1]
        dist = math.sqrt(d_x ** 2 + d_y ** 2)

        if self.creature.reached_goal:
            # Récompense énorme pour la victoire + bonus de vitesse
            score = 10000 + (self.creature.level.n_ticks - self.creature.tick) * 50
        else:
            # Plus on est près, meilleur est le score
            # Formule : 100 / (distance + 1)
            score = 100.0 / (dist + 1.0)

            # Bonus pour la progression en X (encourage à avancer vers la droite)
            score += self.creature.x * 2

            # Pénalité de mort
            if self.creature.is_dead:
                score *= 0.1

        self.fitness = score
        return score


# --- FONCTIONS D'ÉVOLUTION (ROULETTE EXPONENTIELLE) ---

def get_parent_roulette(agents, weights, total_weight):
    """
    Sélectionne un parent en utilisant les poids (fitness exponentiel).
    """
    pick = random.uniform(0, total_weight)
    current = 0

    for agent, weight in zip(agents, weights):
        current += weight
        if current > pick:
            return agent

    return agents[-1]  # Sécurité


def evolve(agents, level):
    # 1. Évaluation
    scores = [a.calculate_fitness() for a in agents]

    # 2. Tri (nécessaire pour l'élitisme)
    sorted_agents = sorted(agents, key=lambda x: x.fitness, reverse=True)
    best_agent_prev_gen = sorted_agents[0]

    new_agents = []

    # Elitisme (On garde les meilleurs absolus) ELITISM_COUNT = 5
    for i in range(ELITISM_COUNT):
        new_dna = DNA(level.n_ticks)
        new_dna.genes = sorted_agents[i].dna.genes[:]
        new_agents.append(Agent(level, new_dna))

    # --- ROULETTE EXPONENTIELLE ---
    # On élève le fitness exposant 4 pour favoriser les meilleurs
    EXPONENT = 4

    weights = [a.fitness ** EXPONENT for a in sorted_agents]
    total_weight = sum(weights)

    # 3. Reproduction
    while len(new_agents) < POPULATION_SIZE:
        # Sélection
        parent_a = get_parent_roulette(sorted_agents, weights, total_weight)
        parent_b = get_parent_roulette(sorted_agents, weights, total_weight)

        while parent_a == parent_b:
            parent_a = get_parent_roulette(sorted_agents, weights, total_weight)
            parent_b = get_parent_roulette(sorted_agents, weights, total_weight)

        child_dna = DNA(level.n_ticks)

        # Crossover (Point unique) point de coupure au hasard
        midpoint = random.randint(0, level.n_ticks - 1)
        # Recolle (Début de A + Fin de B)
        child_dna.genes = parent_a.dna.genes[:midpoint] + parent_b.dna.genes[midpoint:]

        # Mutation (Standard + Shift)
        child_dna.mutate(MUTATION_RATE)

        #Ajouter l'enfant a la nouvelle population
        new_agents.append(Agent(level, child_dna))

    return new_agents, best_agent_prev_gen


# --- VISUALISATION ---

def to_screen(gx, gy, h):
    return gx * TILE_SIZE, (h - 1 - gy) * TILE_SIZE


def draw_level_static(screen, level):
    for y in range(level.height):
        for x in range(level.width):
            sx, sy = to_screen(x, y, level.height)
            rect = pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)

            pygame.draw.rect(screen, (30, 30, 30), rect, 1)  # Grille

            if level.is_obstacle(x, y):
                pygame.draw.rect(screen, GRAY, rect)
            elif (x, y) == level.start_pos:
                pygame.draw.rect(screen, (30, 80, 30), rect)
            elif (x, y) == level.goal_pos:
                pygame.draw.rect(screen, (100, 30, 30), rect)


def draw_agents(screen, agents, level, best_agent=None):
    surface = pygame.Surface((level.width * TILE_SIZE, level.height * TILE_SIZE), pygame.SRCALPHA)

    for agent in agents:
        if agent == best_agent: continue

        cx, cy = to_screen(agent.creature.x, agent.creature.y, level.height)

        color = TRANSPARENT_BLUE
        if agent.creature.reached_goal:
            color = (50, 250, 50, 100)
        elif agent.creature.is_dead:
            color = (50, 50, 50, 30)

        pygame.draw.circle(surface, color, (cx + TILE_SIZE // 2, cy + TILE_SIZE // 2), TILE_SIZE // 4)

    screen.blit(surface, (0, 0))

    if best_agent:
        cx, cy = to_screen(best_agent.creature.x, best_agent.creature.y, level.height)
        pygame.draw.circle(screen, GREEN, (cx + TILE_SIZE // 2, cy + TILE_SIZE // 2), TILE_SIZE // 3)

        if len(best_agent.creature.path) > 1:
            pts = []
            for (px, py) in best_agent.creature.path:
                sx, sy = to_screen(px, py, level.height)
                pts.append((sx + TILE_SIZE // 2, sy + TILE_SIZE // 2))
            pygame.draw.lines(screen, GREEN, False, pts, 3)


def main():
    create_default_level_if_missing("level1.txt")

    # Chargement
    lvl = Level("level1.txt")

    pygame.init()
    screen = pygame.display.set_mode((lvl.width * TILE_SIZE, lvl.height * TILE_SIZE))
    pygame.display.set_caption("Platformer GA")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    # Initialisation Population
    agents = [Agent(lvl) for _ in range(POPULATION_SIZE)]
    generation = 1
    champion = None

    fps = 60
    running = True
    while running:
        # --- LOGIQUE ---
        all_finished = True

        for agent in agents:
            if not agent.finished:
                agent.update()
                all_finished = False

        if all_finished:
            agents, champion = evolve(agents, lvl)
            generation += 1
            print(f"Gen {generation} | Best Fit: {champion.fitness:.1f} | Goal: {champion.creature.reached_goal}")

        # --- EVENEMENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    fps = 300
                if event.key == pygame.K_DOWN:
                    fps = 60
                if event.key == pygame.K_SPACE:
                    fps = 5

        # --- DESSIN ---
        screen.fill(BLACK)
        draw_level_static(screen, lvl)
        draw_agents(screen, agents, lvl, champion)

        # UI
        info_txt = f"Gen: {generation} | Alive: {sum(1 for a in agents if not a.finished)}/{POPULATION_SIZE}"
        surf = font.render(info_txt, True, WHITE)
        screen.blit(surf, (10, 10))

        spd_txt = font.render(f"FPS: {fps}", True, GRAY)
        screen.blit(spd_txt, (10, 30))

        if champion and champion.creature.reached_goal:
            win_surf = font.render(f"SOLVED IN GEN {generation - 1}!", True, GREEN)
            screen.blit(win_surf, (10, 50))

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


if __name__ == "__main__":
    main()