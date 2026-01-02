import random
import time
import math
from typing import List, Tuple

import pygame
from PIL import Image

from config import MAP_WIDTH, MAP_HEIGHT, CELL_SIZE, GAME_DURATION, FPS, GIF_PATH, SNAKE_LENGTH


Vec2 = Tuple[int, int]


def spawn_fruit(snake: List[Vec2]) -> Vec2:
    free = [(x, y) for x in range(MAP_WIDTH) for y in range(MAP_HEIGHT) if (x, y) not in snake]
    return random.choice(free) if free else snake[0]


def draw_cell(surface: pygame.Surface, pos: Vec2, color: Tuple[int, int, int, int]):
    x, y = pos
    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, color, rect)


def surface_to_image(surface: pygame.Surface) -> Image.Image:
    data = pygame.image.tostring(surface, "RGBA")
    size = surface.get_size()
    return Image.frombytes("RGBA", size, data)


def save_gif(frames: List[Image.Image], path: str):
    if not frames:
        return
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        disposal=2,
        transparency=0,
    )


def main():
    pygame.init()
    size_px = (MAP_WIDTH * CELL_SIZE, MAP_HEIGHT * CELL_SIZE)
    screen = pygame.display.set_mode(size_px, pygame.SRCALPHA)
    pygame.display.set_caption("Snake (Transparent GIF)")
    clock = pygame.time.Clock()

    # 按固定长度初始化蛇，水平朝右
    cy = MAP_HEIGHT // 2
    start_x = max(0, min(MAP_WIDTH - SNAKE_LENGTH, MAP_WIDTH // 2 - SNAKE_LENGTH // 2))
    snake: List[Vec2] = [(start_x + i, cy) for i in range(SNAKE_LENGTH)]
    direction: Vec2 = (1, 0)
    fruit = spawn_fruit(snake)

    frames: List[Image.Image] = []
    start_time = time.monotonic()
    end_time = start_time + GAME_DURATION

    key_dir = {
        pygame.K_w: (0, -1),
        pygame.K_s: (0, 1),
        pygame.K_a: (-1, 0),
        pygame.K_d: (1, 0),
        pygame.K_UP: (0, -1),
        pygame.K_DOWN: (0, 1),
        pygame.K_LEFT: (-1, 0),
        pygame.K_RIGHT: (1, 0),
    }
    snake_color_tail = (70, 140, 240)
    snake_color_head = (10, 40, 140)
    fruit_base = (230, 60, 60)

    def can_turn(nd):
        return len(snake) < 2 or (nd[0] != -direction[0] or nd[1] != -direction[1])

    pending_dir = direction

    def lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def render(elapsed):
        screen.fill((0, 0, 0, 0))
        # 果子：圆角 + 闪烁
        flash = 0.5 + 0.5 * math.sin(elapsed * 4)
        fruit_color = tuple(min(255, int(c * (0.7 + 0.3 * flash))) for c in fruit_base)
        fx, fy = fruit
        frect = pygame.Rect(fx * CELL_SIZE, fy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, fruit_color, frect, border_radius=CELL_SIZE // 3)

        # 蛇：蓝色渐深，尾细头粗，左右摇摆（渲染偏移，不影响逻辑）
        if direction != (0, 0):
            nx, ny = -direction[1], direction[0]
        else:
            nx, ny = 0, 0
        amp = CELL_SIZE * 0.2
        phase_base = elapsed * 6
        total = len(snake) - 1 or 1
        for idx, seg in enumerate(snake):
            t = idx / total
            color = lerp(snake_color_tail, snake_color_head, t)
            size = CELL_SIZE * (0.35 + 0.65 * t)
            sway = amp * math.sin(phase_base + idx * 0.6)
            cx = seg[0] * CELL_SIZE + CELL_SIZE / 2 + nx * sway
            cy = seg[1] * CELL_SIZE + CELL_SIZE / 2 + ny * sway
            pygame.draw.circle(screen, color, (int(cx), int(cy)), int(size / 2))

        pygame.display.flip()
        frames.append(surface_to_image(screen))

    render(0.0)  # 记录首帧，计时从启动后开始

    running = True
    while running:
        if time.monotonic() >= end_time:
            break
        pygame.event.pump()
        elapsed = time.monotonic() - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in key_dir:
                nd = key_dir[event.key]
                if can_turn(nd):
                    pending_dir = nd

        pressed = pygame.key.get_pressed()
        for key, nd in key_dir.items():
            if pressed[key] and can_turn(nd):
                pending_dir = nd
                break

        direction = pending_dir
        head = snake[-1]
        new_head = (head[0] + direction[0], head[1] + direction[1])

        # 碰撞检测：撞墙或咬到自己则结束
        if (
            not (0 <= new_head[0] < MAP_WIDTH and 0 <= new_head[1] < MAP_HEIGHT)
            or new_head in snake
        ):
            break

        snake.append(new_head)
        if new_head == fruit:
            fruit = spawn_fruit(snake)
        if len(snake) > SNAKE_LENGTH:
            snake.pop(0)

        render(elapsed)
        clock.tick(FPS)
    save_gif(frames, GIF_PATH)
    pygame.quit()


if __name__ == "__main__":
    main()
