import pygame
import sys
import random
import math
import os

# --- CONFIGURATION ---
TILE_SIZE = 60  # Réduit un peu pour mieux voir sur les petits écrans
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)
RED = (200, 50, 50)  # Goal
GREEN = (50, 200, 50)  # Start / Best Creature
BLUE = (50, 100, 250)  # Creature Standard
CYAN = (0, 255, 255)  # Choix possibles
ORANGE = (255, 165, 0)  # Mouvement forcé

# --- PARAMETRES GENETIQUES ---
POPULATION_SIZE = 50
MUTATION_RATE = 0.02
ELITISM_COUNT = 5  # Nombre de meilleurs conservés tels quels


# --- HELPER: CREATION FICHIER LEVEL SI MANQUANT ---
def create_default_level_if_missing(filename="level.txt"):
    if not os.path.exists(filename):
        content = """60
20 15
1 1
18 8
5 0 5 1 5 2 5 3
8 14 8 13 8 12
12 0 12 1 12 2 12 3 12 4
14 7 15 7 16 7
"""
        with open(filename, "w") as f:
            f.write(content)
        print(f"Fichier '{filename}' créé par défaut.")


# --- CLASSES (LOGIQUE DE MOUVEMENT INCHANGEE) ---

class Level:
    def __init__(self, filepath):
        self.obstacles = set()
        self.n_ticks = 0
        self.width = 0
        self.height = 0
        self.start_pos = (0, 0)
        self.goal_pos = (0, 0)
        self.load_from_file(filepath)

    def load_from_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                lines = [l.strip() for l in f if l.strip()]

            self.n_ticks = int(lines[0])
            self.width, self.height = map(int, lines[1].split())
            self.start_pos = tuple(map(int, lines[2].split()))
            self.goal_pos = tuple(map(int, lines[3].split()))

            for line in lines[4:]:
                parts = list(map(int, line.split()))
                # Lecture par paires (x y)
                if len(parts) >= 2:
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):
                            self.obstacles.add((parts[i], parts[i + 1]))

        except Exception as e:
            print(f"Erreur lecture fichier: {e}")
            sys.exit()

    def is_obstacle(self, x, y):
        return (x, y) in self.obstacles

    def is_out_of_bounds(self, x, y):
        return x < 0 or x >= self.width or y < 0 or y >= self.height

    def is_valid_position(self, x, y):
        return not self.is_out_of_bounds(x, y) and not self.is_obstacle(x, y)


class Creature:
    def __init__(self, level):
        self.level = level
        self.x, self.y = level.start_pos
        self.vx = 0
        self.is_dead = False
        self.reached_goal = False
        self.tick = 0
        self.path = [(self.x, self.y)]

    def is_in_air(self):
        if self.y > 0:
            return not self.level.is_obstacle(self.x, self.y - 1)
        return False

    def get_possible_moves(self):
        """
        Retourne une liste de dictionnaires :
        [{'x': int, 'y': int, 'vx': int, 'type': 'ground'|'air'}]
        """
        moves = []

        if self.is_dead or self.reached_goal:
            return moves

        # --- CAS 1 : EN L'AIR (Mouvement Forcé) ---
        if self.is_in_air():
            next_x = self.x + self.vx
            next_y = self.y - 1

            final_x = next_x
            final_y = next_y
            final_vx = self.vx

            if self.vx != 0 and not self.level.is_valid_position(self.x + self.vx, self.y):
                final_x = self.x
                final_vx = 0
            elif not self.level.is_valid_position(next_x, next_y):
                if self.level.is_valid_position(self.x, next_y):
                    final_x = self.x
                else:
                    final_y = self.y
                    final_vx = 0

            if final_y < 0: final_y = 0

            moves.append({
                'x': final_x, 'y': final_y, 'vx': final_vx, 'type': 'air'
            })

        # --- CAS 2 : AU SOL (Choix du joueur) ---
        else:
            actions = [
                (0, 0), (-1, 0), (1, 0),
                (0, 1), (-1, 1), (1, 1),
                (-1, -1), (1, -1), (0, -1)
            ]

            for dx, dy in actions:
                target_x = self.x + dx
                target_y = self.y + dy
                new_vx = dx if dx != 0 else 0

                if not self.level.is_valid_position(target_x, target_y):
                    continue

                if dx != 0 and dy != 0:
                    if dy == 1 and self.level.is_obstacle(self.x, self.y + 1):
                        continue
                    if dy == -1 and self.level.is_obstacle(self.x + dx, self.y):
                        continue

                moves.append({
                    'x': target_x,
                    'y': target_y,
                    'vx': new_vx,
                    'type': 'ground'
                })

        return moves

    def apply_move(self, move):
        self.x = move['x']
        self.y = move['y']
        self.vx = move['vx']
        self.tick += 1
        self.path.append((self.x, self.y))

        if (self.x, self.y) == self.level.goal_pos:
            self.reached_goal = True
            # print(">>> GAGNÉ ! <<<") # Commenté pour éviter le spam console

        if self.y == 0 and self.level.is_out_of_bounds(self.x, -1):
            pass


