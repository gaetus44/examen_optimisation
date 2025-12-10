import random
from individual import Individual
from population import Population


class SimpleGeneticAlgorithm:
    def __init__(self, game, selection_type="tournament"):
        self.game = game
        self.selection_type = selection_type

        # --- PARAMÈTRES CONFORMES AU PDF ---
        self.tournament_size = 5
        self.elitism = True
        self.max_gen = 1000

        # Slide 9 : Crossover rate p entre 20% et 90%
        self.uniform_rate = 0.5

        # Slide 9 : Mutation rate m entre 1% et 10%
        # C'est LE paramètre critique pour la convergence fine
        self.mutation_rate_flip = 0.05

        # Mutation structurelle (non requise par le PDF, gardée très basse)
        self.mutation_rate_add = 0.01
        self.mutation_rate_remove = 0.01

    def run_algorithm(self, population_size):
        # Création population initiale
        pop = Population(population_size, gene_length=self.game.max_ticks)
        generation_count = 1

        while generation_count <= self.max_gen:
            best_indiv = pop.get_fittest(self.game)
            score = best_indiv.get_fitness(self.game)

            print(f"Gen: {generation_count} | Score: {score:.2f} | Moves: {best_indiv}")

            # Condition d'arrêt : Score parfait ou proche
            if score >= 99.0:
                print("Solution trouvée !")
                break

            pop = self.evolve_population(pop)
            generation_count += 1

        final_best = pop.get_fittest(self.game)
        print(f"FIN. Gen: {generation_count}")
        print(f"Best Score: {final_best.get_fitness(self.game):.2f}")
        return True

    def evolve_population(self, pop):
        new_pop = Population(pop.size(), initialize=False)
        elitism_offset = 0

        if self.elitism:
            new_pop.individuals.append(pop.get_fittest(self.game))
            elitism_offset = 1

        for i in range(elitism_offset, pop.size()):
            if self.selection_type == "tournament":
                indiv1 = self.tournament_selection(pop)
                indiv2 = self.tournament_selection(pop)
            else:
                indiv1 = self.roulette_wheel_selection(pop)
                indiv2 = self.roulette_wheel_selection(pop)

            new_indiv = self.crossover(indiv1, indiv2)
            new_pop.individuals.append(new_indiv)

        # On applique la mutation sur les nouveaux enfants (sauf l'élite)
        for i in range(elitism_offset, new_pop.size()):
            self.mutate(new_pop.get_individual(i))

        return new_pop

    def crossover(self, indiv1, indiv2):
        # Uniform Crossover
        shorter = min(indiv1.get_length(), indiv2.get_length())
        child_genes = []

        for i in range(shorter):
            if random.random() <= self.uniform_rate:
                child_genes.append(indiv1.get_single_gene(i))
            else:
                child_genes.append(indiv2.get_single_gene(i))

        return Individual(genes_list=child_genes)

    def mutate(self, indiv):
        # Mutation Flip (Change un mouvement existant)
        for i in range(indiv.get_length()):
            if random.random() <= self.mutation_rate_flip:
                # 0=Wait, 1=Left, 2=Right, 3=Jump, 4=JumpL, 5=JumpR
                indiv.set_single_gene(i, random.randint(0, 5))

        # Mutation Add (Extension rare)
        if random.random() <= self.mutation_rate_add:
            indiv.add_gene(random.randint(0, 5))

        # Mutation Remove (Contraction rare)
        if indiv.get_length() > 10 and random.random() <= self.mutation_rate_remove:
            indiv.remove_gene(random.randint(0, indiv.get_length() - 1))

    def tournament_selection(self, pop):
        tournament = Population(self.tournament_size, initialize=False)
        for _ in range(self.tournament_size):
            random_indiv = pop.get_individual(random.randint(0, pop.size() - 1))
            tournament.individuals.append(random_indiv)
        return tournament.get_fittest(self.game)

    def roulette_wheel_selection(self, pop):
        total_fitness = sum(indiv.get_fitness(self.game) for indiv in pop.individuals)
        if total_fitness == 0:
            return pop.get_individual(random.randint(0, pop.size() - 1))

        pick = random.uniform(0, total_fitness)
        current = 0
        for indiv in pop.individuals:
            current += indiv.get_fitness(self.game)
            if current > pick:
                return indiv
        return pop.individuals[-1]