import math


class Game:
    def __init__(self, level_file):
        self.width = 0
        self.height = 0
        self.start_pos = (0, 0)
        self.goal_pos = (0, 0)
        self.obstacles = set()
        self.max_ticks = 0
        self.load_level(level_file)

    def load_level(self, filename):
        with open(filename, 'r') as f:
            lines = f.read().splitlines()

        # Lecture sécurisée du nombre de ticks
        line0 = lines[0].split(']')[-1].strip()
        self.max_ticks = int(line0)

        self.width, self.height = map(int, lines[1].split())
        self.start_pos = tuple(map(int, lines[2].split()))
        self.goal_pos = tuple(map(int, lines[3].split()))

        for line in lines[4:]:
            if line.strip():
                parts = list(map(int, line.split()))
                if len(parts) >= 2:
                    self.obstacles.add((parts[0], parts[1]))

    def is_obstacle(self, x, y):
        # Les bords du niveau sont des murs infinis
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return (x, y) in self.obstacles

    def _run_physics(self, moves, record_path=False):
        x, y = self.start_pos
        path = [(x, y)] if record_path else None

        vx, vy = 0, 0
        limit = min(self.max_ticks, len(moves))

        for t in range(limit):
            is_on_ground = self.is_obstacle(x, y - 1)

            if not is_on_ground:
                # --- EN L'AIR ---
                # 1. Gravité
                vy -= 1

                # 2. Mouvement X (Inertie conservée)
                next_x = x + vx
                if self.is_obstacle(next_x, y):
                    vx = 0  # Mur : on s'arrête net en X
                    # x ne change pas
                else:
                    x = next_x

                # 3. Mouvement Y (Chute/Saut)
                next_y = y + vy
                if self.is_obstacle(x, next_y):
                    vy = 0  # Sol ou Plafond : on s'arrête net en Y
                    # y ne change pas
                else:
                    y = next_y

            else:
                # --- AU SOL ---
                vy = 0
                vx = 0

                move = moves[t]
                dx, dy = 0, 0
                jump = False

                # Décodage des gènes
                if move == 1:  # Left
                    dx = -1;
                    vx = -1
                elif move == 2:  # Right
                    dx = 1;
                    vx = 1
                elif move == 3:  # Jump Up
                    jump = True
                elif move == 4:  # Jump Left
                    dx = -1;
                    vx = -1
                    jump = True
                elif move == 5:  # Jump Right
                    dx = 1;
                    vx = 1
                    jump = True

                if jump:
                    # --- CORRECTION CRITIQUE ---
                    # On vérifie le plafond direct
                    if not self.is_obstacle(x, y + 1):
                        dy = 1
                        vy = 1  # IMPÉRATIF : 1 seule case de force
                    else:
                        dy = 0
                        vy = 0

                # Application du mouvement initial (si pas de mur direct)
                if not self.is_obstacle(x + dx, y + dy):
                    x += dx
                    y += dy
                else:
                    # Si on bute contre un mur au décollage, on reste sur place
                    vx = 0

            if record_path:
                path.append((x, y))

            if (x, y) == self.goal_pos:
                break

        if record_path:
            return path
        else:
            return self.calculate_score(x, y)

    def simulate(self, moves):
        return self._run_physics(moves, record_path=False)

    def get_trajectory(self, moves):
        return self._run_physics(moves, record_path=True)

    def calculate_score(self, final_x, final_y):
        d = math.sqrt((final_x - self.goal_pos[0]) ** 2 + (final_y - self.goal_pos[1]) ** 2)
        return 100.0 * (1.0 / (1.0 + d))