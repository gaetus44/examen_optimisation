# genome.py
import random
import config
from genes import ConnectionGene, NodeGene


class Genome:
    """
        Représente le 'plan de construction' (Génotype) d'un réseau de neurones.
        Il contient la liste des nœuds et des connexions qui évoluent au fil du temps.
        """
    def __init__(self, id):
        """
                Crée une topologie de départ minimaliste :
                Aucun neurone caché, seulement des connexions directes Entrées -> Sorties.
                NEAT commence simple et complexifie ensuite.
                """
        self.id = id
        self.nodes = []
        self.connections = []
        self.fitness = 0.0
        self.adjusted_fitness = 0.0

    def init_simple(self, num_inputs, num_outputs, innovation_counter):
        # 1. Création des nœuds d'entrée
        for i in range(num_inputs):
            self.nodes.append(NodeGene(i, 'INPUT'))
        # 2. Création des nœuds de sortie
        for i in range(num_outputs):
            self.nodes.append(NodeGene(num_inputs + i, 'OUTPUT'))
        # 3. Connexion totale (Fully Connected) initiale avec poids aléatoires
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
        # On trie les connexions par numéro d'innovation pour aligner l'historique génétique
        genes1 = sorted(self.connections, key=lambda c: c.innovation)
        genes2 = sorted(other.connections, key=lambda c: c.innovation)

        if not genes1 or not genes2: return 0

        # Vérification des gènes en excès (ceux apparus plus tard dans l'histoire)
        highest_innov1 = genes1[-1].innovation
        highest_innov2 = genes2[-1].innovation
        if highest_innov1 < highest_innov2:
            genes1, genes2 = genes2, genes1 # On s'assure que genes1 a l'innovation la plus haute


        idx1, idx2 = 0, 0
        disjoint, excess, matching = 0, 0, 0
        weight_diff = 0

        # Comparaison gène par gène (comme un diff de fichier)
        while idx1 < len(genes1) and idx2 < len(genes2):
            c1, c2 = genes1[idx1], genes2[idx2]
            if c1.innovation == c2.innovation:
                # Gènes identiques (Matching) : On compare juste le poids
                weight_diff += abs(c1.weight - c2.weight)
                matching += 1
                idx1 += 1
                idx2 += 1
            elif c1.innovation < c2.innovation:
                # Disjoint : Gène présent chez l'un mais pas l'autre (au milieu de la chaîne)
                disjoint += 1
                idx1 += 1
            else:
                disjoint += 1
                idx2 += 1

        # Les gènes restants à la fin de la liste la plus longue sont des 'Excess'
        excess = len(genes1) - idx1

        # Normalisation par la taille du génome (pour ne pas pénaliser les gros cerveaux)
        N = max(len(genes1), len(genes2))
        if N < 20: N = 1

        avg_weight = weight_diff / matching if matching > 0 else 0

        # Formule finale de compatibilité (c1*E + c2*D + c3*W)
        return (config.COEFF_EXCESS * excess / N) + (config.COEFF_DISJOINT * disjoint / N) + (
                    config.COEFF_WEIGHT * avg_weight)

    def mutate(self, innovation_counter):
        """Gère les 3 types de mutations possibles"""

        # 1. Mutation des Poids (Weight Mutation) - La plus fréquente
        # Permet l'apprentissage fin sans changer la structure.
        if random.random() < config.PROB_MUTATE_WEIGHT:
            for conn in self.connections:
                if random.random() < 0.1:
                    # Remplacement total du poids (choc brutal)
                    conn.weight = random.uniform(-config.WEIGHT_RANDOM_STRENGTH, config.WEIGHT_RANDOM_STRENGTH)
                else:
                    # Légère perturbation (apprentissage continu)
                    conn.weight += random.gauss(0, 1) * 0.5
                    conn.weight = max(min(conn.weight, 8.0), -8.0) # Clamp pour éviter l'explosion

        # 2. Mutation Structurelle : Ajout de Connexion
        if random.random() < config.PROB_ADD_CONNECTION:
            self.mutate_add_connection(innovation_counter)

        # 3. Mutation Structurelle : Ajout de Nœud (Complexification)
        if random.random() < config.PROB_ADD_NODE:
            self.mutate_add_node(innovation_counter)

    def mutate_add_connection(self, innovation_counter):
        """Crée un nouveau lien (synapse) entre deux neurones existants non connectés."""
        n1, n2 = random.choice(self.nodes), random.choice(self.nodes)

        # Vérifications de validité (pas d'entrée vers entrée, pas de boucle sur soi-même)
        if n2.type == 'INPUT' or n1.id == n2.id: return

        # Vérifie si la connexion existe déjà
        for c in self.connections:
            if c.in_node == n1.id and c.out_node == n2.id: return

        # Création et ajout avec un nouveau numéro d'innovation
        innov = innovation_counter.get_innovation(n1.id, n2.id)
        self.connections.append(ConnectionGene(n1.id, n2.id, random.uniform(-1, 1), True, innov))

    def mutate_add_node(self, innovation_counter):
        """
                Insère un neurone caché au milieu d'une connexion existante.
                Exemple : A -> B devient A -> Nouveau -> B
                """
        enabled_conns = [c for c in self.connections if c.enabled]
        if not enabled_conns: return
        conn = random.choice(enabled_conns)
        conn.enabled = False # On désactive l'ancienne connexion directe
        new_id = max(n.id for n in self.nodes) + 1
        self.nodes.append(NodeGene(new_id, 'HIDDEN'))

        # --- Astuce NEAT pour conserver le comportement ---
        # 1. Connexion Entrante (A -> Nouveau) : Poids de 1.0
        self.connections.append(
            ConnectionGene(conn.in_node, new_id, 1.0, True, innovation_counter.get_innovation(conn.in_node, new_id)))

        # 2. Connexion Sortante (Nouveau -> B) : Poids de l'ancienne connexion
        # Résultat : 1.0 * AncienPoids = AncienPoids. Le signal est préservé.
        self.connections.append(ConnectionGene(new_id, conn.out_node, conn.weight, True,
                                               innovation_counter.get_innovation(new_id, conn.out_node)))

    @staticmethod
    def crossover(p1, p2):
        """
                Reproduction sexuée : Combine les gènes de deux parents.
                Les gènes alignés (même innovation) sont hérités au hasard.
                Les gènes disjoints/excess sont hérités du parent le plus 'fit'.
                """
        offspring = Genome(0)

        # Copie de tous les nœuds nécessaires
        all_nodes = {n.id: n.copy() for n in p1.nodes}
        for n in p2.nodes:
            if n.id not in all_nodes: all_nodes[n.id] = n.copy()
        offspring.nodes = list(all_nodes.values())

        # Alignement des connexions par ID d'innovation
        g1 = {c.innovation: c for c in p1.connections}
        g2 = {c.innovation: c for c in p2.connections}

        # On parcourt toutes les innovations présentes chez les deux parents
        for innov in sorted(set(g1.keys()) | set(g2.keys())):
            c1, c2 = g1.get(innov), g2.get(innov)
            if c1 and c2:
                # Gène commun : on choisit au hasard l'un ou l'autre
                offspring.connections.append((c1 if random.random() > 0.5 else c2).copy())
            elif c1:
                # Gène présent uniquement chez P1 (supposé être le meilleur parent ici)
                offspring.connections.append(c1.copy())
            # Note : Si c2 existe mais pas c1, on ne le prend pas (on ne garde que les traits du meilleur parent, ici P1)
        return offspring