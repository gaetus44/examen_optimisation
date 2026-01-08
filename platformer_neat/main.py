# main.py
import random, math, sys, pygame
import config
from rules import Level, Creature, draw, TILE_SIZE, BLACK
from genome import Genome
from network import FeedForwardNetwork

ACTIONS_MAP = [(0,0),(-1,0),(1,0),(0,1),(-1,1),(1,1),(-1,-1),(1,-1),(0,-1)]

class InnovationCounter:
    def __init__(self):
        self.current, self.history = 0, {}
    def get_innovation(self, n1, n2):
        # Si cette connexion (n1 -> n2) a déjà été inventée par quelqu'un dans l'histoire,
        # je renvoie son ID historique existant.
        # Sinon, je crée un nouveau numéro d'innovation.
        if (n1, n2) not in self.history: self.current += 1; self.history[(n1, n2)] = self.current
        return self.history[(n1, n2)]

class Species:
    def __init__(self, rep):
        self.representative, self.members, self.best_fitness, self.stagnation = rep, [rep], 0.0, 0
    def sort_and_update(self):
        # Trie les membres par score.
        # Vérifie si l'espèce progresse ou stagne (pour l'éteindre si elle devient nulle).
        # Désigne le nouveau "Représentant" (le meilleur membre) pour la prochaine comparaison.
        self.members.sort(key=lambda x: x.fitness, reverse=True)
        if self.members[0].fitness > self.best_fitness: self.best_fitness, self.stagnation = self.members[0].fitness, 0
        else: self.stagnation += 1
        self.representative = self.members[0]

class Population:
    def __init__(self, size):
        self.size, self.genomes, self.species, self.innov = size, [], [], InnovationCounter()
        self.runner = GameRunner()
        # Création de la population initiale (Réseaux minimalistes sans neurones cachés)
        for i in range(size):
            g = Genome(i); g.init_simple(config.INPUTS, config.OUTPUTS, self.innov); self.genomes.append(g)

    def speciate(self):
        for s in self.species: s.members = [] # Vide les espèces précédentes
        for g in self.genomes:
            found = False
            for s in self.species:
                # Si le génome ressemble au représentant, il rejoint l'espèce
                if g.get_distance(s.representative) < config.DISTANCE_THRESHOLD: s.members.append(g); found = True; break
            # Sinon, il fonde une nouvelle espèce
            if not found: self.species.append(Species(g))
        # Supprime les espèces vides
        self.species = [s for s in self.species if s.members]

    def run(self):
        for gen in range(config.MAX_GENERATIONS):
            # 1. Classification (Spéciation)
            self.speciate()

            # 2. Évaluation (Simulation du jeu pour chaque agent)
            best_g, max_f = None, -1
            for g in self.genomes:
                g.fitness = self.runner.run_genome(g)
                if g.fitness > max_f: max_f, best_g = g.fitness, g
            # 3. Ajustement du score (Fitness Sharing)
            for s in self.species:
                # On divise le score par la taille de l'espèce pour protéger les petites innovations
                for g in s.members: g.adjusted_fitness = g.fitness / len(s.members)
                s.sort_and_update()
            print(f"Gen {gen}: Best={max_f:.2f} | Species={len(self.species)}")
            # Affichage visuel tous les 10 tours
            if gen % 10 == 0: self.runner.run_genome(best_g, True)
            # 4. Gestion de l'extinction (Stagnation)
            if len(self.species) > 2: self.species = [s for s in self.species if s.stagnation < config.STAGNATION_LIMIT]
            # 5. Reproduction
            next_gen = [best_g] # Élitisme global : le champion survit toujours
            # Calcul du nombre d'enfants par espèce (basé sur le fitness ajusté)
            for s in self.species:
                # Élitisme par espèce (optionnel)
                if s.members[0] != best_g: next_gen.append(s.members[0])
            total_adj = sum(g.adjusted_fitness for g in self.genomes)
            if total_adj > 0:
                for s in self.species:
                    s_adj = sum(g.adjusted_fitness for g in s.members)
                    # Nombre d'enfants alloués à cette espèce
                    n_child = int((s_adj / total_adj) * self.size) - 1
                    for _ in range(max(0, n_child)):
                        if len(next_gen) >= self.size: break
                        # Sélection des parents
                        p1 = self.select(s.members)
                        # Chance de croisement inter-espèces (très rare)
                        p2 = self.select(self.genomes) if random.random() < config.PROB_INTERSPECIES_MATE else self.select(s.members)
                        if p2.fitness > p1.fitness: p1, p2 = p2, p1
                        # Crossover + Mutation (Poids, Lien ou Nœud)
                        child = Genome.crossover(p1, p2); child.mutate(self.innov)
                        child.id = len(next_gen) + gen*self.size; next_gen.append(child)
            # Combler le vide si les calculs d'arrondi ont laissé des places libres
            while len(next_gen) < self.size:
                p = random.choice(self.genomes); c = Genome.crossover(p, p); c.mutate(self.innov); c.id = len(next_gen) + gen*self.size; next_gen.append(c)
            self.genomes = next_gen
        pygame.quit()

    def select(self, members):
        """ Un peu comme le système de roulette, les individus avec un plus grand fitness
        ont plus de chance d'être parent. """
        total = sum(m.fitness for m in members)
        if total == 0: return random.choice(members)
        r, cur = random.uniform(0, total), 0
        for m in members:
            cur += m.fitness
            if cur >= r: return m
        return members[0]

