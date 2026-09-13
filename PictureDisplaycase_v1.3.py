import sys
import math
import pygame
import csv
import os
import json
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.logger import DailyLogger

# -----------------------------
# ログ設定
# -----------------------------
logger = DailyLogger(base_dir="logs", prefix="dsc_")
logger.write("[INFO] Display Show Case Start!!")

base_path = Path(__file__).resolve().parent
img_path = os.path.join(base_path, "images")
csv_path = os.path.join(base_path, "images.csv")
config_path = os.path.join(base_path, "config.json")

# -----------------------------
# config.json 読み込み
# -----------------------------
with open(config_path, "r", encoding="utf-8") as cf:
    config = json.load(cf)

logo_cfg = config["logo"]
text_cfg = config["text"]
front_ratio = config["front_max_ratio"]
FRONT_LIFT = config["front_lift_ratio"]
SMALL_BASE = config["small_base_px"]
title_flow_cfg = config["title_flow"]   # ★追加：タイトル流し込み設定

pygame.init()

disp_cfg = config["display"]

monitor= disp_cfg["monitor"]
if monitor == 0:
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
else:
    x = disp_cfg["width"]
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},0"

logger.write(f"[INFO] Target Display : monitor={monitor}")

# 画面設定
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

logger.write(f"[INFO] Display Setting: width={WIDTH} / height={HEIGHT}")

# 背景
bg = pygame.image.load(os.path.join(base_path,"back.png")).convert()
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

# ロゴ
logo_path = os.path.join(base_path, logo_cfg["path"])
logo2 = pygame.image.load(logo_path).convert()
logo2 = pygame.transform.smoothscale(logo2, (logo_cfg["width"], logo_cfg["height"]))
logo2.set_alpha(logo_cfg.get("alpha", 255))

COLOR_MAP = {
    "1":  ((255, 180, 200), (255, 150, 170)),
    "2":  ((150, 200, 255), (120, 170, 230)),
    "3":  ((255, 200, 150), (230, 160, 100)),
    "4":  ((80, 80, 80), (255, 255, 255)),
}


# -----------------------------
# 画像読み込み（orig と small）
# -----------------------------
image_info = []

with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        filename = row["filename"]
        title = row["title"]
        color_key = row["color"]

        orig = pygame.image.load(os.path.join(img_path, filename)).convert_alpha()

        w, h = orig.get_size()
        base = SMALL_BASE / max(w, h)
        small = pygame.transform.smoothscale(orig, (int(w * base), int(h * base)))

        image_info.append({
            "orig": orig,
            "small": small,
            "title": title,
            "color": color_key,
            "state": "small",
            "scale": 1.0,
            "y_offset": 0.0
        })

logger.write(f"[INFO] Image files read complete!")

