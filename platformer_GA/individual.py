import random

class Individual:
    def __init__(self, gene_length=60, genes_list=None):
        if genes_list:
            self.genes = list(genes_list)
        else:
            # 0=Wait, 1=Left, 2=Right, 3=Jump, 4=JumpL, 5=JumpR
            self.genes = [random.randint(0, 5) for _ in range(gene_length)]

        self.fitness = -1

    def get_length(self):
        return len(self.genes)

    def get_single_gene(self, index):
        return self.genes[index]

    def set_single_gene(self, index, value):
        self.genes[index] = value
        self.fitness = -1

    def add_gene(self, value):
        self.genes.append(value)
        self.fitness = -1

    def remove_gene(self, index):
        if self.get_length() > 0:
            self.genes.pop(index)
            self.fitness = -1

    def get_fitness(self, game):
        if self.fitness == -1:
            self.fitness = game.simulate(self.genes)
        return self.fitness

    def __str__(self):
        # Affichage compact pour le debug
        mapping = {0: '.', 1: 'L', 2: 'R', 3: 'J', 4: '(', 5: ')'}
        return ''.join([mapping.get(g, '?') for g in self.genes])