class GameRunner:
    def run_genome(self, genome, draw_mode=False):
        lvl = Level("level3.txt"); c = Creature(lvl); net = FeedForwardNetwork(genome)
        if draw_mode: pygame.init(); screen = pygame.display.set_mode((lvl.width*TILE_SIZE, lvl.height*TILE_SIZE)); clock = pygame.time.Clock()
        start_dist = math.sqrt((lvl.goal_pos[0]-c.x)**2 + (lvl.goal_pos[1]-c.y)**2)
        while c.tick < lvl.n_ticks and not c.reached_goal:
            if draw_mode:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            moves = c.get_possible_moves()
            if not moves: break
            # Si en l'air, la physique commande, pas l'IA
            if c.is_in_air(): chosen = moves[0]
            else:
                # --- VISION DE L'IA ---
                # INJECTION DU BIAIS ICI : 5ème entrée à 1.0
                inputs = [
                    c.x/lvl.width, # Ma position X (Normalisée entre 0 et 1)
                    c.y/lvl.height, # Ma position Y
                    (lvl.goal_pos[0]-c.x)/lvl.width, # Distance X vers le but
                    (lvl.goal_pos[1]-c.y)/lvl.height, # Distance Y vers le but
                    1.0 # LE BIAIS
                ]

                # Le réseau réfléchit
                out = net.activate(inputs)
                # On trie les sorties : la plus forte gagne
                prefs = sorted(enumerate(out), key=lambda x: x[1], reverse=True)
                # enumerate() crée des paires (Index, Score).
                # Cela permet de trier par score tout en gardant l'index pour retrouver l'action correspondante dans ACTIONS_MAP.

                chosen = moves[0]

                # On cherche la première action "physiquement possible" parmi les préférences de l'IA
                for idx, v in prefs:
                    dx, dy = ACTIONS_MAP[idx]
                    found = [m for m in moves if (m['x']-c.x)==dx and (m['y']-c.y)==dy]
                    if found: chosen = found[0]; break
            c.apply_move(chosen)
            if draw_mode: draw(screen, lvl, c, moves); pygame.display.flip(); clock.tick(30)
        # Calcul du Fitness (Distance + Bonus Victoire)
        dist = math.sqrt((lvl.goal_pos[0]-c.x)**2 + (lvl.goal_pos[1]-c.y)**2)
        fitness = max(0, start_dist - dist)
        if c.reached_goal: fitness += 50 + (lvl.n_ticks - c.tick) * 0.1
        return fitness

if __name__ == "__main__":
    pop = Population(config.POPULATION_SIZE); pop.run()