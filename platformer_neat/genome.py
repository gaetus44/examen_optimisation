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

    def mutate(self, innovation_counter):
        if random.random() < config.PROB_MUTATE_WEIGHT:
            self.mutate_weight()
        if random.random() < config.PROB_ADD_CONNECTION:
            self.mutate_add_connection(innovation_counter)
        if random.random() < config.PROB_ADD_NODE:
            self.mutate_add_node(innovation_counter)

    def mutate_weight(self):
        for conn in self.connections:
            if random.random() < 0.1:
                conn.weight = random.uniform(-config.WEIGHT_RANDOM_STRENGTH, config.WEIGHT_RANDOM_STRENGTH) #remplacement complet
            else:
                conn.weight += random.gauss(0, 1) * 0.5#légère modification du poid
                conn.weight = max(min(conn.weight, 8.0), -8.0)

    def mutate_add_connection(self, innovation_counter):
        if not self.nodes: return
        node1 = random.choice(self.nodes)
        node2 = random.choice(self.nodes)
        if node2.type == 'INPUT' or node1.id == node2.id:
            return
        for conn in self.connections:
            if conn.in_node == node1.id and conn.out_node == node2.id:
                return
        innov = innovation_counter.get_innovation(node1.id, node2.id)
        self.connections.append(ConnectionGene(node1.id, node2.id, random.uniform(-1, 1), True, innov))

    def mutate_add_node(self, innovation_counter):
        if not self.connections: return
        valid_conns = [c for c in self.connections if c.enabled]
        if not valid_conns: return
        conn = random.choice(valid_conns)
        conn.enabled = False

        max_id = max([n.id for n in self.nodes])
        new_node_id = max_id + 1
        self.nodes.append(NodeGene(new_node_id, 'HIDDEN'))

        innov1 = innovation_counter.get_innovation(conn.in_node, new_node_id)
        self.connections.append(ConnectionGene(conn.in_node, new_node_id, 1.0, True, innov1))
        innov2 = innovation_counter.get_innovation(new_node_id, conn.out_node)
        self.connections.append(ConnectionGene(new_node_id, conn.out_node, conn.weight, True, innov2))

    @staticmethod
    def crossover(parent1, parent2):
        offspring = Genome(0)
        # Héritage des nœuds
        all_nodes = {n.id: n for n in parent1.nodes}
        for n in parent2.nodes:
            if n.id not in all_nodes:
                all_nodes[n.id] = n
        offspring.nodes = [n.copy() for n in all_nodes.values()]

        # Héritage des connexions (Alignement par innovation)
        genes1 = {c.innovation: c for c in parent1.connections}
        genes2 = {c.innovation: c for c in parent2.connections}
        all_innovations = set(genes1.keys()) | set(genes2.keys())

        for innov in sorted(all_innovations):
            c1 = genes1.get(innov)
            c2 = genes2.get(innov)
            if c1 and c2:
                chosen = c1 if random.random() > 0.5 else c2
                offspring.connections.append(chosen.copy())
            elif c1:  # On prend seulement l'excès du parent 1 (le meilleur)
                offspring.connections.append(c1.copy())

        return offspring