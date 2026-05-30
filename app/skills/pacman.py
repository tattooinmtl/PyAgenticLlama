import pygame
import math
import random
import json
import os

BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE   = (0,   0,   150)
RED    = (255, 0,   0)
PINK   = (255, 105, 180)
ORANGE = (255, 165, 0)
CYAN   = (0,   255, 255)
DBLUE  = (0,   0,   200)

TILE   = 30
COLS   = 20
ROWS   = 18
WIDTH  = COLS * TILE
HEIGHT = ROWS * TILE + 40

SCORES_FILE = os.path.join(os.path.dirname(__file__), 'pacman_scores.json')

MAP = []  # replaced each level by generate_map()


def generate_map(level=1):
    grid = [[1] * COLS for _ in range(ROWS)]

    # DFS maze on odd-coordinate cells
    cell_cols = list(range(1, COLS - 1, 2))   # [1,3,...,17]  9 cells
    cell_rows = list(range(1, ROWS - 1, 2))   # [1,3,...,15]  8 cells
    nc, nr = len(cell_cols), len(cell_rows)
    visited = [[False] * nc for _ in range(nr)]

    def carve(ci, ri):
        visited[ri][ci] = True
        grid[cell_rows[ri]][cell_cols[ci]] = 0
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(dirs)
        for dci, dri in dirs:
            nci, nri = ci + dci, ri + dri
            if 0 <= nci < nc and 0 <= nri < nr and not visited[nri][nci]:
                grid[(cell_rows[ri] + cell_rows[nri]) // 2][(cell_cols[ci] + cell_cols[nci]) // 2] = 0
                carve(nci, nri)

    carve(0, 0)

    # Extra connections; fewer at higher levels = tighter maze
    extra = max(8, 22 - level * 2)
    for _ in range(extra):
        ci = random.randint(0, nc - 2)
        ri = random.randint(0, nr - 1)
        grid[cell_rows[ri]][(cell_cols[ci] + cell_cols[ci + 1]) // 2] = 0
    for _ in range(extra):
        ci = random.randint(0, nc - 1)
        ri = random.randint(0, nr - 2)
        grid[(cell_rows[ri] + cell_rows[ri + 1]) // 2][cell_cols[ci]] = 0

    # Enforce border walls
    for x in range(COLS):
        grid[0][x] = grid[ROWS - 1][x] = 1
    for y in range(ROWS):
        grid[y][0] = grid[y][COLS - 1] = 1

    # Ghost house: walls around rows 7-10, cols 8-11; interior = type 4
    for x in range(8, 12):
        grid[7][x]  = 1
        grid[10][x] = 1
    for y in range(8, 10):
        grid[y][8]  = 1
        grid[y][11] = 1
    for gy in range(8, 10):
        for gx in range(9, 11):
            grid[gy][gx] = 4
    # Exit opening in top wall + open corridor above it
    grid[7][9] = grid[7][10] = 0
    grid[6][9] = grid[6][10] = 0
    grid[5][9] = grid[5][10] = 0   # ensure DFS-cell connectivity to exit

    # Power pellets at all 4 corners
    grid[1][1]          = 3
    grid[1][COLS - 2]   = 3
    grid[ROWS - 2][1]   = 3
    grid[ROWS - 2][COLS - 2] = 3

    # Guarantee Pac-Man start tile open
    grid[16][10] = 0

    return grid


def tile_passable(x, y):
    if x < 0 or x >= COLS or y < 0 or y >= ROWS:
        return False
    return MAP[y][x] != 1


class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y  = 10, 16
        self.dir        = (0, 0)
        self.next_dir   = (1, 0)
        self.anim_tick  = 0

    def move(self):
        nx = self.x + self.next_dir[0]
        ny = self.y + self.next_dir[1]
        if tile_passable(nx, ny):
            self.dir = self.next_dir
        nx = self.x + self.dir[0]
        ny = self.y + self.dir[1]
        if tile_passable(nx, ny):
            self.x, self.y = nx, ny
        self.anim_tick += 1

    def draw(self, surface):
        cx = self.x * TILE + TILE // 2
        cy = self.y * TILE + TILE // 2 + 40
        r  = TILE // 2 - 3
        angle_map = {(1, 0): 0, (0, 1): 270, (-1, 0): 180, (0, -1): 90}
        base  = angle_map.get(self.dir, 0)
        mouth = 35 * abs(math.sin(self.anim_tick * 0.15))
        points = [(cx, cy)]
        for deg in range(int(base + mouth), int(base + 360 - mouth) + 1, 4):
            rad = math.radians(deg)
            points.append((cx + r * math.cos(rad), cy - r * math.sin(rad)))
        if len(points) > 2:
            pygame.draw.polygon(surface, YELLOW, points)
        eye_angle = math.radians(base + 60)
        ex = cx + int(r * 0.55 * math.cos(eye_angle))
        ey = cy - int(r * 0.55 * math.sin(eye_angle))
        pygame.draw.circle(surface, BLACK, (ex, ey), 2)


class Ghost:
    def __init__(self, color, sx, sy):
        self.color      = color
        self.sx, self.sy = sx, sy
        self.reset()

    def reset(self):
        self.x, self.y    = self.sx, self.sy
        self.dir          = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.scared       = False
        self.scared_timer = 0

    def move(self, pacman):
        for _ in range(4):
            nx = self.x + self.dir[0]
            ny = self.y + self.dir[1]
            if tile_passable(nx, ny):
                self.x, self.y = nx, ny
                break
            self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        if random.random() < 0.04:
            self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        if self.scared:
            self.scared_timer -= 1
            if self.scared_timer <= 0:
                self.scared = False

    def draw(self, surface):
        cx = self.x * TILE + TILE // 2
        cy = self.y * TILE + TILE // 2 + 40
        r  = TILE // 2 - 3
        color = DBLUE if self.scared else self.color
        pygame.draw.circle(surface, color, (cx, cy - r // 3), r)
        pygame.draw.rect(surface, color, (cx - r, cy - r // 3, r * 2, r + 4))
        wave_w = r // 3
        for i in range(3):
            wx = cx - r + i * wave_w * 2
            wy = cy + r - r // 3 + 4
            pygame.draw.circle(surface, BLACK, (wx + wave_w, wy), wave_w // 2 + 1)
        if not self.scared:
            for ex_off in (-4, 4):
                pygame.draw.circle(surface, WHITE, (cx + ex_off, cy - r // 2), 3)
                pygame.draw.circle(surface, DBLUE,  (cx + ex_off, cy - r // 2), 1)
        else:
            pygame.draw.line(surface, WHITE, (cx - 4, cy - r // 2 + 2), (cx + 4, cy - r // 2 + 2), 1)


class Game:
    def __init__(self, screen, clock, font):
        self.screen = screen
        self.clock  = clock
        self.font   = font
        self.full_reset()

    def full_reset(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.reset_level()

    def reset_level(self):
        global MAP
        MAP = generate_map(self.level)
        self.pacman = Pacman()
        self.ghosts = [
            Ghost(RED,    9,  8),
            Ghost(PINK,   10, 8),
            Ghost(ORANGE, 9,  9),
            Ghost(CYAN,   10, 9),
        ]
        self.dots   = set()
        self.powers = set()
        self._build_dots()

    def next_level(self):
        self.level += 1
        self.reset_level()

    def _build_dots(self):
        self.dots.clear()
        self.powers.clear()
        for ry, row in enumerate(MAP):
            for rx, cell in enumerate(row):
                if cell == 0:
                    self.dots.add((rx, ry))
                elif cell == 3:
                    self.powers.add((rx, ry))

    def update(self):
        self.pacman.move()
        px, py = self.pacman.x, self.pacman.y

        if (px, py) in self.dots:
            self.dots.discard((px, py))
            self.score += 10

        if (px, py) in self.powers:
            self.powers.discard((px, py))
            self.score += 50
            for g in self.ghosts:
                g.scared       = True
                g.scared_timer = 180

        for g in self.ghosts:
            g.move(self.pacman)

        for g in self.ghosts:
            if g.x == px and g.y == py:
                if g.scared:
                    g.reset()
                    self.score += 200
                else:
                    self.lives -= 1
                    if self.lives <= 0:
                        return 'gameover'
                    self.pacman.reset()
                    for gh in self.ghosts:
                        gh.reset()
                    pygame.time.wait(1000)
                break

        if not self.dots and not self.powers:
            return 'win'
        return 'playing'

    def draw(self):
        self.screen.fill(BLACK)

        for ry, row in enumerate(MAP):
            for rx, cell in enumerate(row):
                rx_px = rx * TILE
                ry_px = ry * TILE + 40
                if cell == 1:
                    pygame.draw.rect(self.screen, BLUE,
                                     (rx_px + 1, ry_px + 1, TILE - 2, TILE - 2))
                    pygame.draw.rect(self.screen, DBLUE,
                                     (rx_px + 1, ry_px + 1, TILE - 2, TILE - 2), 1)

        for dx, dy in self.dots:
            pygame.draw.circle(self.screen, WHITE,
                               (dx * TILE + TILE // 2, dy * TILE + TILE // 2 + 40), 3)

        pulse = int(6 + 2 * math.sin(pygame.time.get_ticks() * 0.005))
        for px2, py2 in self.powers:
            pygame.draw.circle(self.screen, WHITE,
                               (px2 * TILE + TILE // 2, py2 * TILE + TILE // 2 + 40), pulse)

        for g in self.ghosts:
            g.draw(self.screen)
        self.pacman.draw(self.screen)

        pygame.draw.rect(self.screen, (20, 20, 20), (0, 0, WIDTH, 38))
        score_txt = self.font.render(f"Score: {self.score}", True, WHITE)
        level_txt = self.font.render(f"LVL {self.level}", True, YELLOW)
        lives_txt = self.font.render(f"Lives: {'♥ ' * self.lives}", True, RED)
        self.screen.blit(score_txt, (10, 8))
        self.screen.blit(level_txt, (WIDTH // 2 - level_txt.get_width() // 2, 8))
        self.screen.blit(lives_txt, (WIDTH - 140, 8))

        pygame.display.flip()


# ── High-score helpers ─────────────────────────────────────────────

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_scores(scores):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f)


def is_high_score(score, scores):
    return score > 0 and (len(scores) < 5 or score > scores[-1]['score'])


def add_score(name, score, level, scores):
    scores.append({'name': name, 'score': score, 'level': level})
    scores.sort(key=lambda e: e['score'], reverse=True)
    return scores[:5]


# ── Name entry (3-letter arcade style) ────────────────────────────

class NameEntry:
    def __init__(self):
        self.chars = ['A', 'A', 'A']
        self.pos   = 0

    def handle_key(self, key):
        c = ord(self.chars[self.pos]) - ord('A')
        if key == pygame.K_UP:
            self.chars[self.pos] = chr(ord('A') + (c - 1) % 26)
        elif key == pygame.K_DOWN:
            self.chars[self.pos] = chr(ord('A') + (c + 1) % 26)
        elif key == pygame.K_LEFT and self.pos > 0:
            self.pos -= 1
        elif key in (pygame.K_RIGHT, pygame.K_TAB) and self.pos < 2:
            self.pos += 1
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return True
        return False

    def get_name(self):
        return ''.join(self.chars)

    def draw(self, screen, font, score):
        screen.fill(BLACK)
        big = pygame.font.Font(None, 52)
        t1 = big.render("NEW HIGH SCORE!", True, YELLOW)
        t2 = font.render(f"Score: {score}", True, WHITE)
        t3 = font.render("ENTER YOUR NAME", True, WHITE)
        screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 4 - 20))
        screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 4 + 36))
        screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 - 60))

        letter_font = pygame.font.Font(None, 80)
        for i, ch in enumerate(self.chars):
            x = WIDTH // 2 - 72 + i * 60
            y = HEIGHT // 2 - 10
            color = YELLOW if i == self.pos else WHITE
            ltr = letter_font.render(ch, True, color)
            screen.blit(ltr, (x, y))
            if i == self.pos:
                pygame.draw.rect(screen, YELLOW, (x - 4, y - 4, 52, 68), 2)

        hint = font.render("UP/DOWN: letter    LEFT/RIGHT: move    ENTER: confirm", True, (130, 130, 130))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 80))
        pygame.display.flip()


# ── Screen helpers ─────────────────────────────────────────────────

def draw_scores_block(screen, font, scores, y_start):
    """Render up to 5 score rows at y_start."""
    if not scores:
        txt = font.render("No scores yet!", True, (130, 130, 130))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y_start))
        return
    medals = ['★', '2.', '3.', '4.', '5.']
    for i, entry in enumerate(scores):
        color = YELLOW if i == 0 else WHITE
        line  = font.render(
            f"{medals[i]:<3} {entry['name']}   {entry['score']:>6}   LVL {entry['level']}",
            True, color
        )
        screen.blit(line, (WIDTH // 2 - line.get_width() // 2, y_start + i * 36))


def draw_highscores(screen, font, scores):
    screen.fill(BLACK)
    big = pygame.font.Font(None, 52)
    t = big.render("HIGH SCORES", True, YELLOW)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 24))
    draw_scores_block(screen, font, scores, 90)
    hint = font.render("Press R to play again", True, (130, 130, 130))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 46))
    pygame.display.flip()


def draw_gameover(screen, font, game, scores):
    screen.fill(BLACK)
    big = pygame.font.Font(None, 60)
    t1 = big.render("GAME OVER", True, RED)
    t2 = font.render(f"Score: {game.score}   Level: {game.level}", True, WHITE)
    screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, 28))
    screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 88))
    sep = font.render("─── HIGH SCORES ───", True, YELLOW)
    screen.blit(sep, (WIDTH // 2 - sep.get_width() // 2, 130))
    draw_scores_block(screen, font, scores, 166)
    hint = font.render("Press R to restart", True, (130, 130, 130))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 46))
    pygame.display.flip()


def draw_level_complete(screen, font, level, score):
    screen.fill(BLACK)
    big = pygame.font.Font(None, 56)
    t1 = big.render(f"LEVEL {level} COMPLETE!", True, YELLOW)
    t2 = font.render(f"Score: {score}", True, WHITE)
    t3 = font.render("Get ready...", True, (130, 130, 130))
    screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 10))
    screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 50))
    pygame.display.flip()