# --- ALGORITHME GENETIQUE ---

class DNA:
    """Représente les instructions d'une créature."""

    def __init__(self, length):
        self.length = length
        # Gènes : Une liste d'entiers aléatoires.
        # Chaque entier servira d'index pour choisir un mouvement dans la liste des possible_moves.
        self.genes = [random.randint(0, 100) for _ in range(length)]

    def mutate(self, rate):
        for i in range(self.length):
            if random.random() < rate:
                self.genes[i] = random.randint(0, 100)


class Agent:
    """Wrapper liant une Créature et son ADN."""

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

        # 1. Obtenir les mouvements possibles (Logique originale intacte)
        moves = self.creature.get_possible_moves()

        if not moves:
            self.creature.is_dead = True
            self.finished = True
            return

        # 2. Utiliser l'ADN pour choisir un mouvement
        # On utilise le modulo pour s'assurer que l'index est toujours valide
        # peu importe le nombre d'options (1 en l'air, X au sol).
        gene_val = self.dna.genes[self.creature.tick]
        chosen_move = moves[gene_val % len(moves)]

        # 3. Appliquer le mouvement
        self.creature.apply_move(chosen_move)

    def calculate_fitness(self):
        # Distance euclidienne vers l'objectif
        d_x = self.creature.x - self.creature.level.goal_pos[0]
        d_y = self.creature.y - self.creature.level.goal_pos[1]
        dist = math.sqrt(d_x ** 2 + d_y ** 2)

        if self.creature.reached_goal:
            # Récompense énorme pour la victoire + bonus de vitesse
            score = 10000 + (self.creature.level.n_ticks - self.creature.tick) * 10
        else:
            # Plus on est près, meilleur est le score
            score = 100.0 / (dist + 1.0)

            # Pénalité de mort (optionnel, parfois mieux sans)
            if self.creature.is_dead:
                score *= 0.5

        self.fitness = score
        return score


# --- VISUALISATION & MAIN ---

def to_screen(gx, gy, h):
    return gx * TILE_SIZE, (h - 1 - gy) * TILE_SIZE


def draw_level(screen, level):
    # Fond et Grille
    for y in range(level.height):
        for x in range(level.width):
            sx, sy = to_screen(x, y, level.height)
            rect = pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, (30, 30, 30), rect, 1)  # Grille subtile

            if level.is_obstacle(x, y):
                pygame.draw.rect(screen, GRAY, rect)
            elif (x, y) == level.start_pos:
                pygame.draw.rect(screen, (30, 100, 30), rect)  # Vert foncé start
            elif (x, y) == level.goal_pos:
                pygame.draw.rect(screen, RED, rect)


