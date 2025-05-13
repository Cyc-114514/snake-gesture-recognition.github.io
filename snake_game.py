
import pygame
import random
import time
import cv2
import mediapipe as mp

# 初始化pygame
pygame.init()

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
GAME_WIDTH = 800
GAME_HEIGHT = 600

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# 创建屏幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("贪吃蛇游戏")

# 游戏区域
game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
assist_surface = pygame.Surface((SCREEN_WIDTH - GAME_WIDTH, SCREEN_HEIGHT))

# 手势识别设置
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# 尝试初始化手势识别，如果失败则提示
try:
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)
    gesture_enabled = True
except Exception as e:
    print(f"手势识别初始化失败: {e}")
    print("将使用键盘控制替代")
    gesture_enabled = False

# 打开摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH - GAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT - 100)

# 方向文本字体
font = pygame.font.SysFont('Arial', 30)

# 蛇的初始设置
snake_pos = [[100, 50], [90, 50], [80, 50]]
snake_speed = 10  # 每秒移动的格子数
direction = 'RIGHT'
change_to = direction

# 果实设置
fruits = []
last_fruit_time = 0
fruit_spawn_time = 20  # 20秒刷新一次

# 游戏状态
game_over = False
clock = pygame.time.Clock()
last_move_time = 0  # 记录上次移动时间

def spawn_fruits():
    """生成4个新果实"""
    global fruits
    fruits = []
    for _ in range(8):
            while True:
                # 确保坐标是10的倍数，与蛇移动步长一致
                x = random.randrange(20, GAME_WIDTH - 40, 10)
                y = random.randrange(20, GAME_HEIGHT - 40, 10)
                # 确保果实不靠近边缘
                if (20 < x < GAME_WIDTH - 40) and (20 < y < GAME_HEIGHT - 40):
                    fruits.append([x, y])
                    break

def get_direction_from_hand(hand_landmarks):
    """根据手势识别方向"""
    # 获取食指和手腕的坐标
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    index_finger = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    
    # 计算方向向量
    dx = index_finger.x - wrist.x
    dy = index_finger.y - wrist.y
    
    # 确定主要方向
    if abs(dx) > abs(dy):
        return 'RIGHT' if dx > 0 else 'LEFT'
    else:
        return 'DOWN' if dy > 0 else 'UP'

def draw_game():
    """绘制游戏界面"""
    game_surface.fill(BLACK)
    assist_surface.fill(WHITE)
    
    # 读取摄像头画面
    ret, frame = cap.read()
    if ret:
        # 水平翻转摄像头画面
        frame = cv2.flip(frame, 1)  # 1表示水平翻转
        
        if gesture_enabled:
            try:
                # 转换为RGB格式
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 手势识别
                results = hands.process(frame_rgb)
                
                # 绘制手势骨架
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                        # 获取方向
                        direction_text = get_direction_from_hand(hand_landmarks)
                        cv2.putText(frame, direction_text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # 更新蛇的方向
                        global change_to
                        change_to = direction_text
                
                # 显示方向文本
                if results.multi_hand_landmarks:
                    text = font.render(f"Direction: {direction_text}", True, BLACK)
                    assist_surface.blit(text, (10, SCREEN_HEIGHT - 100))
            except Exception as e:
                print(f"手势识别出错: {e}")
                text = font.render("手势识别不可用", True, BLACK)
                assist_surface.blit(text, (10, SCREEN_HEIGHT - 100))
        else:
            text = font.render("使用键盘控制", True, BLACK)
            assist_surface.blit(text, (10, SCREEN_HEIGHT - 100))
        
        # 将OpenCV图像转换为Pygame Surface
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (SCREEN_WIDTH - GAME_WIDTH, SCREEN_HEIGHT - 100))
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        assist_surface.blit(frame, (0, 0))
    
    # 绘制蛇
    for pos in snake_pos:
        pygame.draw.rect(game_surface, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))
    
    # 绘制果实
    for fruit in fruits:
        pygame.draw.rect(game_surface, RED, pygame.Rect(fruit[0], fruit[1], 10, 10))
    
    # 绘制到屏幕
    screen.blit(game_surface, (0, 0))
    screen.blit(assist_surface, (GAME_WIDTH, 0))
    pygame.display.flip()

