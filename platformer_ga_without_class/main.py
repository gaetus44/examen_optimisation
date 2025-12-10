import pygame
import sys

# --- CONFIGURATION ---
TILE_SIZE = 60
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)
RED = (200, 50, 50)  # Goal
GREEN = (50, 200, 50)  # Start
BLUE = (50, 100, 250)  # Creature
CYAN = (0, 255, 255)  # Choix possibles (Au sol)
ORANGE = (255, 165, 0)  # Mouvement forcé (En l'air)


# --- CLASSES ---

class Level:
    def __init__(self, filepath):
        self.obstacles = set()
        self.n_ticks = 0
        self.width = 0
        self.height = 0
        self.start_pos = (0, 0)
        self.goal_pos = (0, 0)
        self.load_from_file(filepath)

    def load_from_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                lines = [l.strip() for l in f if l.strip()]

            self.n_ticks = int(lines[0])
            self.width, self.height = map(int, lines[1].split())
            self.start_pos = tuple(map(int, lines[2].split()))
            self.goal_pos = tuple(map(int, lines[3].split()))

            for line in lines[4:]:
                parts = list(map(int, line.split()))
                if len(parts) >= 2:
                    self.obstacles.add((parts[0], parts[1]))

        except Exception as e:
            print(f"Erreur lecture fichier: {e}")
            sys.exit()

    def is_obstacle(self, x, y):
        return (x, y) in self.obstacles

    def is_out_of_bounds(self, x, y):
        return x < 0 or x >= self.width or y < 0 or y >= self.height

    def is_valid_position(self, x, y):
        return not self.is_out_of_bounds(x, y) and not self.is_obstacle(x, y)


class Creature:
    def __init__(self, level):
        self.level = level
        self.x, self.y = level.start_pos
        self.vx = 0
        self.is_dead = False
        self.reached_goal = False
        self.tick = 0
        self.path = [(self.x, self.y)]

    def is_in_air(self):
        # En l'air si y > 0 ET pas d'obstacle en dessous
        if self.y > 0:
            return not self.level.is_obstacle(self.x, self.y - 1)
        return False

    def get_possible_moves(self):
        """
        Retourne une liste de dictionnaires :
        [{'x': int, 'y': int, 'vx': int, 'type': 'ground'|'air'}]
        """
        moves = []

        if self.is_dead or self.reached_goal:
            return moves

        # --- CAS 1 : EN L'AIR (Mouvement Forcé) ---
        if self.is_in_air():
            # Calcul théorique de la destination
            next_x = self.x + self.vx
            next_y = self.y - 1

            final_x = next_x
            final_y = next_y
            final_vx = self.vx

            # Collision latérale (fix précédent)
            if self.vx != 0 and not self.level.is_valid_position(self.x + self.vx, self.y):
                final_x = self.x
                final_vx = 0
            # Sinon, on vérifie la case d'arrivée normale
            elif not self.level.is_valid_position(next_x, next_y):
                if self.level.is_valid_position(self.x, next_y):
                    final_x = self.x
                else:
                    final_y = self.y
                    final_vx = 0

            if final_y < 0: final_y = 0

            moves.append({
                'x': final_x, 'y': final_y, 'vx': final_vx, 'type': 'air'
            })

        # --- CAS 2 : AU SOL (Choix du joueur) ---
        else:
            actions = [
                (0, 0), (-1, 0), (1, 0),  # Sur place, Gauche, Droite
                (0, 1), (-1, 1), (1, 1),  # Sauts (Haut, Gauche, Droite)
                (-1, -1), (1, -1), (0, -1)  # Bas-Gauche, Bas-Droite, Bas
            ]

            for dx, dy in actions:
                target_x = self.x + dx
                target_y = self.y + dy
                new_vx = dx if dx != 0 else 0

                # 1. Vérification de base : La cible est-elle valide ?
                if not self.level.is_valid_position(target_x, target_y):
                    continue

                # 2. --- CORRECTIF : Vérification des coins (Diagonales) ---
                # Si c'est un mouvement diagonal (dx et dy ne sont pas 0)
                if dx != 0 and dy != 0:
                    # Règle : Pour sauter en diagonale vers le HAUT,
                    # il ne faut pas avoir de plafond direct au-dessus.
                    if dy == 1 and self.level.is_obstacle(self.x, self.y + 1):
                        continue # Plafond bloquant, on saute cette action

                    # Règle : Pour descendre en diagonale vers le BAS,
                    # il ne faut pas avoir de mur direct sur le côté vers lequel on va.
                    if dy == -1 and self.level.is_obstacle(self.x + dx, self.y):
                        continue # Mur bloquant le passage, on saute

                # Si toutes les vérifications passent, on ajoute le coup
                moves.append({
                    'x': target_x,
                    'y': target_y,
                    'vx': new_vx,
                    'type': 'ground'
                })

        return moves

    def apply_move(self, move):
        self.x = move['x']
        self.y = move['y']
        self.vx = move['vx']
        self.tick += 1
        self.path.append((self.x, self.y))

        if (self.x, self.y) == self.level.goal_pos:
            self.reached_goal = True
            print(">>> GAGNÉ ! <<<")

        if self.y == 0 and self.level.is_out_of_bounds(self.x, -1):
            pass


