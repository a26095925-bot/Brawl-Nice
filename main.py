import math
import random
import sys
import json

import pygame


WIDTH, HEIGHT = 960, 540
FPS = 60

WORLD_WIDTH = 2600
WORLD_HEIGHT = 2600

PLAYER_RADIUS = 18
PLAYER_SPEED = 4
PLAYER_MAX_HP = 100

BULLET_RADIUS = 4
BULLET_SPEED = 10
BULLET_COOLDOWN = 120
BULLET_DAMAGE = 25

BOX_SIZE = 40
BOX_HP = 3
BOX_COUNT = 80

DEPOSIT_SIZE = 42
DEPOSIT_HP = 4
DEPOSIT_TARGET_COUNT = 30
DEPOSIT_RESPAWN_INTERVAL = 4500  # ms

GRASS_COLOR = (46, 139, 87)
MINE_FLOOR_COLOR = (40, 40, 40)
STONE_COLOR = (75, 75, 75)
DEPOSIT_COLOR = (110, 110, 140)

BOT_RADIUS = 18
BOT_SPEED = 3.2
BOT_VIEW_RANGE = 520
BOT_SHOOT_RANGE = 480

MOUSE_AIM_RADIUS = 260

STATE_MENU = "menu"
STATE_SETTINGS = "settings"
STATE_MODE_SELECT = "mode_select"
STATE_GAME = "game"
STATE_PAUSE = "pause"
STATE_SKINS = "skins"
STATE_RESULT = "result"

MODE_CRYSTALS = "crystals"
MODE_LAST_MAN = "last_man"
MODE_MADNESS = "madness"

CONTROL_KEYBOARD = "keyboard"
CONTROL_TOUCH = "touch"

SKINS = {
    "white": {"color": (255, 255, 255), "price": 0},
    "green": {"color": (0, 220, 140), "price": 500},
    "pink": {"color": (255, 110, 200), "price": 1000},
    "red": {"color": (230, 60, 60), "price": 1500},
    "gray": {"color": (160, 160, 160), "price": 2000},
    "black": {"color": (20, 20, 20), "price": 2500},
    "rainbow": {"color": (255, 255, 255), "price": 3000},
}


def random_edge_pos(margin: int = 80):
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        x = random.randint(margin, WORLD_WIDTH - margin)
        y = margin
    elif side == "bottom":
        x = random.randint(margin, WORLD_WIDTH - margin)
        y = WORLD_HEIGHT - margin
    elif side == "left":
        x = margin
        y = random.randint(margin, WORLD_HEIGHT - margin)
    else:
        x = WORLD_WIDTH - margin
        y = random.randint(margin, WORLD_HEIGHT - margin)
    return float(x), float(y)


def create_boxes_grass():
    boxes = []
    attempts = 0
    while len(boxes) < BOX_COUNT and attempts < BOX_COUNT * 30:
        attempts += 1
        x = random.randint(0, WORLD_WIDTH - BOX_SIZE)
        y = random.randint(0, WORLD_HEIGHT - BOX_SIZE)
        rect = pygame.Rect(x, y, BOX_SIZE, BOX_SIZE)
        boxes.append({"rect": rect, "hp": BOX_HP})
    return boxes


def random_deposit_rect():
    x = random.randint(0, WORLD_WIDTH - DEPOSIT_SIZE)
    y = random.randint(0, WORLD_HEIGHT - DEPOSIT_SIZE)
    return pygame.Rect(x, y, DEPOSIT_SIZE, DEPOSIT_SIZE)


def create_mine_deposits():
    deposits = []
    attempts = 0
    while len(deposits) < DEPOSIT_TARGET_COUNT and attempts < DEPOSIT_TARGET_COUNT * 40:
        attempts += 1
        rect = random_deposit_rect()
        deposits.append(
            {"rect": rect, "hp": DEPOSIT_HP, "has_crystal": True, "emerge": 1.0}
        )
    return deposits


def build_grass_world():
    surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
    surface.fill(GRASS_COLOR)
    noise = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
    for _ in range(6000):
        x = random.randint(0, WORLD_WIDTH - 1)
        y = random.randint(0, WORLD_HEIGHT - 1)
        color = random.choice(
            [
                (0, 35, 0, 35),
                (10, 55, 10, 45),
                (20, 70, 20, 40),
            ]
        )
        noise.set_at((x, y), color)
    surface.blit(noise, (0, 0))
    return surface


def build_mine_world():
    surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
    surface.fill(MINE_FLOOR_COLOR)
    noise = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)
    for _ in range(7000):
        x = random.randint(0, WORLD_WIDTH - 1)
        y = random.randint(0, WORLD_HEIGHT - 1)
        color = random.choice(
            [
                (10, 10, 10, 50),
                (35, 35, 35, 50),
                (20, 20, 30, 60),
            ]
        )
        noise.set_at((x, y), color)
    surface.blit(noise, (0, 0))
    return surface


def move_circle(pos, vel, obstacles, radius, speed):
    x, y = pos
    dx, dy = vel
    length = math.hypot(dx, dy)
    if length > 0:
        dx = dx / length * speed
        dy = dy / length * speed

    new_x = x + dx
    new_y = y + dy

    px = new_x
    py = y
    for r in obstacles:
        if circle_rect_collide(px, py, radius, r):
            if dx > 0:
                px = r.left - radius
            elif dx < 0:
                px = r.right + radius
    qx = px
    qy = new_y
    for r in obstacles:
        if circle_rect_collide(qx, qy, radius, r):
            if dy > 0:
                qy = r.top - radius
            elif dy < 0:
                qy = r.bottom + radius

    qx = max(radius, min(WORLD_WIDTH - radius, qx))
    qy = max(radius, min(WORLD_HEIGHT - radius, qy))
    return qx, qy


def circle_rect_collide(cx, cy, radius, rect):
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy < radius * radius


def spawn_bullet(pos, direction, owner_id):
    dx, dy = direction
    length = math.hypot(dx, dy)
    if length == 0:
        return None
    dx /= length
    dy /= length
    x = pos[0] + dx * (PLAYER_RADIUS + BULLET_RADIUS + 4)
    y = pos[1] + dy * (PLAYER_RADIUS + BULLET_RADIUS + 4)
    return {
        "x": x,
        "y": y,
        "dx": dx * BULLET_SPEED,
        "dy": dy * BULLET_SPEED,
        "life": 1100,
        "owner": owner_id,
    }


def draw_text_center(surf, text, font, color, center):
    img = font.render(text, True, color)
    rect = img.get_rect(center=center)
    surf.blit(img, rect)


def draw_button(surf, rect, text, font, hovered):
    base = (25, 25, 30)
    hover = (55, 55, 70)
    border = (230, 230, 230)
    color = hover if hovered else base
    pygame.draw.rect(surf, color, rect, border_radius=10)
    pygame.draw.rect(surf, border, rect, 2, border_radius=10)
    draw_text_center(surf, text, font, (240, 240, 240), rect.center)


def clamp_mouse(center, mouse_pos, radius):
    cx, cy = center
    mx, my = mouse_pos
    dx = mx - cx
    dy = my - cy
    dist = math.hypot(dx, dy)
    if dist == 0 or dist <= radius:
        return mx, my
    k = radius / dist
    return cx + dx * k, cy + dy * k