def check_collision():
    """检查碰撞"""
    # 检查墙壁碰撞
    if (snake_pos[0][0] >= GAME_WIDTH or snake_pos[0][0] < 0 or
        snake_pos[0][1] >= GAME_HEIGHT or snake_pos[0][1] < 0):
        return True
    
    # 检查自身碰撞
    for block in snake_pos[1:]:
        if snake_pos[0][0] == block[0] and snake_pos[0][1] == block[1]:
            return True
    
    return False

def show_game_over():
    """显示游戏结束界面"""
    font = pygame.font.SysFont('Arial', 50)
    text = font.render('Game Over', True, RED)
    text_rect = text.get_rect(center=(GAME_WIDTH/2, GAME_HEIGHT/2 - 50))
    
    button = pygame.Rect(GAME_WIDTH/2 - 100, GAME_HEIGHT/2 + 50, 200, 50)
    pygame.draw.rect(game_surface, WHITE, button)
    button_text = font.render('Restart', True, BLACK)
    button_text_rect = button_text.get_rect(center=button.center)
    
    game_surface.blit(text, text_rect)
    game_surface.blit(button_text, button_text_rect)
    screen.blit(game_surface, (0, 0))
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 释放摄像头资源
                cap.release()
                pygame.quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button.collidepoint(event.pos):
                    return True
        clock.tick(10)
    return True

# 初始生成果实
spawn_fruits()
last_fruit_time = time.time()

# 游戏主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 如果手势识别不可用，则使用键盘控制
    if not gesture_enabled and event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP and direction != 'DOWN':
            change_to = 'UP'
        if event.key == pygame.K_DOWN and direction != 'UP':
            change_to = 'DOWN'
        if event.key == pygame.K_LEFT and direction != 'RIGHT':
            change_to = 'LEFT'
        if event.key == pygame.K_RIGHT and direction != 'LEFT':
            change_to = 'RIGHT'
    
    if not game_over:
        # 更新方向
        direction = change_to
        
        # 移动蛇
        if time.time() - last_fruit_time > fruit_spawn_time:
            spawn_fruits()
            last_fruit_time = time.time()
        
        # 每0.25秒移动一次
        current_time = pygame.time.get_ticks()
        if current_time - last_move_time >= 250:  # 严格每0.25秒移动一次
            last_move_time = current_time
            if direction == 'UP':
                snake_pos.insert(0, [snake_pos[0][0], snake_pos[0][1] - 10])
            if direction == 'DOWN':
                snake_pos.insert(0, [snake_pos[0][0], snake_pos[0][1] + 10])
            if direction == 'LEFT':
                snake_pos.insert(0, [snake_pos[0][0] - 10, snake_pos[0][1]])
            if direction == 'RIGHT':
                snake_pos.insert(0, [snake_pos[0][0] + 10, snake_pos[0][1]])
            
            # 检查是否吃到果实
            fruit_eaten = False
            for fruit in fruits[:]:
                # 允许蛇头在果实所在格子的任何位置都算吃到
                if (abs(snake_pos[0][0] - fruit[0]) < 10 and 
                    abs(snake_pos[0][1] - fruit[1]) < 10):
                    fruits.remove(fruit)
                    fruit_eaten = True
                    break
            
            # 如果没有吃到果实，移除尾部
            if not fruit_eaten:
                snake_pos.pop()
            else:
                # 如果吃到了果实，检查是否需要生成新果实
                if len(fruits) == 0:
                    spawn_fruits()
                    last_fruit_time = time.time()
            
            # 检查碰撞
            if check_collision():
                game_over = True
    
    # 绘制游戏
    draw_game()
    
    # 游戏结束处理
    if game_over:
        if show_game_over():
            # 重置游戏
            snake_pos = [[100, 50], [90, 50], [80, 50]]
            direction = 'RIGHT'
            change_to = direction
            spawn_fruits()
            last_fruit_time = time.time()
            game_over = False
        else:
            running = False
    
    clock.tick(60)

pygame.quit()
