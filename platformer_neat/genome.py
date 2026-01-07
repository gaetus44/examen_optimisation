# genome.py
import random
import config
from genes import ConnectionGene, NodeGene


class Genome:
    def __init__(self, id):
        self.id = id
        self.nodes = []
        self.connections = []
        self.fitness = 0.0
        self.adjusted_fitness = 0.0

    def init_simple(self, num_inputs, num_outputs, innovation_counter):
        for i in range(num_inputs):
            self.nodes.append(NodeGene(i, 'INPUT'))
        for i in range(num_outputs):
            self.nodes.append(NodeGene(num_inputs + i, 'OUTPUT'))
        for i in range(num_inputs):
            for j in range(num_outputs):
                innov = innovation_counter.get_innovation(i, num_inputs + j)
                weight = random.uniform(-1, 1)
                self.connections.append(ConnectionGene(i, num_inputs + j, weight, True, innov))

    def get_distance(self, other):
        """
        Calcule la distance génétique entre deux génomes pour la spéciation.

        Compare les gènes de connexion en utilisant leurs numéros d'innovation :
        - Les gènes communs (Matching) : On calcule la différence de poids.
        - Les gènes uniques (Disjoint/Excess) : On compte les différences de structure.

        Returns:
            float: Une valeur représentant la divergence entre les deux réseaux.
                   Si distance > DISTANCE_THRESHOLD, ils sont d'espèces différentes.
        """

        genes1 = sorted(self.connections, key=lambda c: c.innovation)
        genes2 = sorted(other.connections, key=lambda c: c.innovation)

        if not genes1 or not genes2: return 0

        highest_innov1 = genes1[-1].innovation
        highest_innov2 = genes2[-1].innovation
        if highest_innov1 < highest_innov2:
            genes1, genes2 = genes2, genes1

        idx1, idx2 = 0, 0
        disjoint, excess, matching = 0, 0, 0
        weight_diff = 0

        while idx1 < len(genes1) and idx2 < len(genes2):
            c1, c2 = genes1[idx1], genes2[idx2]
            if c1.innovation == c2.innovation:
                weight_diff += abs(c1.weight - c2.weight)
                matching += 1
                idx1 += 1
                idx2 += 1
            elif c1.innovation < c2.innovation:
                disjoint += 1
                idx1 += 1
            else:
                disjoint += 1
                idx2 += 1

        excess = len(genes1) - idx1
        N = max(len(genes1), len(genes2))
        if N < 20: N = 1

        avg_weight = weight_diff / matching if matching > 0 else 0
        return (config.COEFF_EXCESS * excess / N) + (config.COEFF_DISJOINT * disjoint / N) + (
                    config.COEFF_WEIGHT * avg_weight)

    def mutate(self, innovation_counter):
        if random.random() < config.PROB_MUTATE_WEIGHT:
            for conn in self.connections:
                if random.random() < 0.1:
                    conn.weight = random.uniform(-config.WEIGHT_RANDOM_STRENGTH, config.WEIGHT_RANDOM_STRENGTH)
                else:
                    conn.weight += random.gauss(0, 1) * 0.5
                    conn.weight = max(min(conn.weight, 8.0), -8.0)

        if random.random() < config.PROB_ADD_CONNECTION:
            self.mutate_add_connection(innovation_counter)
        if random.random() < config.PROB_ADD_NODE:
            self.mutate_add_node(innovation_counter)

    def mutate_add_connection(self, innovation_counter):
        n1, n2 = random.choice(self.nodes), random.choice(self.nodes)
        if n2.type == 'INPUT' or n1.id == n2.id: return
        for c in self.connections:
            if c.in_node == n1.id and c.out_node == n2.id: return
        innov = innovation_counter.get_innovation(n1.id, n2.id)
        self.connections.append(ConnectionGene(n1.id, n2.id, random.uniform(-1, 1), True, innov))

    def mutate_add_node(self, innovation_counter):
        enabled_conns = [c for c in self.connections if c.enabled]
        if not enabled_conns: return
        conn = random.choice(enabled_conns)
        conn.enabled = False
        new_id = max(n.id for n in self.nodes) + 1
        self.nodes.append(NodeGene(new_id, 'HIDDEN'))
        self.connections.append(
            ConnectionGene(conn.in_node, new_id, 1.0, True, innovation_counter.get_innovation(conn.in_node, new_id)))
        self.connections.append(ConnectionGene(new_id, conn.out_node, conn.weight, True,
                                               innovation_counter.get_innovation(new_id, conn.out_node)))

    @staticmethod
    def crossover(p1, p2):
        offspring = Genome(0)
        all_nodes = {n.id: n.copy() for n in p1.nodes}
        for n in p2.nodes:
            if n.id not in all_nodes: all_nodes[n.id] = n.copy()
        offspring.nodes = list(all_nodes.values())

        g1 = {c.innovation: c for c in p1.connections}
        g2 = {c.innovation: c for c in p2.connections}
        for innov in sorted(set(g1.keys()) | set(g2.keys())):
            c1, c2 = g1.get(innov), g2.get(innov)
            if c1 and c2:
                offspring.connections.append((c1 if random.random() > 0.5 else c2).copy())
            elif c1:
                offspring.connections.append(c1.copy())
        return offspring