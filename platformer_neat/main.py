# main.py
import random
import math
import sys
import pygame
import config

# Import du moteur de jeu existant (SANS MODIFICATION)
from rules import Level, Creature, draw, TILE_SIZE, WHITE, BLACK
from genome import Genome
from network import FeedForwardNetwork

# Liste des actions théoriques (Doit correspondre EXACTEMENT à rules.py lignes 115-117)
# (dx, dy)
ACTIONS_MAP = [
    (0, 0), (-1, 0), (1, 0),  # Sur place, Gauche, Droite
    (0, 1), (-1, 1), (1, 1),  # Sauts (Haut, Gauche, Droite)
    (-1, -1), (1, -1), (0, -1)  # Bas-Gauche, Bas-Droite, Bas
]


class InnovationCounter:
    def __init__(self):
        self.current_innovation = 0
        self.history = {}

    def get_innovation(self, in_node, out_node):
        key = (in_node, out_node)
        if key in self.history:
            return self.history[key]
        self.current_innovation += 1
        self.history[key] = self.current_innovation
        return self.current_innovation


class GameRunner:
    def __init__(self, level_path="level.txt"):
        self.level_path = level_path
        self.base_level = Level(level_path)  # On charge une fois pour lire les dimensions

    def get_distance(self, c_x, c_y, g_x, g_y):
        return math.sqrt((g_x - c_x) ** 2 + (g_y - c_y) ** 2)

    def run_genome(self, genome, draw_mode=False):
        """
        Exécute une simulation complète pour un génome.
        Retourne la fitness (score).
        Si draw_mode=True, affiche le jeu avec Pygame.
        """
        # Réinitialisation propre du niveau et de la créature à chaque test
        level = Level(self.level_path)
        creature = Creature(level)
        net = FeedForwardNetwork(genome)

        screen = None
        clock = None
        if draw_mode:
            pygame.init()
            screen = pygame.display.set_mode((level.width * TILE_SIZE, level.height * TILE_SIZE))
            pygame.display.set_caption(f"Replay Genome ID: {genome.id}")
            clock = pygame.time.Clock()

        # Distance initiale pour calculer le progrès
        start_dist = self.get_distance(creature.x, creature.y, level.goal_pos[0], level.goal_pos[1])

        # Boucle de jeu (limitée par le nombre de ticks du niveau)
        while creature.tick < level.n_ticks:

            # Gestion basique des événements Pygame (pour pouvoir fermer la fenêtre)
            if draw_mode:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

            # 1. Obtenir les coups possibles du moteur physique
            possible_moves = creature.get_possible_moves()

            # Si plus de coups possibles (bloqué ou mort), fin.
            if not possible_moves:
                break

            chosen_move = None

            # --- LOGIQUE DE DÉCISION ---
            if creature.is_in_air():
                # CAS 1 : EN L'AIR -> Mouvement forcé par la physique
                # On prend le seul mouvement disponible (la chute/inertie)
                if possible_moves:
                    chosen_move = possible_moves[0]
            else:
                # CAS 2 : AU SOL -> Le Réseau de Neurones décide

                # A. Préparation des Entrées (Inputs)
                # Normalisation des valeurs entre 0 et 1 (ou -1 et 1) pour le réseau
                norm_x = creature.x / level.width
                norm_y = creature.y / level.height
                dist_x = (level.goal_pos[0] - creature.x) / level.width
                dist_y = (level.goal_pos[1] - creature.y) / level.height

                inputs = [norm_x, norm_y, dist_x, dist_y]

                # B. Activation du réseau
                outputs = net.activate(inputs)  # Retourne une liste de 9 valeurs

                # C. Sélection de l'action
                # On associe chaque output à une action théorique via ACTIONS_MAP
                # On trie les actions par la valeur de sortie (du plus fort au plus faible)
                indexed_outputs = []
                for i, val in enumerate(outputs):
                    indexed_outputs.append((val, i))

                # Tri décroissant (la plus grande valeur d'abord)
                indexed_outputs.sort(key=lambda x: x[0], reverse=True)

                # D. Trouver le premier mouvement VALIDE parmi les souhaits du réseau
                for val, idx in indexed_outputs:
                    desired_dx, desired_dy = ACTIONS_MAP[idx]

                    # On cherche si ce (dx, dy) correspond à un coup valide réel
                    found = False
                    for move in possible_moves:
                        # move['x'] est la destination absolue. On recalcule le delta.
                        real_dx = move['x'] - creature.x
                        real_dy = move['y'] - creature.y

                        if real_dx == desired_dx and real_dy == desired_dy:
                            chosen_move = move
                            found = True
                            break

                    if found:
                        break  # On a trouvé le meilleur coup valide

                # Sécurité : Si le réseau ne trouve rien (rare), on ne bouge pas ou 1er coup
                if not chosen_move and possible_moves:
                    chosen_move = possible_moves[0]

            # Application du mouvement
            if chosen_move:
                creature.apply_move(chosen_move)

            # Dessin
            if draw_mode and screen:
                draw(screen, level, creature, possible_moves)
                pygame.display.flip()
                clock.tick(20)  # Vitesse de replay (15 FPS pour bien voir)

            # Condition de victoire
            if creature.reached_goal:
                break

        # --- CALCUL DE LA FITNESS ---
        end_dist = self.get_distance(creature.x, creature.y, level.goal_pos[0], level.goal_pos[1])

        # Score basé sur la distance parcourue (Plus on réduit la distance, mieux c'est)
        # start_dist ~ 15.0. Si on arrive à 0, on gagne environ 15 points.
        fitness = (start_dist - end_dist)

        # Gros bonus si gagné
        if creature.reached_goal:
            fitness += 50.0  # Bonus victoire
            # Petit bonus de vitesse (plus il reste de ticks, mieux c'est)
            fitness += (level.n_ticks - creature.tick) * 0.1

        # On évite les fitness négatives
        return max(0.0, fitness)


