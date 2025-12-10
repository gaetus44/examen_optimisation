import pygame
import sys
import os
from game import Game
from simple_genetic_algorithm import SimpleGeneticAlgorithm
from population import Population

# --- CONFIGURATION GRAPHIQUE ---
TILE_SIZE = 40
COLOR_BG = (255, 255, 255)
COLOR_WALL = (50, 50, 50)
COLOR_PLAYER = (50, 150, 255)
COLOR_START = (100, 200, 100)
COLOR_GOAL = (255, 50, 50)
FPS = 5  # Plus rapide pour voir l'évolution

# --- PARAMÈTRES GA ---
POPULATION_SIZE = 200
MAX_GENERATION = 200


def run_visualization():
    # 1. Charger le niveau
    level_path = "level.txt"
    if not os.path.exists(level_path):
        print("Erreur: level.txt manquant")
        return

    game = Game(level_path)

    # 2. Initialiser l'Algo Génétique
    ga = SimpleGeneticAlgorithm(game, selection_type="tournament")

    # Création de la première population
    current_population = Population(POPULATION_SIZE, True)
    generation_count = 1

    best_indiv = current_population.get_fittest(game)
    trajectory = game.get_trajectory(best_indiv.genes)

    # 3. Initialiser Pygame
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 20, bold=True)

    screen_width = game.width * TILE_SIZE
    screen_height = game.height * TILE_SIZE + 60
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Projet 3: Visualisation GA")
    clock = pygame.time.Clock()

    running = True
    tick_index = 0
    evolution_finished = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- DESSIN ---
        screen.fill(COLOR_BG)

        for y in range(game.height):
            for x in range(game.width):
                draw_y = game.height - 1 - y
                rect = pygame.Rect(x * TILE_SIZE, draw_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if game.is_obstacle(x, y):
                    pygame.draw.rect(screen, COLOR_WALL, rect)
                    pygame.draw.rect(screen, (0, 0, 0), rect, 1)

                if (x, y) == game.start_pos:
                    pygame.draw.rect(screen, COLOR_START, rect.inflate(-10, -10))

                if (x, y) == game.goal_pos:
                    pygame.draw.rect(screen, COLOR_GOAL, rect.inflate(-10, -10))

        # --- JOUEUR ---
        if tick_index < len(trajectory):
            px, py = trajectory[tick_index]
            draw_py = game.height - 1 - py
            player_rect = pygame.Rect(px * TILE_SIZE, draw_py * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.circle(screen, COLOR_PLAYER, player_rect.center, TILE_SIZE // 2 - 2)
            tick_index += 1
        else:
            # FIN ANIMATION -> EVOLUTION
            if not evolution_finished and generation_count < MAX_GENERATION:
                if best_indiv.get_fitness(game) >= 99.0:
                    print("Solution trouvée !")
                    evolution_finished = True
                else:
                    current_population = ga.evolve_population(current_population)
                    generation_count += 1
                    best_indiv = current_population.get_fittest(game)
                    trajectory = game.get_trajectory(best_indiv.genes)
                    tick_index = 0
                    print(f"Gen {generation_count} -> Best Score: {best_indiv.get_fitness(game):.2f}")
            else:
                tick_index = 0

        # --- UI ---
        pygame.draw.rect(screen, (30, 30, 30), (0, game.height * TILE_SIZE, screen_width, 60))
        info_text = f"Gen: {generation_count} | Score: {best_indiv.get_fitness(game):.2f} / 100"
        if evolution_finished: info_text += " (TERMINÉ)"
        text_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (20, game.height * TILE_SIZE + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_visualization()