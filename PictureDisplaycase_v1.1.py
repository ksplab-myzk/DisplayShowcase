import sys
import math
import pygame
import csv
import os
import json

pygame.init()

# 画面設定
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

base_path = "D:\\Programming\\DisplayShowcase"

# 設定ファイルの読み込み
config_path = os.path.join(base_path, "config.json")
with open(config_path, "r", encoding="utf-8") as cf:
    config = json.load(cf)


img_path = os.path.join(base_path, "images")
csv_path = os.path.join(base_path, "images.csv")

# 背景
bg = pygame.image.load(os.path.join(base_path,"back.png")).convert()
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

# ロゴ
logo_cfg = config["logo"]
logo_path = os.path.join(base_path, logo_cfg["path"])
logo2 = pygame.image.load(logo_path).convert()
logo2 = pygame.transform.smoothscale(logo2, (logo_cfg["width"], logo_cfg["height"]))

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
        base = 400 / max(w, h)
        small = pygame.transform.smoothscale(orig, (int(w * base), int(h * base)))

        image_info.append({
            "orig": orig,
            "small": small,
            "title": title,
            "color": color_key,
            "state": "small",       # ★ small / expanding / front / shrinking
            "scale": 1.0            # 現在のスケール
        })

# 円のパラメータ
center = (WIDTH // 2, HEIGHT // 2)
radius = int(min(WIDTH, HEIGHT) * 0.75)
vertical_offset = int(HEIGHT * 0.20)

offset_angle = 0.0
rotate_speed = math.radians(3)

font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 36)

last_input_time = pygame.time.get_ticks()
auto_rotate_delay = 5000

# 正面画像の最大サイズ
MAX_W = WIDTH * 0.5
MAX_H = HEIGHT * 0.5

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

    # 自動回転
    if pygame.time.get_ticks() - last_input_time > auto_rotate_delay:
        offset_angle += rotate_speed * 0.1

    # 背景
    screen.blit(bg, (0, 0))

    # 黒レイヤー
    dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 180))
    screen.blit(dark_overlay, (0, 0))

    screen.blit(logo2, (logo_cfg["x"], logo_cfg["y"]))

    # テキスト
    text_cfg = config["text"]

    text_font = pygame.font.Font(text_cfg["font"], text_cfg["size"])
    text_surface = text_font.render(text_cfg["content"], True, tuple(text_cfg["color"]))
    text_rect = text_surface.get_rect(topleft=(text_cfg["x"], text_cfg["y"]))

    screen.blit(text_surface, text_rect)

    n = len(image_info)

    # ----------------------------------------------------
    # ★ 正面画像を「depth 最大の 1 枚だけ」選ぶ
    # ----------------------------------------------------
    depths = []
    angles = []

    for i in range(n):
        base_angle = 2 * math.pi * i / n
        angle = base_angle + offset_angle
        angles.append(angle)
        depth = (math.cos(angle) + 1) / 2
        depths.append(depth)

    front_index = depths.index(max(depths))

    # 描画リスト
    draw_list = []

    for i, info in enumerate(image_info):
        orig = info["orig"]
        small = info["small"]
        title = info["title"]
        color_key = info["color"]

        angle = angles[i]
        depth = depths[i]

        is_front = (i == front_index)

        # -----------------------------
        # ★ 状態遷移
        # -----------------------------
        if is_front:
            if info["state"] == "small":
                info["state"] = "expanding"
            elif info["state"] == "expanding":
                pass
            elif info["state"] == "front":
                pass
        else:
            if info["state"] == "front":
                info["state"] = "shrinking"
            elif info["state"] == "shrinking":
                pass
            elif info["state"] == "expanding":
                # 正面に入る前に外れた場合
                info["state"] = "shrinking"

        # -----------------------------
        # ★ スケール制御（滑らか拡大・縮小）
        # -----------------------------
        small_w, small_h = small.get_size()
        orig_w, orig_h = orig.get_size()

        # 正面の最大サイズを計算
        scale_front_w = MAX_W / orig_w
        scale_front_h = MAX_H / orig_h
        front_scale_target = min(scale_front_w, scale_front_h)

        small_scale_target = small_w / orig_w  # small の縮小率

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

        # -----------------------------
        # ★ 画像選択（orig / small）
        # -----------------------------
        img = orig if info["state"] in ("expanding", "front", "shrinking") else small

        # 拡大
        w, h = img.get_size()
        scaled_img = pygame.transform.smoothscale(img, (int(w * info["scale"]), int(h * info["scale"])))

        # 傾き補正
        tilt = abs(math.sin(angle))
        tilt_factor = 1 - tilt * 0.4
        new_w = max(1, int(scaled_img.get_width() * tilt_factor))
        new_h = scaled_img.get_height()
        scaled_img = pygame.transform.smoothscale(scaled_img, (new_w, new_h))

        # 明るさ
        alpha = int(100 + depth * 155)
        scaled_img.set_alpha(alpha)

        # 座標
        x = center[0] + radius * math.sin(angle)
        y = center[1] + vertical_offset * math.cos(angle)

        rect = scaled_img.get_rect(center=(int(x), int(y)))

        draw_list.append((depth, scaled_img, rect, title, color_key))

    # 奥から手前へ描画
    sorted_list = sorted(draw_list, key=lambda x: x[0])

    for idx, (depth, img, rect, title, color_key) in enumerate(sorted_list):
        screen.blit(img, rect)

        frame_color, title_color = COLOR_MAP.get(color_key, ((255,255,255),(255,255,255)))

        if idx == len(sorted_list) - 1:
            pygame.draw.rect(screen, frame_color, rect.inflate(10, 10), 3)

    # 正面タイトル
    _, _, front_rect, front_title, front_color = sorted_list[-1]
    frame_color, title_color = COLOR_MAP.get(front_color, ((255,255,255),(255,255,255)))

    text = font.render(front_title, True, title_color)
    text_rect = text.get_rect(center=(WIDTH // 2, 150))
    screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