class Population:
    def __init__(self, size):
        self.genomes = []
        self.innovation_counter = InnovationCounter()
        self.runner = GameRunner("level.txt")  # Gestionnaire du jeu

        # Init population
        for i in range(size):
            g = Genome(i)
            # Init avec INPUTS et OUTPUTS du config
            g.init_simple(config.INPUTS, config.OUTPUTS, self.innovation_counter)
            self.genomes.append(g)

    def run(self):
        for gen in range(config.MAX_GENERATIONS):
            # 1. Évaluer Fitness pour toute la population
            best_gen_fitness = -1000
            best_genome = None

            for genome in self.genomes:
                # Lancer le jeu sans graphismes (rapide)
                genome.fitness = self.runner.run_genome(genome, draw_mode=False)

                if genome.fitness > best_gen_fitness:
                    best_gen_fitness = genome.fitness
                    best_genome = genome

            print(
                f"Gen {gen}: Best Fitness = {best_gen_fitness:.4f} | Neurones: {len(best_genome.nodes)} | Connexions: {len(best_genome.connections)}")

            # Visualiser le champion de la génération
            # (Optionnel : on peut le faire tous les 10 tours ou si le score est bon)
            print(f"   -> Replay du champion (ID: {best_genome.id})...")
            self.runner.run_genome(best_genome, draw_mode=True)

            # Si on a un score très élevé (Victoire + marge), on peut arrêter ou continuer
            if best_gen_fitness > 45:
                print(">>> PERFORMANCE EXCEPTIONNELLE ATTEINTE <<<")

            # 2. Sélection et Reproduction
            self.genomes.sort(key=lambda x: x.fitness, reverse=True)

            # ÉLITISME : Garder les 20% meilleurs
            cutoff = int(config.POPULATION_SIZE * 0.2)
            cutoff = max(2, cutoff)
            survivors = self.genomes[:cutoff]

            next_gen_genomes = []

            # On garde le Top 1 tel quel
            next_gen_genomes.append(survivors[0])

            while len(next_gen_genomes) < config.POPULATION_SIZE:
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)

                if parent1.fitness < parent2.fitness:
                    parent1, parent2 = parent2, parent1

                child = Genome.crossover(parent1, parent2)
                child.mutate(self.innovation_counter)
                child.id = len(next_gen_genomes) + (gen * config.POPULATION_SIZE)  # ID unique
                next_gen_genomes.append(child)

            self.genomes = next_gen_genomes

        pygame.quit()


if __name__ == "__main__":
    # Vérification fichier level
    try:
        with open("level.txt", "r"):
            pass
    except FileNotFoundError:
        print("Erreur: level.txt introuvable.")
        sys.exit()

    pop = Population(config.POPULATION_SIZE)
    pop.run()