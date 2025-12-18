# main.py
import random, math, sys, pygame
import config
from rules import Level, Creature, draw, TILE_SIZE, BLACK
from genome import Genome
from network import FeedForwardNetwork

ACTIONS_MAP = [(0, 0), (-1, 0), (1, 0), (0, 1), (-1, 1), (1, 1), (-1, -1), (1, -1), (0, -1)]


class InnovationCounter:
    def __init__(self):
        self.current, self.history = 0, {}

    def get_innovation(self, n1, n2):
        if (n1, n2) not in self.history: self.current += 1; self.history[(n1, n2)] = self.current
        return self.history[(n1, n2)]


class Species:
    def __init__(self, rep):
        self.representative, self.members, self.best_fitness, self.stagnation = rep, [rep], 0.0, 0

    def sort_and_update(self):
        self.members.sort(key=lambda x: x.fitness, reverse=True)
        if self.members[0].fitness > self.best_fitness:
            self.best_fitness, self.stagnation = self.members[0].fitness, 0
        else:
            self.stagnation += 1
        self.representative = self.members[0]


class Population:
    def __init__(self, size):
        self.size, self.genomes, self.species, self.innov = size, [], [], InnovationCounter()
        self.runner = GameRunner()
        for i in range(size):
            g = Genome(i);
            g.init_simple(config.INPUTS, config.OUTPUTS, self.innov);
            self.genomes.append(g)

    def speciate(self):
        for s in self.species: s.members = []
        for g in self.genomes:
            found = False
            for s in self.species:
                if g.get_distance(s.representative) < config.DISTANCE_THRESHOLD: s.members.append(
                    g); found = True; break
            if not found: self.species.append(Species(g))
        self.species = [s for s in self.species if s.members]

    def run(self):
        for gen in range(config.MAX_GENERATIONS):
            self.speciate()
            best_g, max_f = None, -1
            for g in self.genomes:
                g.fitness = self.runner.run_genome(g)
                if g.fitness > max_f: max_f, best_g = g.fitness, g
            for s in self.species:
                for g in s.members: g.adjusted_fitness = g.fitness / len(s.members)
                s.sort_and_update()

            print(f"Gen {gen}: Best={max_f:.2f} | Species={len(self.species)}")
            if gen % 10 == 0: self.runner.run_genome(best_g, True)

            # Gestion de la survie
            if len(self.species) > 2:
                self.species = [s for s in self.species if s.stagnation < config.STAGNATION_LIMIT]

            next_gen = [best_g]  # Elitisme
            total_adj = sum(g.adjusted_fitness for g in self.genomes)

            if total_adj > 0:
                for s in self.species:
                    s_adj = sum(g.adjusted_fitness for g in s.members)
                    n_child = int((s_adj / total_adj) * self.size) - 1
                    for _ in range(max(0, n_child)):
                        if len(next_gen) >= self.size: break
                        p1 = self.select(s.members)
                        p2 = self.select(
                            self.genomes) if random.random() < config.PROB_INTERSPECIES_MATE else self.select(s.members)
                        child = Genome.crossover(p1, p2);
                        child.mutate(self.innov)
                        child.id = len(next_gen) + gen * self.size;
                        next_gen.append(child)

            while len(next_gen) < self.size:
                p = self.select(self.genomes)
                c = Genome.crossover(p, p);
                c.mutate(self.innov);
                c.id = len(next_gen) + gen * self.size;
                next_gen.append(c)
            self.genomes = next_gen
        pygame.quit()

    def select(self, members):
        total = sum(m.fitness for m in members)
        if total <= 0: return random.choice(members)
        r, cur = random.uniform(0, total), 0
        for m in members:
            cur += m.fitness
            if cur >= r: return m
        return members[0]


class GameRunner:
    def run_genome(self, genome, draw_mode=False):
        lvl = Level("level.txt");
        c = Creature(lvl);
        net = FeedForwardNetwork(genome)
        if draw_mode:
            pygame.init()
            screen = pygame.display.set_mode((lvl.width * TILE_SIZE, lvl.height * TILE_SIZE))
            clock = pygame.time.Clock()

        start_dist = math.sqrt((lvl.goal_pos[0] - c.x) ** 2 + (lvl.goal_pos[1] - c.y) ** 2)
        visited = set()

        while c.tick < lvl.n_ticks and not c.reached_goal:
            if draw_mode:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: pygame.quit(); sys.exit()

            moves = c.get_possible_moves()
            if not moves: break

            if c.is_in_air():
                chosen = moves[0]
            else:
                # --- CALCUL DES CAPTEURS DE VISION (0 ou 1) ---
                v_up = 1.0 if lvl.is_obstacle(c.x, c.y + 1) or c.y + 1 >= lvl.height else 0.0
                v_down = 1.0 if lvl.is_obstacle(c.x, c.y - 1) or c.y - 1 < 0 else 0.0
                v_left = 1.0 if lvl.is_obstacle(c.x - 1, c.y) or c.x - 1 < 0 else 0.0
                v_right = 1.0 if lvl.is_obstacle(c.x + 1, c.y) or c.x + 1 >= lvl.width else 0.0

                inputs = [
                    c.x / lvl.width,
                    c.y / lvl.height,
                    (lvl.goal_pos[0] - c.x) / lvl.width,
                    (lvl.goal_pos[1] - c.y) / lvl.height,
                    1.0,  # Biais
                    v_up, v_down, v_left, v_right  # Nouveaux capteurs
                ]

                out = net.activate(inputs)
                prefs = sorted(enumerate(out), key=lambda x: x[1], reverse=True)

                chosen = moves[0]
                for idx, v in prefs:
                    if idx >= len(ACTIONS_MAP): continue
                    dx, dy = ACTIONS_MAP[idx]
                    found = [m for m in moves if (m['x'] - c.x) == dx and (m['y'] - c.y) == dy]
                    if found:
                        chosen = found[0]
                        break

            c.apply_move(chosen)
            visited.add((c.x, c.y))

            if draw_mode:
                draw(screen, lvl, c, moves)
                pygame.display.flip()
                clock.tick(30)

        # --- CALCUL DE LA FITNESS AMÉLIORÉE ---
        end_dist = math.sqrt((lvl.goal_pos[0] - c.x) ** 2 + (lvl.goal_pos[1] - c.y) ** 2)

        # Base : On récompense le rapprochement
        fitness = max(0.1, start_dist - end_dist)

        # Bonus d'exploration : récompense les cases uniques visitées
        fitness += len(visited) * 0.5

        # Gros bonus de victoire
        if c.reached_goal:
            fitness += 100 + (lvl.n_ticks - c.tick) * 2.0

        return fitness


if __name__ == "__main__":
    pop = Population(config.POPULATION_SIZE)
    pop.run()