# network.py
import config


class FeedForwardNetwork:
    def __init__(self, genome):
        self.genome = genome
        self.values = {}

    def activate(self, inputs):
        self.values = {}
        # On mappe les entrées sur les IDs des nœuds de type INPUT
        input_nodes = sorted([n for n in self.genome.nodes if n.type == 'INPUT'], key=lambda x: x.id)

        for i, val in enumerate(inputs):
            if i < len(input_nodes):
                self.values[input_nodes[i].id] = val

        nodes_to_process = [n for n in self.genome.nodes if n.type != 'INPUT']
        nodes_to_process.sort(key=lambda x: x.id)

        # On propage plusieurs fois pour les connexions complexes
        for _ in range(3):
            state_changed = False
            for node in nodes_to_process:
                incoming_sum = 0.0
                has_input = False

                for conn in self.genome.connections:
                    if not conn.enabled: continue
                    if conn.out_node == node.id:
                        if conn.in_node in self.values:
                            incoming_sum += self.values[conn.in_node] * conn.weight
                            has_input = True

                if has_input:
                    activated_val = config.sigmoid(incoming_sum)
                    if node.id not in self.values or abs(self.values[node.id] - activated_val) > 0.01:
                        self.values[node.id] = activated_val
                        state_changed = True
            if not state_changed: break

        output_nodes = sorted([n for n in self.genome.nodes if n.type == 'OUTPUT'], key=lambda x: x.id)
        return [self.values.get(n.id, 0.0) for n in output_nodes]