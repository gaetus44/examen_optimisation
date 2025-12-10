from simple_genetic_algorithm import SimpleGeneticAlgorithm
from game import Game
import os

if __name__ == "__main__":
    level_path = "level.txt"

    if not os.path.exists(level_path):
        print("Erreur: Le fichier level.txt est introuvable.")
    else:
        # 1. Initialiser le jeu (Environnement)
        my_game = Game(level_path)

        print(f"Niveau chargé: {my_game.width}x{my_game.height}, Max Ticks: {my_game.max_ticks}")
        print(f"Start: {my_game.start_pos}, Goal: {my_game.goal_pos}")

        # 2. Initialiser l'Algo Génétique avec le jeu
        ga = SimpleGeneticAlgorithm(my_game, selection_type="tournament")

        # 3. Lancer l'évolution
        ga.run_algorithm(population_size=50)