def draw_agents(screen, agents, level, best_agent=None):
    # Dessiner tous les agents (semi-transparents)
    surface = pygame.Surface((level.width * TILE_SIZE, level.height * TILE_SIZE), pygame.SRCALPHA)

    for agent in agents:
        if agent == best_agent: continue  # On le dessine après
        cx, cy = to_screen(agent.creature.x, agent.creature.y, level.height)
        # Bleu très transparent
        pygame.draw.circle(surface, (50, 100, 250, 50), (cx + TILE_SIZE // 2, cy + TILE_SIZE // 2), TILE_SIZE // 4)

    screen.blit(surface, (0, 0))

    # Dessiner le "Champion" de la génération précédente (ou actuelle si on veut)
    if best_agent:
        cx, cy = to_screen(best_agent.creature.x, best_agent.creature.y, level.height)
        pygame.draw.circle(screen, GREEN, (cx + TILE_SIZE // 2, cy + TILE_SIZE // 2), TILE_SIZE // 3 + 2)
        # Dessiner son chemin
        if len(best_agent.creature.path) > 1:
            pts = []
            for (px, py) in best_agent.creature.path:
                sx, sy = to_screen(px, py, level.height)
                pts.append((sx + TILE_SIZE // 2, sy + TILE_SIZE // 2))
            pygame.draw.lines(screen, GREEN, False, pts, 2)


def evolve(agents, level):
    # 1. Évaluation
    scores = [a.calculate_fitness() for a in agents]
    max_score = max(scores)

    # Normalisation pour la roulette
    # Création d'un pool de mating basé sur la fitness
    mating_pool = []
    for a in agents:
        # On ajoute l'agent dans la piscine proportionnellement à son score
        # (Version simplifiée de la roulette)
        n = int(a.fitness * 100)
        if a.creature.reached_goal: n *= 2  # Boost pour les vainqueurs
        for _ in range(n):
            mating_pool.append(a)

    # Sécurité si pool vide
    if not mating_pool:
        mating_pool = agents

    new_agents = []

    # 2. Elitisme : On garde les meilleurs absolus
    sorted_agents = sorted(agents, key=lambda x: x.fitness, reverse=True)
    best_dna = sorted_agents[0].dna  # Pour affichage

    for i in range(ELITISM_COUNT):
        # On copie l'ADN du meilleur dans un nouvel agent
        new_dna = DNA(level.n_ticks)
        new_dna.genes = sorted_agents[i].dna.genes[:]
        new_agents.append(Agent(level, new_dna))

    # 3. Reproduction
    while len(new_agents) < POPULATION_SIZE:
        parent_a = random.choice(mating_pool)
        parent_b = random.choice(mating_pool)

        child_dna = DNA(level.n_ticks)

        # Crossover (Point unique)
        midpoint = random.randint(0, level.n_ticks - 1)
        child_dna.genes = parent_a.dna.genes[:midpoint] + parent_b.dna.genes[midpoint:]

        # Mutation
        child_dna.mutate(MUTATION_RATE)

        new_agents.append(Agent(level, child_dna))

    return new_agents, sorted_agents[0]


def main():
    create_default_level_if_missing("level.txt")
    try:
        lvl = Level("level.txt")
    except FileNotFoundError:
        print("Erreur critique fichier.")
        return

    pygame.init()
    screen = pygame.display.set_mode((lvl.width * TILE_SIZE, lvl.height * TILE_SIZE))
    pygame.display.set_caption("AI Evolution - Genetic Algorithm")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    # Initialisation Population
    agents = [Agent(lvl) for _ in range(POPULATION_SIZE)]
    generation = 1
    champion = None  # Le meilleur de la gen précédente

    running = True
    while running:
        # --- LOGIQUE ---

        # Vérifier si la génération est finie
        all_finished = True
        for agent in agents:
            if not agent.finished:
                agent.update()
                all_finished = False

        # Si tout le monde a fini ses mouvements (ou est mort)
        if all_finished:
            agents, champion = evolve(agents, lvl)
            generation += 1
            print(
                f"Generation {generation} | Best Fitness: {champion.fitness:.2f} | Reached Goal: {champion.creature.reached_goal}")

        # --- EVENEMENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Option pour accélérer/ralentir avec FLÈCHE HAUT/BAS
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    clock.tick(1000)  # Turbo
                if event.key == pygame.K_DOWN:
                    clock.tick(60)  # Normal

        # --- DESSIN ---
        screen.fill(BLACK)
        draw_level(screen, lvl)

        # On dessine les agents
        # Pour éviter de dessiner 50 cercles opaques, on utilise la fonction dédiée
        draw_agents(screen, agents, lvl, champion)

        # Infos Texte
        info_txt = f"Gen: {generation} | Tick: {agents[0].creature.tick}/{lvl.n_ticks} | Pop: {POPULATION_SIZE}"
        surf = font.render(info_txt, True, WHITE)
        screen.blit(surf, (10, 10))

        if champion and champion.creature.reached_goal:
            win_surf = font.render("GOAL REACHED!", True, GREEN)
            screen.blit(win_surf, (10, 30))

        pygame.display.flip()

        # Vitesse de simulation : augmenter pour apprendre plus vite
        # 60 FPS = vitesse visuelle normale. 0 = max speed.
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()