# 円のパラメータ
center = (WIDTH // 2, HEIGHT // 2)
radius = int(min(WIDTH, HEIGHT) * 0.75)
vertical_offset = int(HEIGHT * 0.20)

offset_angle = 0.0
rotation_cfg = config["rotation"]
rotate_speed = math.radians(rotation_cfg["speed_deg"])

font = pygame.font.Font(text_cfg["font"], text_cfg["size"])

last_input_time = pygame.time.get_ticks()
auto_rotate_delay = 5000

MAX_W = WIDTH * front_ratio["width"]
MAX_H = HEIGHT * front_ratio["height"]

# ★追加：タイトル流し込み用変数
title_x = WIDTH
title_state = "moving"
current_front_title = ""

logger.write(f"[INFO] display init complete! Start running")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        offset_angle -= rotate_speed
        last_input_time = pygame.time.get_ticks()
    if keys[pygame.K_RIGHT]:
        offset_angle += rotate_speed
        last_input_time = pygame.time.get_ticks()

    if pygame.time.get_ticks() - last_input_time > auto_rotate_delay:
        offset_angle += rotate_speed * 0.1

    screen.blit(bg, (0, 0))

    dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 180))
    screen.blit(dark_overlay, (0, 0))

    screen.blit(logo2, (logo_cfg["x"], logo_cfg["y"]))

    n = len(image_info)

    depths = []
    angles = []

    for i in range(n):
        base_angle = 2 * math.pi * i / n
        angle = base_angle + offset_angle
        angles.append(angle)
        depth = (math.cos(angle) + 1) / 2
        depths.append(depth)

    front_index = depths.index(max(depths))

    # ★追加：正面タイトル変更チェック
    new_front_title = image_info[front_index]["title"]
    if new_front_title != current_front_title:
        current_front_title = new_front_title
        title_state = "moving"
        title_x = WIDTH   # 右端から再スタート

    draw_list = []

    for i, info in enumerate(image_info):
        orig = info["orig"]
        small = info["small"]
        title = info["title"]
        color_key = info["color"]

        angle = angles[i]
        depth = depths[i]

        is_front = (i == front_index)

        if is_front:
            if info["state"] == "small":
                info["state"] = "expanding"
        else:
            if info["state"] == "front":
                info["state"] = "shrinking"
            elif info["state"] == "expanding":
                info["state"] = "shrinking"

        small_w, small_h = small.get_size()
        orig_w, orig_h = orig.get_size()

        scale_front_w = MAX_W / orig_w
        scale_front_h = MAX_H / orig_h
        front_scale_target = min(scale_front_w, scale_front_h)

        small_scale_target = small_w / orig_w

        if info["state"] == "expanding":
            info["scale"] += (front_scale_target - info["scale"]) * 0.1
            if abs(info["scale"] - front_scale_target) < 0.002:
                info["scale"] = front_scale_target
                info["state"] = "front"

        elif info["state"] == "shrinking":
            info["scale"] += (small_scale_target - info["scale"]) * 0.1
            if abs(info["scale"] - small_scale_target) < 0.002:
                info["scale"] = small_scale_target
                info["state"] = "small"

        elif info["state"] == "front":
            info["scale"] = front_scale_target

        elif info["state"] == "small":
            info["scale"] = small_scale_target

        target_offset = -HEIGHT * FRONT_LIFT

        if info["state"] == "expanding":
            info["y_offset"] += (target_offset - info["y_offset"]) * 0.1
        elif info["state"] == "front":
            info["y_offset"] = target_offset
        elif info["state"] == "shrinking":
            info["y_offset"] += (0 - info["y_offset"]) * 0.1
        else:
            info["y_offset"] = 0

        img = orig if info["state"] in ("expanding", "front", "shrinking") else small

        w, h = img.get_size()
        scaled_img = pygame.transform.smoothscale(img, (int(w * info["scale"]), int(h * info["scale"])))

        tilt = abs(math.sin(angle))
        tilt_factor = 1 - tilt * 0.4
        new_w = max(1, int(scaled_img.get_width() * tilt_factor))
        new_h = scaled_img.get_height()
        scaled_img = pygame.transform.smoothscale(scaled_img, (new_w, new_h))

        alpha = int(100 + depth * 155)
        scaled_img.set_alpha(alpha)

        x = center[0] + radius * math.sin(angle)
        y = center[1] + vertical_offset * math.cos(angle)

        rect = scaled_img.get_rect(center=(int(x), int(y + info["y_offset"])))

        draw_list.append((depth, scaled_img, rect, title, color_key))

    sorted_list = sorted(draw_list, key=lambda x: x[0])

    for idx, (depth, img, rect, title, color_key) in enumerate(sorted_list):
        screen.blit(img, rect)

        frame_color, title_color = COLOR_MAP.get(color_key, ((255,255,255),(255,255,255)))

        if idx == len(sorted_list) - 1:
            pygame.draw.rect(screen, frame_color, rect.inflate(10, 10), 3)

    # ★タイトル流し込み処理
    target_x = WIDTH // 2
    flow_speed = title_flow_cfg["speed"]

    if title_state == "moving":
        title_x += (target_x - title_x) * flow_speed
        if abs(title_x - target_x) < 2:
            title_x = target_x
            title_state = "stopped"

    # ★タイトル描画（位置は config.json の y）
    _, _, front_rect, front_title, front_color = sorted_list[-1]
    frame_color, title_color = COLOR_MAP.get(front_color, ((255,255,255),(255,255,255)))

    title_surface = font.render(current_front_title, True, title_color)
    title_rect = title_surface.get_rect(center=(title_x, title_flow_cfg["y"]))
    screen.blit(title_surface, title_rect)

    # 任意テキスト（固定）
    text_surface = font.render(text_cfg["content"], True, tuple(text_cfg["color"]))
    text_rect = text_surface.get_rect(topleft=(text_cfg["x"], text_cfg["y"]))
    screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

logger.write("[INFO] Display Show Case End!!")

sys.exit()
