# genes.py
class ConnectionGene:
    def __init__(self, in_node, out_node, weight, enabled, innovation):
        self.in_node = in_node # D'où ça part
        self.out_node = out_node # Où ça arrive
        self.weight = weight # La force (Synapse)
        self.enabled = enabled # Actif ou Pas ?
        self.innovation = innovation # Num d'innovation

    def copy(self):
        return ConnectionGene(self.in_node, self.out_node, self.weight, self.enabled, self.innovation)


class NodeGene:
    def __init__(self, id, type):
        self.id = id
        self.type = type  # 'INPUT', 'HIDDEN', 'OUTPUT'

    def copy(self):
        return NodeGene(self.id, self.type)