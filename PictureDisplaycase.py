import sys
import math
import pygame
import csv
import os

pygame.init()

# 画面設定
fullscreen = True

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()  # 実際の画面サイズを取得

#WIDTH, HEIGHT = 1600, 950
#screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circle Image Viewer")

clock = pygame.time.Clock()

base_path = "D:\Programming\DisplayShowcase"
img_path = os.path.join(base_path, "images")
csv_path = os.path.join(base_path, "images.csv")


back_path = os.path.join(base_path,"back.png")
bg = pygame.image.load(back_path).convert()

logo_path = os.path.join(base_path,"kda-logo1.jpg")
logo = pygame.image.load(logo_path).convert()

logo2_path = os.path.join(base_path,"kda-logo2.jpg")
logo2 = pygame.image.load(logo2_path).convert()
logo2 = pygame.transform.smoothscale(logo2, (300, 100))

# サイズをウィンドウに合わせて調整（必要なら）
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

COLOR_MAP = {
    "1":  ((255, 180, 200), (255, 150, 170)),  # (枠色, タイトル色)
    "2":  ((150, 200, 255), (120, 170, 230)),
    "3":((255, 200, 150), (230, 160, 100)),
    "4": ((80, 80, 80), (255, 255, 255)),
}


# -----------------------------
# 画像読み込み（orig と small の両方を作る）
# -----------------------------
image_info = []  # (orig, small, title)

with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        filename = row["filename"]
        title = row["title"]
        color_key = row["color"]

        full_path = os.path.join(img_path, filename)

        orig = pygame.image.load(full_path).convert_alpha()

        # small（軽量版）を作る：最大200pxに収まるように縮小
        w, h = orig.get_size()
        base = 200 / max(w, h)
        small = pygame.transform.smoothscale(orig, (int(w * base), int(h * base)))

        # image_info.append((orig, small, title, color_key))

        image_info.append({
            "orig": orig,
            "small": small,
            "title": title,
            "color": color_key,
            "scale": 1.0,
            "front_scale": 1.0   # ← 正面用の滑らか拡大率
        })

# 円のパラメータ
center = (WIDTH // 2, HEIGHT // 2)
radius = int(min(WIDTH, HEIGHT) * 0.75)
vertical_offset = int(HEIGHT * 0.20)

offset_angle = 0.0
rotate_speed = math.radians(3)

# 日本語フォント
font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 36)

