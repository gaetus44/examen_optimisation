import config


class FeedForwardNetwork:
    def __init__(self, genome):
        self.genome = genome
        # Trier les nœuds pour s'assurer que les calculs se font dans l'ordre (simplifié)
        # Pour une vraie implémentation robuste, il faudrait un tri topologique.
        # Ici, on va faire une méthode "lazy" : on itère plusieurs fois pour propager.
        self.values = {}

    def activate(self, inputs):
        # Reset et charger les inputs
        self.values = {}
        input_nodes = [n for n in self.genome.nodes if n.type == 'INPUT']

        # On suppose que les IDs des inputs sont 0, 1, 2...
        if len(inputs) != len(input_nodes):
            # Gestion d'erreur simplifiée
            pass

        for i, val in enumerate(inputs):
            # On cherche le nœud input avec l'ID i (simplification, IDs fixes attendus)
            # 1. On remplit les neurones d'entrée avec les valeurs du jeu
            self.values[i] = val # ID 0 = Input 0, ID 1 = Input 1...

        # Nœud de biais (souvent ID = num_inputs) - Ajoutons un biais virtuel à 1
        self.values['BIAS'] = 1.0

        # Propagation : On boucle 3 fois.
        # C'est une astuce : pour un petit réseau FeedForward, l'info traverse vite.
        # NEAT standard utilise un tri topologique pour faire ça en 1 passe.
        output_nodes = [n for n in self.genome.nodes if n.type == 'OUTPUT']

        # On stocke les activations entrantes
        activations = {}

        nodes_to_process = [n for n in self.genome.nodes if n.type != 'INPUT']
        # Trier par ID assure souvent un semblant d'ordre topologique si IDs sont croissants
        nodes_to_process.sort(key=lambda x: x.id)

        # 1. On remplit les neurones d'entrée avec les valeurs du jeu
        for _ in range(len(self.genome.nodes)):

            state_changed = False
            current_vals = self.values.copy()

            for node in nodes_to_process:
                incoming_sum = 0.0 # La somme de tout ce qui arrive au neurone
                has_input = False

                # Chercher toutes les connexions entrant dans ce nœud
                for conn in self.genome.connections:
                    if not conn.enabled: continue # On ignore les câbles coupés
                    if conn.out_node == node.id:
                        # Si le nœud source a une valeur calculée
                        source_val = 0.0
                        if conn.in_node in current_vals:
                            source_val = current_vals[conn.in_node]
                            has_input = True
                        elif conn.in_node == -1:  # Exemple de handling Biais si géré par ID
                            pass

                        incoming_sum += source_val * conn.weight

                # Si on a reçu quelque chose (ou si c'est un nœud connecté au bias)
                if has_input:
                    # L'ACTIVATION (Sigmoïde)
                    activated_val = config.sigmoid(incoming_sum)
                    if node.id not in self.values or self.values[node.id] != activated_val:
                        self.values[node.id] = activated_val
                        state_changed = True

            # Si plus rien ne bouge on arrete de calculer
            if not state_changed: break

        # Récupérer les sorties
        outputs = []
        for n in output_nodes:
            outputs.append(self.values.get(n.id, 0.0))
        return outputs