def make_bot(bot_id, pos):
    return {
        "id": bot_id,
        "x": float(pos[0]),
        "y": float(pos[1]),
        "hp": PLAYER_MAX_HP,
        "aim_dx": 1.0,
        "aim_dy": 0.0,
        "last_shot": 0,
        "crystals": 0,
        "alive": True,
        "target_pos": None,
        "respawn_timer": 0,
        "last_damage": 0,
        "dodge_timer": 0,
        "dodge_dx": 0.0,
        "dodge_dy": 0.0,
        "kills": 0,
        "deaths": 0,
    }


def get_menu_layout(screen):
    sw, sh = screen.get_size()
    play_rect = pygame.Rect(0, 0, 200, 60)
    play_rect.bottomright = (sw - 20, sh - 20)

    settings_rect = pygame.Rect(0, 0, 36, 36)
    settings_rect.topright = (sw - 16, 16)

    exit_rect = pygame.Rect(0, 0, 36, 36)
    exit_rect.topleft = (16, 16)

    skins_rect = pygame.Rect(0, 0, 200, 40)
    skins_rect.midbottom = (sw // 2, sh - 20)

    madness_rect = pygame.Rect(0, 0, 200, 40)
    madness_rect.midbottom = (sw // 2, sh - 70)

    return play_rect, settings_rect, exit_rect, skins_rect, madness_rect


def draw_player_preview(surf, center, color, aim_angle):
    shadow_color = (10, 10, 20, 120)
    shadow = pygame.Surface((PLAYER_RADIUS * 4, PLAYER_RADIUS * 4), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        shadow_color,
        (0, PLAYER_RADIUS * 1.2, PLAYER_RADIUS * 4, PLAYER_RADIUS * 1.4),
    )
    surf.blit(
        shadow,
        (center[0] - PLAYER_RADIUS * 2, center[1] - PLAYER_RADIUS * 0.2),
    )

    pygame.draw.circle(surf, color, center, PLAYER_RADIUS)
    gun_len = 18
    gun_w = 8
    dx = math.cos(aim_angle)
    dy = math.sin(aim_angle)
    base_x = center[0] + dx * (PLAYER_RADIUS - 4)
    base_y = center[1] + dy * (PLAYER_RADIUS - 4)
    end_x = base_x + dx * gun_len
    end_y = base_y + dy * gun_len
    perp_x = -dy
    perp_y = dx
    w = gun_w / 2
    p1 = (base_x + perp_x * w, base_y + perp_y * w)
    p2 = (base_x - perp_x * w, base_y - perp_y * w)
    p3 = (end_x - perp_x * w, end_y - perp_y * w)
    p4 = (end_x + perp_x * w, end_y + perp_y * w)
    pygame.draw.polygon(surf, (30, 30, 30), [p1, p2, p3, p4])


def draw_gun_on_world(surf, px, py, aim_dx, aim_dy, cam_x, cam_y):
    cx = px - cam_x
    cy = py - cam_y
    length = math.hypot(aim_dx, aim_dy)
    if length == 0:
        aim_dx, aim_dy = 1.0, 0.0
    else:
        aim_dx /= length
        aim_dy /= length
    gun_len = 18
    gun_w = 8
    base_x = cx + aim_dx * (PLAYER_RADIUS - 4)
    base_y = cy + aim_dy * (PLAYER_RADIUS - 4)
    end_x = base_x + aim_dx * gun_len
    end_y = base_y + aim_dy * gun_len
    perp_x = -aim_dy
    perp_y = aim_dx
    w = gun_w / 2
    p1 = (base_x + perp_x * w, base_y + perp_y * w)
    p2 = (base_x - perp_x * w, base_y - perp_y * w)
    p3 = (end_x - perp_x * w, end_y - perp_y * w)
    p4 = (end_x + perp_x * w, end_y + perp_y * w)
    pygame.draw.polygon(surf, (30, 30, 30), [p1, p2, p3, p4])


def main():
    pygame.init()
    pygame.display.set_caption("Brawl Nice")

    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("arial", 44)
    font_med = pygame.font.SysFont("arial", 26)
    font_small = pygame.font.SysFont("arial", 18)

    fullscreen = False
    game_state = STATE_MENU
    current_mode = MODE_CRYSTALS

    # --- persistence: coins, скіни, безумство ---
    save_path = "save.json"
    coins = 0
    unlocked_skins = {"white"}
    selected_skin = "white"
    madness_purchased = False

    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        coins = int(data.get("coins", 0))
        unlocked_skins = set(data.get("unlocked_skins", ["white"]))
        if "white" not in unlocked_skins:
            unlocked_skins.add("white")
        selected_skin = data.get("selected_skin", "white")
        madness_purchased = bool(data.get("madness_purchased", False))
    except Exception:
        pass

    def save_profile():
        try:
            data = {
                "coins": coins,
                "unlocked_skins": sorted(list(unlocked_skins)),
                "selected_skin": selected_skin,
                "madness_purchased": madness_purchased,
            }
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            # не ламаємо гру, якщо не вдалося зберегти
            pass

    control_mode = CONTROL_KEYBOARD
    auto_control = True

    if auto_control:
        if sys.platform.startswith("android"):
            control_mode = CONTROL_TOUCH
        else:
            control_mode = CONTROL_KEYBOARD

    grass_world = build_grass_world()
    mine_world = build_mine_world()

    def skin_color(name):
        base = SKINS[name]["color"]
        if name == "rainbow":
            t = pygame.time.get_ticks() / 700.0
            r = int(128 + 127 * math.sin(t))
            g = int(128 + 127 * math.sin(t + 2.1))
            b = int(128 + 127 * math.sin(t + 4.2))
            return (r, g, b)
        return base

    def reset_match(mode):
        px, py = random_edge_pos()
        player = {
            "id": "player",
            "x": float(px),
            "y": float(py),
            "hp": PLAYER_MAX_HP,
            "aim_dx": 1.0,
            "aim_dy": 0.0,
            "last_shot": 0,
            "crystals": 0,
            "alive": True,
            "respawn_timer": 0,
            "last_damage": 0,
            "kills": 0,
            "deaths": 0,
        }
        if mode == MODE_CRYSTALS:
            boxes = []
            deposits = create_mine_deposits()
            bots = []
            for i in range(5):
                bots.append(make_bot(f"bot{i}", random_edge_pos()))
            world = mine_world
        else:
            boxes = create_boxes_grass()
            deposits = []
            bots = []
            for i in range(10):
                bots.append(make_bot(f"bot{i}", random_edge_pos()))
            world = grass_world
        bullets = []
        crystals_items = []
        particles = []
        deposit_spawn_timer = DEPOSIT_RESPAWN_INTERVAL
        return (
            player,
            bots,
            boxes,
            deposits,
            bullets,
            crystals_items,
            particles,
            world,
            deposit_spawn_timer,
        )

    (
        player,
        bots,
        boxes,
        deposits,
        bullets,
        crystals_items,
        particles,
        current_world,
        deposit_spawn_timer,
    ) = reset_match(current_mode)

    last_result = None
    result_stats = None
    damage_flash_timer = 0
    pre_round_timer = 0

    madness_plan = []
    madness_index = 0
    madness_player_wins = 0
    madness_bot_wins = 0
    madness_active = False

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        now_ticks = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            (0, 0),
                            pygame.FULLSCREEN
                            | pygame.HWSURFACE
                            | pygame.DOUBLEBUF,
                        )
                    else:
                        screen = pygame.display.set_mode(
                            (WIDTH, HEIGHT), pygame.RESIZABLE
                        )
                if game_state == STATE_GAME and pre_round_timer <= 0:
                    if event.key == pygame.K_ESCAPE:
                        game_state = STATE_PAUSE
                        pygame.event.set_grab(False)
                        pygame.mouse.set_visible(True)
                elif game_state == STATE_PAUSE:
                    if event.key == pygame.K_ESCAPE:
                        game_state = STATE_GAME
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)

            elif game_state == STATE_MENU and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    (
                        play_r,
                        settings_r,
                        exit_r,
                        skins_r,
                        madness_r,
                    ) = get_menu_layout(screen)
                    if exit_r.collidepoint(mx, my):
                        save_profile()
                        running = False
                    elif settings_r.collidepoint(mx, my):
                        game_state = STATE_SETTINGS
                    elif skins_r.collidepoint(mx, my):
                        game_state = STATE_SKINS
                    elif madness_r.collidepoint(mx, my):
                        if not madness_purchased:
                            if coins >= 1000:
                                coins -= 1000
                                madness_purchased = True
                                save_profile()
                            else:
                                last_result = "no_coins"
                        else:
                            madness_active = True
                            madness_index = 0
                            madness_player_wins = 0
                            madness_bot_wins = 0
                            madness_plan = []
                            for _ in range(3):
                                madness_plan.append(
                                    random.choice([MODE_CRYSTALS, MODE_LAST_MAN])
                                )
                            game_state = STATE_MODE_SELECT
                    elif play_r.collidepoint(mx, my):
                        madness_active = False
                        game_state = STATE_MODE_SELECT

            elif game_state == STATE_MODE_SELECT and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    sw, sh = screen.get_size()
                    back_rect = pygame.Rect(0, 0, 200, 50)
                    back_rect.bottomleft = (20, sh - 20)
                    mode1_rect = pygame.Rect(0, 0, 280, 160)
                    mode2_rect = pygame.Rect(0, 0, 280, 160)
                    mode3_rect = pygame.Rect(0, 0, 280, 100)
                    mode1_rect.center = (sw // 2 - 170, sh // 2)
                    mode2_rect.center = (sw // 2 + 170, sh // 2)
                    mode3_rect.center = (sw // 2, sh // 2 + 200)
                    if back_rect.collidepoint(mx, my):
                        game_state = STATE_MENU
                    elif not madness_active and mode1_rect.collidepoint(mx, my):
                        current_mode = MODE_CRYSTALS
                        (
                            player,
                            bots,
                            boxes,
                            deposits,
                            bullets,
                            crystals_items,
                            particles,
                            current_world,
                            deposit_spawn_timer,
                        ) = reset_match(current_mode)
                        pre_round_timer = 3000
                        player["kills"] = player["deaths"] = 0
                        for b in bots:
                            b["kills"] = b["deaths"] = 0
                        last_result = None
                        game_state = STATE_GAME
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)
                    elif not madness_active and mode2_rect.collidepoint(mx, my):
                        current_mode = MODE_LAST_MAN
                        (
                            player,
                            bots,
                            boxes,
                            deposits,
                            bullets,
                            crystals_items,
                            particles,
                            current_world,
                            deposit_spawn_timer,
                        ) = reset_match(current_mode)
                        pre_round_timer = 3000
                        player["kills"] = player["deaths"] = 0
                        for b in bots:
                            b["kills"] = b["deaths"] = 0
                        last_result = None
                        game_state = STATE_GAME
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)
                    elif madness_active and (mode1_rect.collidepoint(mx, my) or mode2_rect.collidepoint(mx, my) or mode3_rect.collidepoint(mx, my)):
                        current_mode = madness_plan[madness_index]
                        (
                            player,
                            bots,
                            boxes,
                            deposits,
                            bullets,
                            crystals_items,
                            particles,
                            current_world,
                            deposit_spawn_timer,
                        ) = reset_match(current_mode)
                        pre_round_timer = 3000
                        player["kills"] = player["deaths"] = 0
                        for b in bots:
                            b["kills"] = b["deaths"] = 0
                        last_result = None
                        game_state = STATE_GAME
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)

            elif game_state == STATE_SETTINGS and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    sw, sh = screen.get_size()
                    back_rect = pygame.Rect(0, 0, 220, 50)
                    back_rect.center = (sw // 2, sh // 2 + 160)
                    fs_rect = pygame.Rect(0, 0, 320, 55)
                    fs_rect.center = (sw // 2, sh // 2 + 70)
                    control_rect = pygame.Rect(0, 0, 320, 55)
                    control_rect.center = (sw // 2, sh // 2 - 20)
                    auto_rect = pygame.Rect(0, 0, 320, 55)
                    auto_rect.center = (sw // 2, sh // 2 - 110)
                    if back_rect.collidepoint(mx, my):
                        game_state = STATE_MENU
                    elif fs_rect.collidepoint(mx, my):
                        fullscreen = not fullscreen
                        if fullscreen:
                            screen = pygame.display.set_mode(
                                (0, 0),
                                pygame.FULLSCREEN
                                | pygame.HWSURFACE
                                | pygame.DOUBLEBUF,
                            )
                        else:
                            screen = pygame.display.set_mode(
                                (WIDTH, HEIGHT), pygame.RESIZABLE
                            )
                    elif auto_rect.collidepoint(mx, my):
                        auto_control = not auto_control
                        if auto_control:
                            if sys.platform.startswith("android"):
                                control_mode = CONTROL_TOUCH
                            else:
                                control_mode = CONTROL_KEYBOARD
                    elif control_rect.collidepoint(mx, my):
                        if not auto_control:
                            control_mode = (
                                CONTROL_TOUCH
                                if control_mode == CONTROL_KEYBOARD
                                else CONTROL_KEYBOARD
                            )

            elif game_state == STATE_SKINS and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    sw, sh = screen.get_size()
                    back_rect = pygame.Rect(0, 0, 220, 50)
                    back_rect.center = (sw // 2, sh - 60)
                    if back_rect.collidepoint(mx, my):
                        game_state = STATE_MENU
                    else:
                        cols = 3
                        cell_w = 200
                        cell_h = 70
                        start_x = sw // 2 - (cols * cell_w + (cols - 1) * 20) // 2
                        start_y = 140
                        skin_names = list(SKINS.keys())
                        for idx, name in enumerate(skin_names):
                            row = idx // cols
                            col = idx % cols
                            rect = pygame.Rect(
                                start_x + col * (cell_w + 20),
                                start_y + row * (cell_h + 16),
                                cell_w,
                                cell_h,
                            )
                            if rect.collidepoint(mx, my):
                                if name in unlocked_skins:
                                    selected_skin = name
                                else:
                                    price = SKINS[name]["price"]
                                    if coins >= price:
                                        coins -= price
                                        unlocked_skins.add(name)
                                        selected_skin = name

            elif game_state == STATE_RESULT and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    sw, sh = screen.get_size()
                    back_rect = pygame.Rect(0, 0, 220, 50)
                    back_rect.center = (sw // 2, sh - 80)
                    if back_rect.collidepoint(mx, my):
                        game_state = STATE_MENU

        sw, sh = screen.get_size()

        if game_state == STATE_MENU:
            screen.fill((12, 16, 24))
            title_pos = (sw // 2, 90)
            draw_text_center(
                screen, "Brawl Nice", font_big, (240, 240, 240), title_pos
            )

            (
                play_r,
                settings_r,
                exit_r,
                skins_r,
                madness_r,
            ) = get_menu_layout(screen)
            mx, my = pygame.mouse.get_pos()

            pygame.draw.rect(screen, (50, 60, 80), exit_r, border_radius=8)
            pygame.draw.rect(screen, (230, 230, 230), exit_r, 2, border_radius=8)
            draw_text_center(screen, "X", font_small, (230, 230, 230), exit_r.center)

            pygame.draw.rect(screen, (50, 60, 80), settings_r, border_radius=10)
            pygame.draw.rect(
                screen, (230, 230, 230), settings_r, 2, border_radius=10
            )
            cx, cy = settings_r.center
            pygame.draw.circle(screen, (230, 230, 230), (cx, cy), 10, 2)
            pygame.draw.circle(screen, (230, 230, 230), (cx + 7, cy - 1), 3)
            pygame.draw.circle(screen, (230, 230, 230), (cx - 4, cy + 6), 3)

            draw_button(
                screen,
                play_r,
                "Грати",
                font_med,
                play_r.collidepoint(mx, my),
            )

            draw_button(
                screen,
                skins_r,
                "Скіни",
                font_small,
                skins_r.collidepoint(mx, my),
            )

            if not madness_purchased:
                madness_label = "Безумство (1000 монет, заблоковано)"
            else:
                madness_label = (
                    "Безумство – активне"
                    if madness_active
                    else "Безумство (доступно назавжди)"
                )
            draw_button(
                screen,
                madness_r,
                madness_label,
                font_small,
                madness_r.collidepoint(mx, my),
            )

            preview_center = (sw // 2, sh // 2)
            pygame.draw.circle(
                screen,
                (30, 35, 50),
                preview_center,
                PLAYER_RADIUS + 40,
                0,
            )
            color = skin_color(selected_skin)
            angle = pygame.time.get_ticks() / 600.0
            draw_player_preview(screen, preview_center, color, angle)

            coins_text = f"Монети: {coins}"
            coins_img = font_small.render(coins_text, True, (240, 240, 180))
            screen.blit(coins_img, (sw - coins_img.get_width() - 20, sh - 60))

            if last_result == "no_coins":
                msg = "Недостатньо монет для Безумства"
                draw_text_center(
                    screen,
                    msg,
                    font_small,
                    (240, 120, 120),
                    (sw // 2, 40),
                )

            pygame.display.flip()
            continue

        if game_state == STATE_MODE_SELECT:
            screen.fill((10, 14, 22))
            draw_text_center(
                screen,
                "Вибір режиму",
                font_big,
                (240, 240, 240),
                (sw // 2, 70),
            )
            back_rect = pygame.Rect(0, 0, 200, 50)
            back_rect.bottomleft = (20, sh - 20)
            mx, my = pygame.mouse.get_pos()
            draw_button(
                screen,
                back_rect,
                "Назад",
                font_med,
                back_rect.collidepoint(mx, my),
            )

            mode1_rect = pygame.Rect(0, 0, 280, 160)
            mode2_rect = pygame.Rect(0, 0, 280, 160)
            mode3_rect = pygame.Rect(0, 0, 280, 100)
            mode1_rect.center = (sw // 2 - 170, sh // 2)
            mode2_rect.center = (sw // 2 + 170, sh // 2)
            mode3_rect.center = (sw // 2, sh // 2 + 200)

            for rect, label, desc1, desc2, icon_type in [
                (
                    mode1_rect,
                    "Шукач кристалів",
                    "Збери 10 кристалів",
                    "Боти теж полюють",
                    "crystal",
                ),
                (
                    mode2_rect,
                    "Останній в живих",
                    "10 ботів на арені",
                    "Без відродження",
                    "skull",
                ),
            ]:
                hovered = rect.collidepoint(mx, my)
                color = (30, 35, 50) if not hovered else (45, 55, 80)
                pygame.draw.rect(screen, color, rect, border_radius=16)
                pygame.draw.rect(
                    screen,
                    (230, 230, 230),
                    rect,
                    2,
                    border_radius=16,
                )
                icon_center = (rect.left + 50, rect.centery)
                if icon_type == "crystal":
                    points = [
                        (icon_center[0], icon_center[1] - 24),
                        (icon_center[0] + 18, icon_center[1]),
                        (icon_center[0], icon_center[1] + 24),
                        (icon_center[0] - 18, icon_center[1]),
                    ]
                    pygame.draw.polygon(screen, (120, 220, 255), points)
                else:
                    pygame.draw.circle(
                        screen, (230, 230, 230), icon_center, 18, 2
                    )
                    pygame.draw.circle(
                        screen, (230, 230, 230), (icon_center[0] - 6, icon_center[1] - 4), 3
                    )
                    pygame.draw.circle(
                        screen, (230, 230, 230), (icon_center[0] + 6, icon_center[1] - 4), 3
                    )
                    pygame.draw.rect(
                        screen,
                        (230, 230, 230),
                        (icon_center[0] - 10, icon_center[1] + 4, 20, 6),
                    )
                title_pos = (rect.left + 90, rect.top + 24)
                draw_text_center(
                    screen,
                    label,
                    font_med,
                    (240, 240, 240),
                    (title_pos[0] + 80, title_pos[1]),
                )
                d1 = font_small.render(desc1, True, (220, 220, 220))
                d2 = font_small.render(desc2, True, (200, 200, 200))
                screen.blit(d1, (rect.left + 90, rect.top + 56))
                screen.blit(d2, (rect.left + 90, rect.top + 82))

            if madness_active:
                pygame.draw.rect(screen, (25, 30, 45), mode3_rect, border_radius=14)
                pygame.draw.rect(
                    screen, (230, 180, 80), mode3_rect, 2, border_radius=14
                )
                line1 = "Безумство: 3 раунди"
                if madness_plan:
                    names = [
                        "Кристали" if m == MODE_CRYSTALS else "Останній"
                        for m in madness_plan
                    ]
                    line2 = "План: " + " → ".join(names)
                else:
                    line2 = "План генерується..."
                line3 = (
                    "Виграй 2 раунди, щоб отримати 600 монет."
                )
                draw_text_center(
                    screen,
                    line1,
                    font_med,
                    (240, 240, 200),
                    (mode3_rect.centerx, mode3_rect.top + 26),
                )
                t2 = font_small.render(line2, True, (230, 230, 230))
                t3 = font_small.render(line3, True, (220, 220, 220))
                screen.blit(
                    t2,
                    (mode3_rect.centerx - t2.get_width() // 2, mode3_rect.top + 48),
                )
                screen.blit(
                    t3,
                    (mode3_rect.centerx - t3.get_width() // 2, mode3_rect.top + 68),
                )

            pygame.display.flip()
            continue

        if game_state == STATE_SETTINGS:
            screen.fill((10, 16, 22))
            draw_text_center(
                screen,
                "Налаштування",
                font_big,
                (240, 240, 240),
                (sw // 2, 80),
            )

            auto_text = (
                "Авто-режим керування: УВІМК"
                if auto_control
                else "Авто-режим керування: ВИМК"
            )
            mode_text = (
                "Керування: Клавіатура + миша"
                if control_mode == CONTROL_KEYBOARD
                else "Керування: Тач/екран"
            )
            fs_text = (
                "Повний екран: УВІМК"
                if fullscreen
                else "Повний екран: ВИМК"
            )

            auto_rect = pygame.Rect(0, 0, 320, 55)
            auto_rect.center = (sw // 2, sh // 2 - 110)
            control_rect = pygame.Rect(0, 0, 320, 55)
            control_rect.center = (sw // 2, sh // 2 - 20)
            fs_rect = pygame.Rect(0, 0, 320, 55)
            fs_rect.center = (sw // 2, sh // 2 + 70)
            back_rect = pygame.Rect(0, 0, 220, 50)
            back_rect.center = (sw // 2, sh // 2 + 160)

            mx, my = pygame.mouse.get_pos()

            draw_button(
                screen,
                auto_rect,
                auto_text,
                font_med,
                auto_rect.collidepoint(mx, my),
            )
            draw_button(
                screen,
                control_rect,
                mode_text + (" (авто)" if auto_control else ""),
                font_med,
                control_rect.collidepoint(mx, my),
            )
            draw_button(
                screen,
                fs_rect,
                fs_text,
                font_med,
                fs_rect.collidepoint(mx, my),
            )
            draw_button(
                screen,
                back_rect,
                "Назад",
                font_med,
                back_rect.collidepoint(mx, my),
            )

            info = "F11 також перемикає повний екран"
            draw_text_center(
                screen,
                info,
                font_small,
                (200, 200, 200),
                (sw // 2, sh - 40),
            )
            pygame.display.flip()
            continue

        if game_state == STATE_SKINS:
            screen.fill((15, 18, 26))
            draw_text_center(
                screen,
                "Скіни",
                font_big,
                (240, 240, 240),
                (sw // 2, 60),
            )

            coins_text = f"Монети: {coins}"
            coins_img = font_small.render(coins_text, True, (240, 240, 180))
            screen.blit(coins_img, (20, 20))

            cols = 3
            cell_w = 200
            cell_h = 70
            start_x = sw // 2 - (cols * cell_w + (cols - 1) * 20) // 2
            start_y = 140
            mx, my = pygame.mouse.get_pos()
            for idx, name in enumerate(SKINS.keys()):
                row = idx // cols
                col = idx % cols
                rect = pygame.Rect(
                    start_x + col * (cell_w + 20),
                    start_y + row * (cell_h + 16),
                    cell_w,
                    cell_h,
                )
                hovered = rect.collidepoint(mx, my)
                owned = name in unlocked_skins
                color_rect = (35, 40, 60) if not hovered else (60, 70, 100)
                pygame.draw.rect(screen, color_rect, rect, border_radius=10)
                pygame.draw.rect(
                    screen,
                    (230, 230, 230),
                    rect,
                    2,
                    border_radius=10,
                )
                col_color = SKINS[name]["color"]
                circle_center = (rect.left + 30, rect.centery)
                pygame.draw.circle(screen, col_color, circle_center, 14)

                label = name
                label_img = font_small.render(label, True, (240, 240, 240))
                screen.blit(label_img, (rect.left + 60, rect.top + 8))
                if owned:
                    extra = "Вибрати" if name != selected_skin else "Вибрано"
                else:
                    extra = f"{SKINS[name]['price']} монет"
                extra_img = font_small.render(extra, True, (230, 230, 200))
                screen.blit(extra_img, (rect.left + 60, rect.top + 32))

            back_rect = pygame.Rect(0, 0, 220, 50)
            back_rect.center = (sw // 2, sh - 60)
            mx, my = pygame.mouse.get_pos()
            draw_button(
                screen,
                back_rect,
                "Назад",
                font_med,
                back_rect.collidepoint(mx, my),
            )

            pygame.display.flip()
            continue

        if game_state == STATE_PAUSE:
            cam_x = player["x"] - sw / 2
            cam_y = player["y"] - sh / 2
            cam_x = max(0, min(WORLD_WIDTH - sw, cam_x))
            cam_y = max(0, min(WORLD_HEIGHT - sh, cam_y))
            draw_game_frame(
                screen,
                current_world,
                player,
                bots,
                boxes,
                deposits,
                bullets,
                crystals_items,
                particles,
                cam_x,
                cam_y,
                font_small,
                selected_skin,
                skin_color,
                coins,
                current_mode,
                damage_flash_timer,
            )
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            draw_text_center(
                screen,
                "Пауза",
                font_big,
                (255, 255, 255),
                (sw // 2, sh // 2 - 30),
            )
            draw_text_center(
                screen,
                "ESC - продовжити",
                font_small,
                (240, 240, 240),
                (sw // 2, sh // 2 + 20),
            )
            pygame.display.flip()
            continue

        if game_state == STATE_RESULT:
            screen.fill((10, 14, 22))
            if result_stats:
                title = (
                    "Перемога!"
                    if result_stats["outcome"] == "win"
                    else "Поразка"
                )
                draw_text_center(
                    screen,
                    title,
                    font_big,
                    (240, 240, 240),
                    (sw // 2, 80),
                )
                mode_name = {
                    MODE_CRYSTALS: "Шукач кристалів",
                    MODE_LAST_MAN: "Останній в живих",
                    MODE_MADNESS: "Безумство",
                }.get(result_stats["mode"], "Режим")
                draw_text_center(
                    screen,
                    f"Режим: {mode_name}",
                    font_med,
                    (220, 220, 220),
                    (sw // 2, 130),
                )
                y = 180
                stats_lines = [
                    f"Вбив: {result_stats['kills']}",
                    f"Смертей: {result_stats['deaths']}",
                    f"Монет за раунд: {result_stats['coins_delta']:+d}",
                ]
                if madness_active:
                    stats_lines.append(
                        f"Серія Безумства: {madness_player_wins} перемог, {madness_bot_wins} поразок"
                    )
                for line in stats_lines:
                    img = font_small.render(line, True, (230, 230, 230))
                    rect = img.get_rect(center=(sw // 2, y))
                    screen.blit(img, rect)
                    y += 26

            back_rect = pygame.Rect(0, 0, 220, 50)
            back_rect.center = (sw // 2, sh - 80)
            mx, my = pygame.mouse.get_pos()
            draw_button(
                screen,
                back_rect,
                "До меню",
                font_med,
                back_rect.collidepoint(mx, my),
            )
            pygame.display.flip()
            continue

        # --- GAME STATE ---

        obstacles = [b["rect"] for b in boxes] + [d["rect"] for d in deposits]

        damage_flash_timer = max(0, damage_flash_timer - dt_ms)

        # pre-round countdown
        cam_x = player["x"] - sw / 2
        cam_y = player["y"] - sh / 2
        cam_x = max(0, min(WORLD_WIDTH - sw, cam_x))
        cam_y = max(0, min(WORLD_HEIGHT - sh, cam_y))

        if pre_round_timer > 0:
            pre_round_timer -= dt_ms
            draw_game_frame(
                screen,
                current_world,
                player,
                bots,
                boxes,
                deposits,
                bullets,
                crystals_items,
                particles,
                cam_x,
                cam_y,
                font_small,
                selected_skin,
                skin_color,
                coins,
                current_mode,
                0,
            )
            secs = max(1, int(pre_round_timer / 1000) + 1)
            txt = str(secs)
            img = font_big.render(txt, True, (255, 255, 255))
            rect = img.get_rect(center=(sw // 2, sh // 2))
            screen.blit(img, rect)
            pygame.display.flip()
            continue

        # PLAYER
        if player["alive"]:
            if control_mode == CONTROL_KEYBOARD:
                keys = pygame.key.get_pressed()
                vx = keys[pygame.K_d] - keys[pygame.K_a]
                vy = keys[pygame.K_s] - keys[pygame.K_w]
            else:
                mx, my = pygame.mouse.get_pos()
                vx = mx - sw // 2
                vy = my - sh // 2
            player["x"], player["y"] = move_circle(
                (player["x"], player["y"]),
                (vx, vy),
                obstacles,
                PLAYER_RADIUS,
                PLAYER_SPEED,
            )

            cam_x = player["x"] - sw / 2
            cam_y = player["y"] - sh / 2
            cam_x = max(0, min(WORLD_WIDTH - sw, cam_x))
            cam_y = max(0, min(WORLD_HEIGHT - sh, cam_y))

            mx, my = pygame.mouse.get_pos()
            sx = player["x"] - cam_x
            sy = player["y"] - cam_y
            cmx, cmy = clamp_mouse((sx, sy), (mx, my), MOUSE_AIM_RADIUS)
            dx = cmx - sx
            dy = cmy - sy
            if dx != 0 or dy != 0:
                player["aim_dx"], player["aim_dy"] = dx, dy

            mouse_buttons = pygame.mouse.get_pressed(num_buttons=3)
            if mouse_buttons[0] and (dx != 0 or dy != 0):
                if now_ticks - player["last_shot"] >= BULLET_COOLDOWN:
                    b = spawn_bullet(
                        (player["x"], player["y"]),
                        (player["aim_dx"], player["aim_dy"]),
                        player["id"],
                    )
                    if b:
                        bullets.append(b)
                        player["last_shot"] = now_ticks
        else:
            player["respawn_timer"] -= dt_ms
            if current_mode == MODE_CRYSTALS and player["respawn_timer"] <= 0:
                px, py = random_edge_pos()
                player["x"], player["y"] = px, py
                player["hp"] = PLAYER_MAX_HP
                player["alive"] = True
                player["crystals"] = 0
                player["last_damage"] = now_ticks

        # BOTS AI
        for bot in bots:
            if not bot["alive"]:
                if current_mode == MODE_CRYSTALS:
                    bot["respawn_timer"] -= dt_ms
                    if bot["respawn_timer"] <= 0:
                        bx, by = random_edge_pos()
                        bot["x"], bot["y"] = bx, by
                        bot["hp"] = PLAYER_MAX_HP
                        bot["alive"] = True
                        bot["crystals"] = 0
                        bot["last_damage"] = now_ticks
                continue

            bot["dodge_timer"] -= dt_ms

            # dodge bullets
            for b in bullets:
                if b["owner"] == bot["id"]:
                    continue
                vx = bot["x"] - b["x"]
                vy = bot["y"] - b["y"]
                dist = math.hypot(vx, vy)
                if dist < 140:
                    dot = vx * b["dx"] + vy * b["dy"]
                    if dot < 0:
                        perp_x = -b["dy"]
                        perp_y = b["dx"]
                        length = math.hypot(perp_x, perp_y)
                        if length > 0:
                            perp_x /= length
                            perp_y /= length
                        if random.random() < 0.5:
                            perp_x, perp_y = -perp_x, -perp_y
                        bot["dodge_dx"] = perp_x
                        bot["dodge_dy"] = perp_y
                        bot["dodge_timer"] = 250
                        break

            enemies_list = [player] + [b for b in bots if b["id"] != bot["id"]]

            move_dir = (0.0, 0.0)
            shoot_target = None

            if bot["dodge_timer"] > 0:
                move_dir = (bot["dodge_dx"], bot["dodge_dy"])
            else:
                if current_mode == MODE_CRYSTALS:
                    # головна задача – залежі
                    if deposits:
                        nearest_dep = min(
                            deposits,
                            key=lambda d: math.hypot(
                                d["rect"].centerx - bot["x"],
                                d["rect"].centery - bot["y"],
                            ),
                        )
                        dx = nearest_dep["rect"].centerx - bot["x"]
                        dy = nearest_dep["rect"].centery - bot["y"]
                        move_dir = (dx, dy)

                    # стріляємо тільки по тим, у кого багато кристалів або дуже близько
                    best_target = None
                    best_dist = 999999
                    for e in enemies_list:
                        if not e["alive"]:
                            continue
                        dx = e["x"] - bot["x"]
                        dy = e["y"] - bot["y"]
                        dist = math.hypot(dx, dy)
                        if dist < best_dist:
                            best_dist = dist
                            best_target = e
                    if best_target:
                        e_crystals = best_target.get("crystals", 0)
                        very_close = best_dist < 140
                        if (e_crystals >= 5 or very_close) and best_dist <= BOT_SHOOT_RANGE:
                            shoot_target = best_target
                else:
                    # останній в живих – агресія/відхід
                    enemies = [
                        e
                        for e in enemies_list
                        if e["alive"]
                    ]
                    if enemies:
                        nearest = min(
                            enemies,
                            key=lambda e: math.hypot(
                                e["x"] - bot["x"], e["y"] - bot["y"]
                            ),
                        )
                        dx = nearest["x"] - bot["x"]
                        dy = nearest["y"] - bot["y"]
                        dist = math.hypot(dx, dy)
                        if bot["hp"] < 30 and dist < 260:
                            move_dir = (-dx, -dy)
                        else:
                            move_dir = (dx, dy)

                        low_hp_target = min(
                            [
                                e
                                for e in enemies
                                if math.hypot(
                                    e["x"] - bot["x"], e["y"] - bot["y"]
                                )
                                <= BOT_SHOOT_RANGE
                            ],
                            key=lambda e: e["hp"],
                            default=None,
                        )
                        shoot_target = low_hp_target

            bot["x"], bot["y"] = move_circle(
                (bot["x"], bot["y"]),
                move_dir,
                obstacles,
                BOT_RADIUS,
                BOT_SPEED,
            )

            if shoot_target:
                dx = shoot_target["x"] - bot["x"]
                dy = shoot_target["y"] - bot["y"]
                if dx != 0 or dy != 0:
                    bot["aim_dx"], bot["aim_dy"] = dx, dy
                if now_ticks - bot["last_shot"] >= BULLET_COOLDOWN + random.randint(
                    -20, 80
                ):
                    bullet = spawn_bullet(
                        (bot["x"], bot["y"]),
                        (bot["aim_dx"], bot["aim_dy"]),
                        bot["id"],
                    )
                    if bullet:
                        bullets.append(bullet)
                        bot["last_shot"] = now_ticks

        # BULLETS
        for b in bullets:
            b["x"] += b["dx"]
            b["y"] += b["dy"]
            b["life"] -= dt_ms
        bullets = [
            b
            for b in bullets
            if 0 <= b["x"] <= WORLD_WIDTH
            and 0 <= b["y"] <= WORLD_HEIGHT
            and b["life"] > 0
        ]

        # PARTICLES
        for p in particles:
            p["x"] += p["dx"] * dt
            p["y"] += p["dy"] * dt
            p["life"] -= dt_ms
        particles = [p for p in particles if p["life"] > 0]

        # COLLISIONS
        for b in bullets[:]:
            rect = pygame.Rect(
                b["x"] - BULLET_RADIUS,
                b["y"] - BULLET_RADIUS,
                BULLET_RADIUS * 2,
                BULLET_RADIUS * 2,
            )

            if current_mode == MODE_CRYSTALS:
                hit_dep = None
                for d in deposits:
                    if d["rect"].colliderect(rect):
                        hit_dep = d
                        break
                if hit_dep:
                    bullets.remove(b)
                    hit_dep["hp"] -= 1
                    for _ in range(4):
                        angle = random.random() * 2 * math.pi
                        speed = random.uniform(60, 120)
                        particles.append(
                            {
                                "x": hit_dep["rect"].centerx,
                                "y": hit_dep["rect"].centery,
                                "dx": math.cos(angle) * speed,
                                "dy": math.sin(angle) * speed,
                                "life": 250,
                                "color": (120, 220, 255),
                            }
                        )
                    if hit_dep["hp"] <= 0:
                        if hit_dep["has_crystal"]:
                            crystals_items.append(
                                {
                                    "x": hit_dep["rect"].centerx,
                                    "y": hit_dep["rect"].centery,
                                }
                            )
                        deposits.remove(hit_dep)
                    continue
            else:
                hit_box = None
                for bx in boxes:
                    if bx["rect"].colliderect(rect):
                        hit_box = bx
                        break
                if hit_box:
                    bullets.remove(b)
                    hit_box["hp"] -= 1
                    for _ in range(4):
                        angle = random.random() * 2 * math.pi
                        speed = random.uniform(60, 120)
                        particles.append(
                            {
                                "x": hit_box["rect"].centerx,
                                "y": hit_box["rect"].centery,
                                "dx": math.cos(angle) * speed,
                                "dy": math.sin(angle) * speed,
                                "life": 250,
                                "color": (255, 230, 120),
                            }
                        )
                    if hit_box["hp"] <= 0:
                        boxes.remove(hit_box)
                    continue

            # hit player
            if player["alive"] and b["owner"] != player["id"]:
                if math.hypot(player["x"] - b["x"], player["y"] - b["y"]) <= (
                    PLAYER_RADIUS + BULLET_RADIUS
                ):
                    bullets.remove(b)
                    player["hp"] -= BULLET_DAMAGE
                    player["last_damage"] = now_ticks
                    damage_flash_timer = 160
                    for _ in range(6):
                        angle = random.random() * 2 * math.pi
                        speed = random.uniform(80, 160)
                        particles.append(
                            {
                                "x": player["x"],
                                "y": player["y"],
                                "dx": math.cos(angle) * speed,
                                "dy": math.sin(angle) * speed,
                                "life": 220,
                                "color": (255, 80, 80),
                            }
                        )
                    if player["hp"] <= 0 and player["alive"]:
                        player["alive"] = False
                        player["deaths"] += 1
                        for bot in bots:
                            if bot["id"] == b["owner"]:
                                bot["kills"] += 1
                                break
                        for _ in range(player["crystals"]):
                            crystals_items.append({"x": player["x"], "y": player["y"]})
                        player["crystals"] = 0
                        if current_mode == MODE_CRYSTALS:
                            player["respawn_timer"] = 3000
                        else:
                            pass
                    continue

            # hit bots
            for bot in bots:
                if not bot["alive"] or b["owner"] == bot["id"]:
                    continue
                if math.hypot(bot["x"] - b["x"], bot["y"] - b["y"]) <= (
                    BOT_RADIUS + BULLET_RADIUS
                ):
                    bullets.remove(b)
                    bot["hp"] -= BULLET_DAMAGE
                    bot["last_damage"] = now_ticks
                    for _ in range(5):
                        angle = random.random() * 2 * math.pi
                        speed = random.uniform(80, 150)
                        particles.append(
                            {
                                "x": bot["x"],
                                "y": bot["y"],
                                "dx": math.cos(angle) * speed,
                                "dy": math.sin(angle) * speed,
                                "life": 220,
                                "color": (255, 120, 80),
                            }
                        )
                    if bot["hp"] <= 0 and bot["alive"]:
                        bot["alive"] = False
                        bot["deaths"] += 1
                        owner = None
                        if b["owner"] == player["id"]:
                            player["kills"] += 1
                        else:
                            for bb in bots:
                                if bb["id"] == b["owner"]:
                                    bb["kills"] += 1
                                    break
                        for _ in range(bot["crystals"]):
                            crystals_items.append({"x": bot["x"], "y": bot["y"]})
                        bot["crystals"] = 0
                        if current_mode == MODE_CRYSTALS:
                            bot["respawn_timer"] = 2500
                    break

        # remove bullets of dead owners
        alive_ids = set()
        if player["alive"]:
            alive_ids.add(player["id"])
        for bot in bots:
            if bot["alive"]:
                alive_ids.add(bot["id"])
        bullets = [b for b in bullets if b["owner"] in alive_ids]

        # crystals pickup + win logic
        round_finished = False
        round_outcome = None
        coins_delta = 0

        if current_mode == MODE_CRYSTALS:
            if player["alive"]:
                for item in crystals_items[:]:
                    if math.hypot(
                        item["x"] - player["x"], item["y"] - player["y"]
                    ) <= PLAYER_RADIUS + 10:
                        player["crystals"] += 1
                        crystals_items.remove(item)
            for bot in bots:
                if not bot["alive"]:
                    continue
                for item in crystals_items[:]:
                    if math.hypot(
                        item["x"] - bot["x"], item["y"] - bot["y"]
                    ) <= BOT_RADIUS + 10:
                        bot["crystals"] += 1
                        crystals_items.remove(item)

            if player["alive"] and player["crystals"] >= 10:
                round_finished = True
                round_outcome = "win"
                coins_delta = 200
                coins += coins_delta

            for bot in bots:
                if bot["alive"] and bot["crystals"] >= 10:
                    round_finished = True
                    round_outcome = "lose"
                    break

            deposit_spawn_timer -= dt_ms
            if deposit_spawn_timer <= 0:
                deposit_spawn_timer = DEPOSIT_RESPAWN_INTERVAL
                if len(deposits) < DEPOSIT_TARGET_COUNT:
                    rect = random_deposit_rect()
                    deposits.append(
                        {
                            "rect": rect,
                            "hp": DEPOSIT_HP,
                            "has_crystal": True,
                            "emerge": 0.0,
                        }
                    )
        else:
            alive_bots = [b for b in bots if b["alive"]]
            total_alive = (1 if player["alive"] else 0) + len(alive_bots)
            if total_alive <= 1:
                round_finished = True
                if player["alive"]:
                    round_outcome = "win"
                    coins_delta = 100
                    coins += coins_delta
                else:
                    round_outcome = "lose"

        # regen (повільніший)
        def regen_char(ch):
            if not ch["alive"]:
                return
            if now_ticks - ch["last_damage"] > 4000:
                ch["hp"] += 6 * dt
                if ch["hp"] > PLAYER_MAX_HP:
                    ch["hp"] = PLAYER_MAX_HP

        regen_char(player)
        for bot in bots:
            regen_char(bot)

        # MADNESS progression
        if round_finished:
            mode_for_result = (
                MODE_MADNESS if madness_active else current_mode
            )
            if madness_active:
                if round_outcome == "win":
                    madness_player_wins += 1
                elif round_outcome == "lose":
                    madness_bot_wins += 1

                if madness_player_wins >= 2:
                    coins += 600
                    coins_delta = 600
                    madness_active = False
                    round_outcome = "win"
                elif madness_bot_wins >= 2:
                    if coins >= 100:
                        coins -= 100
                        coins_delta = -100
                    madness_active = False
                    round_outcome = "lose"
                elif madness_index < 2:
                    # продовжуємо до наступного раунду
                    madness_index += 1
                    current_mode = madness_plan[madness_index]
                    (
                        player,
                        bots,
                        boxes,
                        deposits,
                        bullets,
                        crystals_items,
                        particles,
                        current_world,
                        deposit_spawn_timer,
                    ) = reset_match(current_mode)
                    pre_round_timer = 3000
                    continue

            result_stats = {
                "outcome": round_outcome,
                "mode": mode_for_result,
                "kills": player["kills"],
                "deaths": player["deaths"],
                "coins_delta": coins_delta,
            }
            game_state = STATE_RESULT
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)

        # camera & draw
        cam_x = player["x"] - sw / 2
        cam_y = player["y"] - sh / 2
        cam_x = max(0, min(WORLD_WIDTH - sw, cam_x))
        cam_y = max(0, min(WORLD_HEIGHT - sh, cam_y))

        draw_game_frame(
            screen,
            current_world,
            player,
            bots,
            boxes,
            deposits,
            bullets,
            crystals_items,
            particles,
            cam_x,
            cam_y,
            font_small,
            selected_skin,
            skin_color,
            coins,
            current_mode,
            damage_flash_timer,
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def draw_game_frame(
    screen,
    world_surface,
    player,
    bots,
    boxes,
    deposits,
    bullets,
    crystals_items,
    particles,
    cam_x,
    cam_y,
    font_small,
    selected_skin,
    skin_color_fn,
    coins,
    mode,
    damage_flash_timer,
):
    sw, sh = screen.get_size()
    screen.blit(world_surface, (-cam_x, -cam_y))

    # boxes
    for b in boxes:
        hp_ratio = b["hp"] / BOX_HP
        color = (
            int(140 + (200 - 140) * (1 - hp_ratio)),
            int(110 + (170 - 110) * (1 - hp_ratio)),
            int(80 + (150 - 80) * (1 - hp_ratio)),
        )
        r = b["rect"].copy()
        r.x -= cam_x
        r.y -= cam_y
        shadow = pygame.Rect(r.x + 3, r.y + 6, r.width, r.height)
        pygame.draw.rect(screen, (0, 0, 0, 60), shadow)
        pygame.draw.rect(screen, color, r)

    # deposits
    for d in deposits:
        if "emerge" in d:
            d["emerge"] = min(1.0, d.get("emerge", 0.0) + 0.02)
            scale = d["emerge"]
        else:
            scale = 1.0
        hp_ratio = d["hp"] / DEPOSIT_HP
        base = STONE_COLOR
        color = (
            int(base[0] + (DEPOSIT_COLOR[0] - base[0]) * (1 - hp_ratio)),
            int(base[1] + (DEPOSIT_COLOR[1] - base[1]) * (1 - hp_ratio)),
            int(base[2] + (DEPOSIT_COLOR[2] - base[2]) * (1 - hp_ratio)),
        )
        r = d["rect"].copy()
        r.x -= cam_x
        r.y -= cam_y
        r.inflate_ip(int(r.width * (scale - 1)), int(r.height * (scale - 1)))
        shadow = pygame.Rect(r.x + 4, r.y + 6, r.width, r.height)
        pygame.draw.rect(screen, (0, 0, 0, 80), shadow, border_radius=6)
        pygame.draw.rect(screen, color, r, border_radius=6)

    # crystals
    for item in crystals_items:
        x = item["x"] - cam_x
        y = item["y"] - cam_y
        pygame.draw.circle(screen, (80, 170, 255), (int(x), int(y)), 9)
        pygame.draw.circle(screen, (180, 240, 255), (int(x) - 3, int(y) - 3), 4)

    # particles
    for p in particles:
        x = p["x"] - cam_x
        y = p["y"] - cam_y
        col = p["color"]
        pygame.draw.circle(screen, col, (int(x), int(y)), 3)

    # bots
    alive_bots = 0
    for bot in bots:
        if not bot["alive"]:
            continue
        alive_bots += 1
        x = bot["x"] - cam_x
        y = bot["y"] - cam_y
        shadow_col = (0, 0, 0, 110)
        shadow = pygame.Surface((BOT_RADIUS * 4, BOT_RADIUS * 3), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow,
            shadow_col,
            (0, BOT_RADIUS, BOT_RADIUS * 4, BOT_RADIUS * 1.5),
        )
        screen.blit(shadow, (x - BOT_RADIUS * 2, y - BOT_RADIUS * 0.2))

        pygame.draw.circle(screen, (220, 140, 60), (int(x), int(y)), BOT_RADIUS)
        draw_gun_on_world(
            screen,
            bot["x"],
            bot["y"],
            bot["aim_dx"],
            bot["aim_dy"],
            cam_x,
            cam_y,
        )
        bar_w = 40
        bar_h = 6
        bx = x - bar_w / 2
        by = y - BOT_RADIUS - 14
        pygame.draw.rect(
            screen, (40, 40, 40), (bx - 1, by - 1, bar_w + 2, bar_h + 2), border_radius=3
        )
        ratio = max(0, min(1.0, bot["hp"] / PLAYER_MAX_HP))
        pygame.draw.rect(
            screen,
            (120, 30, 30),
            (bx, by, bar_w, bar_h),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            (40, 230, 80),
            (bx, by, bar_w * ratio, bar_h),
            border_radius=3,
        )
        if mode == MODE_CRYSTALS and bot["crystals"] > 0:
            txt = f"{bot['crystals']}/10"
            img = font_small.render(txt, True, (255, 255, 255))
            rect = img.get_rect(midbottom=(x, by - 2))
            screen.blit(img, rect)

    # player
    px = player["x"] - cam_x
    py = player["y"] - cam_y
    if player["alive"]:
        shadow_col = (0, 0, 0, 120)
        shadow = pygame.Surface((PLAYER_RADIUS * 4, PLAYER_RADIUS * 3), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow,
            shadow_col,
            (0, PLAYER_RADIUS, PLAYER_RADIUS * 4, PLAYER_RADIUS * 1.5),
        )
        screen.blit(shadow, (px - PLAYER_RADIUS * 2, py - PLAYER_RADIUS * 0.2))
        color = skin_color_fn(selected_skin)
        pygame.draw.circle(screen, color, (int(px), int(py)), PLAYER_RADIUS)
        draw_gun_on_world(
            screen,
            player["x"],
            player["y"],
            player["aim_dx"],
            player["aim_dy"],
            cam_x,
            cam_y,
        )
        if mode == MODE_CRYSTALS:
            txt = f"{player['crystals']}/10"
            img = font_small.render(txt, True, (255, 255, 255))
            rect = img.get_rect(midbottom=(px, py - PLAYER_RADIUS - 4))
            screen.blit(img, rect)
    else:
        pygame.draw.circle(
            screen,
            (80, 20, 20),
            (int(px), int(py)),
            PLAYER_RADIUS,
            2,
        )

    # bullets
    for b in bullets:
        x = b["x"] - cam_x
        y = b["y"] - cam_y
        pygame.draw.circle(screen, (255, 230, 100), (int(x), int(y)), BULLET_RADIUS)

    # HUD
    margin = 15
    bar_w = 220
    bar_h = 20
    x = margin
    y = margin
    pygame.draw.rect(
        screen,
        (40, 40, 40),
        (x - 2, y - 2, bar_w + 4, bar_h + 4),
        border_radius=6,
    )
    hp = max(0, min(PLAYER_MAX_HP, player["hp"]))
    ratio = hp / PLAYER_MAX_HP
    pygame.draw.rect(
        screen,
        (120, 30, 30),
        (x, y, bar_w, bar_h),
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        (40, 230, 80),
        (x, y, int(bar_w * ratio), bar_h),
        border_radius=4,
    )
    hp_text = f"HP: {int(hp)}/{PLAYER_MAX_HP}"
    hp_img = font_small.render(hp_text, True, (240, 240, 240))
    screen.blit(hp_img, (x, y + bar_h + 6))

    coins_text = f"{coins} монет"
    coins_img = font_small.render(coins_text, True, (240, 240, 180))
    screen.blit(coins_img, (sw - coins_img.get_width() - 16, 16))

    alive_players = 1 if player["alive"] else 0
    alive_total = alive_players + alive_bots
    alive_text = f"Живі: {alive_total}"
    alive_img = font_small.render(alive_text, True, (230, 230, 230))
    screen.blit(alive_img, (sw - alive_img.get_width() - 16, 40))

    if damage_flash_timer > 0:
        alpha = int(120 * (damage_flash_timer / 160.0))
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, alpha))
        screen.blit(overlay, (0, 0))


if __name__ == "__main__":
    main()