# ── Entry point ───────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pac-Man")
    clock  = pygame.time.Clock()
    font   = pygame.font.Font(None, 32)

    scores     = load_scores()
    game       = Game(screen, clock, font)
    state      = 'playing'
    name_entry = None
    lvl_flash  = 0   # frames left for level-complete screen

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if state == 'playing':
                    if event.key in (pygame.K_UP,    pygame.K_w): game.pacman.next_dir = (0, -1)
                    elif event.key in (pygame.K_DOWN,  pygame.K_s): game.pacman.next_dir = (0,  1)
                    elif event.key in (pygame.K_LEFT,  pygame.K_a): game.pacman.next_dir = (-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d): game.pacman.next_dir = (1,  0)

                elif state == 'entering_name':
                    if name_entry.handle_key(event.key):
                        scores = add_score(name_entry.get_name(), game.score, game.level, scores)
                        save_scores(scores)
                        name_entry = None
                        state = 'highscores'

                if event.key == pygame.K_r and state in ('gameover', 'highscores'):
                    game.full_reset()
                    state = 'playing'

        # ── State machine ──────────────────────────────────────────
        if state == 'playing':
            result = game.update()
            if result == 'win':
                lvl_flash = 25   # 2.5 s at 10 fps
                state = 'level_complete'
            elif result == 'gameover':
                if is_high_score(game.score, scores):
                    name_entry = NameEntry()
                    state = 'entering_name'
                else:
                    state = 'gameover'
            else:
                game.draw()

        elif state == 'level_complete':
            draw_level_complete(screen, font, game.level, game.score)
            lvl_flash -= 1
            if lvl_flash <= 0:
                game.next_level()
                state = 'playing'

        elif state == 'gameover':
            draw_gameover(screen, font, game, scores)

        elif state == 'highscores':
            draw_highscores(screen, font, scores)

        elif state == 'entering_name':
            name_entry.draw(screen, font, game.score)

        clock.tick(10)


if __name__ == "__main__":
    main()