last_input_time = pygame.time.get_ticks()
auto_rotate_delay = 5000  # 5秒（ミリ秒）

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            running = False
            if fullscreen:
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
            #else:
                #screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            #fullscreen = not fullscreen

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        offset_angle -= rotate_speed
        last_input_time = pygame.time.get_ticks()

    if keys[pygame.K_RIGHT]:
        offset_angle += rotate_speed
        last_input_time = pygame.time.get_ticks()

    # --- 一定時間キー入力がない場合は自動回転 ---
    current_time = pygame.time.get_ticks()
    if current_time - last_input_time > auto_rotate_delay:
        offset_angle += rotate_speed * 0.1  # 自動回転はゆっくり

    # screen.fill((30, 30, 30))
    
    screen.blit(bg, (0, 0))
    
    # 黒い半透明レイヤーを重ねる
    dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 180))  # RGBA → 黒・透明度80
    screen.blit(dark_overlay, (0, 0))

    screen.blit(logo2, (20, 20))   # 左上に表示（余白20px）

    draw_list = []
    n = len(image_info)

    # for i, (orig, small, title, color_key) in enumerate(image_info):

    for i, info in enumerate(image_info):
        orig = info["orig"]
        small = info["small"]
        title = info["title"]
        color_key = info["color"]

        base_angle = 2 * math.pi * i / n
        angle = base_angle + offset_angle

        # 正面度（0?1）
        front_factor = max(0, math.cos(angle))

        # 正面に近いほど高解像度を使う
        img = orig if front_factor > 0.995 else small

        # 座標
        x = center[0] + radius * math.sin(angle)
        y = center[1] + vertical_offset * math.cos(angle)

        # 奥行き
        depth = (math.cos(angle) + 1) / 2

        # 拡大率
        # scale = 0.5 + depth * 0.5
        # scale += front_factor * 0.4  # 正面で +40%

        # ★ なめらか拡大ロジック ★
        # target_scale = 0.5 + depth * 0.5 + front_factor * 0.4
        # info["scale"] += (target_scale - info["scale"]) * 0.1
        # scale = info["scale"]

        # 通常の scale（small 用）
        base_scale = 0.5 + depth * 0.5

        # 正面用の目標拡大率（orig 用）
        front_target = base_scale + front_factor * 0.4

        # small のときは front_scale を base_scale に戻す（滑らかに）
        if img == small:
            info["front_scale"] += (base_scale - info["front_scale"]) * 0.2
        else:
            # orig のときは front_target に滑らかに近づける
            info["front_scale"] += (front_target - info["front_scale"]) * 0.1

        # 実際に使うスケール
        scale = info["front_scale"]


        # 浮き上がり
        float_amount = int(HEIGHT * 0.05)
        y -= front_factor * float_amount

        # 元サイズ
        w, h = img.get_size()

        # -----------------------------
        # ウィンドウからはみ出さない最大サイズ制御
        # -----------------------------
        max_w = WIDTH * 0.45
        max_h = HEIGHT * 0.60

        target_w = w * scale
        target_h = h * scale

        limit_scale = min(max_w / target_w, max_h / target_h, 1.0)
        scale *= limit_scale

        # 拡大（縦横比維持）
        scaled_img = pygame.transform.smoothscale(
            img, (int(w * scale), int(h * scale))
        )

        # ぼかし（奥ほど強く）
        blur_strength = int((1 - depth) * 3)
        if blur_strength > 0:
            small2 = pygame.transform.smoothscale(
                scaled_img,
                (
                    max(1, scaled_img.get_width() // (1 + blur_strength)),
                    max(1, scaled_img.get_height() // (1 + blur_strength)),
                ),
            )
            scaled_img = pygame.transform.smoothscale(small2, scaled_img.get_size())

        # 影
        shadow_scale = 0.3 + depth * 0.7
        shadow_width = int(120 * shadow_scale)
        shadow_height = int(40 * shadow_scale)

        shadow = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, int(80 * depth)), shadow.get_rect())
        shadow_rect = shadow.get_rect(center=(int(x), int(y + (h * scale) // 2)))

        draw_list.append((depth - 0.01, shadow, shadow_rect, "", ""))

        # 傾き（Y軸回転風）
        tilt = abs(math.sin(angle))
        tilt_factor = 1 - tilt * 0.4
        new_w = max(1, int(scaled_img.get_width() * tilt_factor))
        new_h = scaled_img.get_height()
        scaled_img = pygame.transform.smoothscale(scaled_img, (new_w, new_h))

        # 明るさ
        alpha = int(100 + depth * 155)
        scaled_img.set_alpha(alpha)

        rect = scaled_img.get_rect(center=(int(x), int(y)))
        draw_list.append((depth, scaled_img, rect, title, color_key))

    # 奥から手前へ描画
    sorted_list = sorted(draw_list, key=lambda x: x[0])

    for idx, (depth, img, rect, title, color_key) in enumerate(sorted_list):
        screen.blit(img, rect)

        # 色区分から色を取得（無ければ白）
        frame_color, title_color = COLOR_MAP.get(color_key, ((255,255,255),(255,255,255)))

        # 正面に枠
        if idx == len(sorted_list) - 1:
            pygame.draw.rect(
                screen,
                frame_color,
                rect.inflate(10, 10),
                3,
            )

    # 正面タイトル
    _, _, front_rect, front_title, front_color = sorted_list[-1]
    text = font.render(front_title, True, title_color)
    text_rect = text.get_rect(center=(WIDTH // 2, 150))
    screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
