import random
from individual import Individual

class Population:
    def __init__(self, size, initialize=True, gene_length=60):
        self.individuals = []
        if initialize:
            for _ in range(size):
                # On crée des individus qui ont au moins la durée du niveau
                individu = Individual(gene_length)
                self.individuals.append(individu)

    def get_individual(self, index):
        return self.individuals[index]

    def get_fittest(self, game):
        # Retourne l'individu avec le meilleur score
        return max(self.individuals, key=lambda ind: ind.get_fitness(game))

    def size(self):
        return len(self.individuals)