# --- VISUALISATION ---

def to_screen(gx, gy, h):
    # Convertit coordonnées grille (y=0 en bas) vers écran (y=0 en haut)
    return gx * TILE_SIZE, (h - 1 - gy) * TILE_SIZE


def draw(screen, level, creature, moves):
    screen.fill(BLACK)

    # Niveau
    for y in range(level.height):
        for x in range(level.width):
            sx, sy = to_screen(x, y, level.height)
            rect = pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, (40, 40, 40), rect, 1)

            if level.is_obstacle(x, y):
                pygame.draw.rect(screen, GRAY, rect)
            elif (x, y) == level.start_pos:
                pygame.draw.rect(screen, GREEN, rect)
            elif (x, y) == level.goal_pos:
                pygame.draw.rect(screen, RED, rect)

    # Prédictions (Cases possibles)
    for m in moves:
        sx, sy = to_screen(m['x'], m['y'], level.height)
        s_center = (sx + TILE_SIZE // 2, sy + TILE_SIZE // 2)
        color = ORANGE if m['type'] == 'air' else CYAN

        # On dessine un "fantôme" (cercle vide)
        pygame.draw.circle(screen, color, s_center, TILE_SIZE // 2 - 2, 2)

    # Créature
    cx, cy = to_screen(creature.x, creature.y, level.height)
    pygame.draw.circle(screen, BLUE, (cx + TILE_SIZE // 2, cy + TILE_SIZE // 2), TILE_SIZE // 3)

    # Infos texte
    font = pygame.font.SysFont("Arial", 18)
    state_txt = "EN L'AIR" if creature.is_in_air() else "AU SOL"
    info = f"Tick: {creature.tick}/{level.n_ticks} | {state_txt} | VX: {creature.vx}"
    surf = font.render(info, True, WHITE)
    screen.blit(surf, (10, 10))


def main():
    try:
        lvl = Level("level.txt")
    except FileNotFoundError:
        print("Erreur: Le fichier 'level.txt' est manquant dans le dossier du projet.")
        return

    creature = Creature(lvl)

    pygame.init()
    screen = pygame.display.set_mode((lvl.width * TILE_SIZE, lvl.height * TILE_SIZE))
    pygame.display.set_caption("Mode Manuel - Debug Physique")
    clock = pygame.time.Clock()

    running = True
    while running:
        # 1. Calculer les coups possibles pour ce tour
        possible_moves = creature.get_possible_moves()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                clicked_gx = mx // TILE_SIZE
                clicked_gy = (lvl.height - 1) - (my // TILE_SIZE)

                chosen_move = None
                for m in possible_moves:
                    if m['x'] == clicked_gx and m['y'] == clicked_gy:
                        chosen_move = m
                        break

                if not chosen_move and creature.is_in_air() and possible_moves:
                    chosen_move = possible_moves[0]

                if chosen_move:
                    creature.apply_move(chosen_move)
                    print(f"Move -> {chosen_move}")

        draw(screen, lvl, creature, possible_moves)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()