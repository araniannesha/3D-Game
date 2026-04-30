from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import sys
import time
game_over = False
score = 0
camera_pos = [0.0, 1.0, 5.0]
camera_yaw = -90.0
camera_pitch = 0.0
keys = {'w': False, 's': False, 'a': False, 'd': False}
move_speed = 0.15
velocity_y = 0.0
gravity = 0.005
is_jumping = False
ground_level = 1.0
sound_pulses = []
pulse_speed = 0.20
pulse_max_radius = 25.0
pulse_cooldown = 0.5
_last_pulse_time = 0.0
collectibles = [] 
walls = []   
enemies = [] 
width, height = 800, 600
mouse_locked = True
def reset_game():
    global camera_pos, game_over, score, walls, enemies, collectibles, sound_pulses
    camera_pos = [0.0, 1.0, 5.0]
    game_over = False
    score = 0
    sound_pulses = []
    walls = []
    collectibles = []
    enemies = []
    create_environment()
    create_enemies()
    print("Game Restarted!")
def create_environment():
    global walls, collectibles
    layout = [
        [0, 0, -10], [5, 0, -10], [-5, 0, -10],
        [0, 0, 10], [5, 0, 10], [-5, 0, 10],
        [10, 0, 0], [10, 0, 5], [10, 0, -5],
        [-10, 0, 0], [-10, 0, 5], [-10, 0, -5],
        [3, 0, -3], [-3, 0, 3], [5, 0, 5], [-5, 0, -5]
    ]
    for pos in layout:
        walls.append({"pos": [float(pos[0]), 1.0, float(pos[2])], "size": 2.0, "reveal_t": 0.0})
    point_locations = [
        [0, 0.5, 0],    
        [-4, 0.5, -4],  
        [4, 0.5, 4],    
        [6, 0.5, -6]    
    ]
    for pos in point_locations:
        collectibles.append({
            "pos": pos, 
            "size": 0.5, 
            "active": True, 
            "reveal_t": 0.0 
        })
def create_enemies():
    global enemies
    enemies.append({"pos": [0.0, 0.6, -10.0], "speed": 0.04})
def to_rad(angle):
    return angle * math.pi / 180.0
def dist_sq(a, b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2
def check_wall_collision(x, z):
    player_radius = 0.5
    for w in walls:
        wx, wz = w["pos"][0], w["pos"][2]
        w_size = w["size"] / 2.0 
        if (x > wx - w_size - player_radius and x < wx + w_size + player_radius and
            z > wz - w_size - player_radius and z < wz + w_size + player_radius):
            return True 
    return False
def check_collectible_collision():
    global score
    for c in collectibles:
        if not c["active"]: continue
        dx = c["pos"][0] - camera_pos[0]
        dz = c["pos"][2] - camera_pos[2]
        distance = math.sqrt(dx*dx + dz*dz)
        if distance < 1.5:
            c["active"] = False 
            score += 10
            print(f"Score: {score}")
def update_movement():
    global camera_pos, velocity_y, is_jumping, game_over   
    if game_over: return  
    check_collectible_collision()
    rad_yaw = to_rad(camera_yaw)
    front_x = math.cos(rad_yaw)
    front_z = math.sin(rad_yaw)
    right_x = math.sin(rad_yaw - math.pi/2)
    right_z = -math.cos(rad_yaw - math.pi/2)
    new_x = camera_pos[0]
    new_z = camera_pos[2]
    if keys['w']: new_x += front_x * move_speed
    if keys['s']: new_x -= front_x * move_speed
    if keys['a']: new_x -= right_x * move_speed
    if keys['d']: new_x += right_x * move_speed
    if not check_wall_collision(new_x, camera_pos[2]): camera_pos[0] = new_x
    if not check_wall_collision(camera_pos[0], new_z): camera_pos[2] = new_z       
    check_collectible_collision()
    camera_pos[1] += velocity_y
    velocity_y -= gravity
    if camera_pos[1] <= ground_level:
        camera_pos[1] = ground_level
        velocity_y = 0.0
        is_jumping = False
def emit_sound_pulse():
    global _last_pulse_time, game_over
    if game_over: return   
    curr_time = time.time()
    if curr_time - _last_pulse_time < pulse_cooldown: return
    _last_pulse_time = curr_time
    sound_pulses.append({"center": list(camera_pos), "r": 0.1, "alive": True})
def update_logic(dt):
    global game_over 
    if game_over: return
    for w in walls:
        if w["reveal_t"] > 0: w["reveal_t"] = max(0, w["reveal_t"] - dt * 0.5)
    for c in collectibles:
        if c["reveal_t"] > 0.0: c["reveal_t"] = max(0.0, c["reveal_t"] - dt * 0.5)
    for pulse in sound_pulses:
        if not pulse["alive"]: continue
        pulse["r"] += pulse_speed * (dt * 60)      
        for w in walls:
            if abs(math.sqrt(dist_sq(pulse["center"], w["pos"])) - pulse["r"]) < 1.5: 
                w["reveal_t"] = 1.0
        for c in collectibles:
            if c["active"] and abs(math.sqrt(dist_sq(pulse["center"], c["pos"])) - pulse["r"]) < 1.5: 
                c["reveal_t"] = 1.0      
        if pulse["r"] > pulse_max_radius: pulse["alive"] = False
    sound_pulses[:] = [p for p in sound_pulses if p["alive"]]
    target = sound_pulses[-1]["center"] if sound_pulses else None
    for enemy in enemies:
        if target:
            ex, ez = enemy["pos"][0], enemy["pos"][2]
            tx, tz = target[0], target[2]
            dx, dz = tx - ex, tz - ez
            dist = math.sqrt(dx*dx + dz*dz)
            if dist > 0.5:
                enemy["pos"][0] += (dx/dist) * enemy["speed"]
                enemy["pos"][2] += (dz/dist) * enemy["speed"]
        dist_p = math.sqrt((enemy["pos"][0]-camera_pos[0])**2 + (enemy["pos"][2]-camera_pos[2])**2)
        if dist_p < 0.8:
            game_over = True
            print("GAME OVER")
def draw_text(x, y, text, r=1, g=1, b=1, large=False):
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)   
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()   
    glColor3f(r, g, b)
    glRasterPos2i(x, y)
    font = GLUT_BITMAP_TIMES_ROMAN_24 if large else GLUT_BITMAP_HELVETICA_18
    for char in text:
        glutBitmapCharacter(font, ord(char))       
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)   
    glEnable(GL_DEPTH_TEST)
def draw_walls():
    for w in walls:
        if w["reveal_t"] <= 0.05: continue
        glPushMatrix()
        glTranslatef(w["pos"][0], w["pos"][1], w["pos"][2])
        intensity = w["reveal_t"]
        glColor3f(0.0, intensity, intensity * 0.5)
        glutSolidCube(w["size"])
        glPopMatrix()
def draw_collectibles():
    for c in collectibles:
        if not c["active"]: continue
        if c["reveal_t"] <= 0.05: continue       
        glPushMatrix()
        glTranslatef(c["pos"][0], c["pos"][1], c["pos"][2])
        glColor3f(c["reveal_t"], c["reveal_t"], 0.0) 
        glRotatef(time.time() * 100, 0, 1, 0)
        glutSolidCube(c["size"])
        glPopMatrix()
def draw_enemies():
    for e in enemies:
        glPushMatrix()
        glTranslatef(e["pos"][0], e["pos"][1], e["pos"][2])
        glColor3f(1.0, 0.0, 0.0)
        glutSolidSphere(0.6, 16, 16)
        glPopMatrix()
def draw_pulses():
    glDisable(GL_LIGHTING)
    for p in sound_pulses:
        glPushMatrix()
        glTranslatef(p["center"][0], p["center"][1], p["center"][2])
        glColor4f(0.0, 0.8, 1.0, max(0, 1.0 - (p["r"] / pulse_max_radius)))
        glutWireSphere(p["r"], 16, 16)
        glPopMatrix()
def draw_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  
    update_movement()
    update_camera() 
    update_logic(0.03)
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_LINES)
    for i in range(-20, 21, 2):
        glVertex3f(i, 0, -20)
        glVertex3f(i, 0, 20)
        glVertex3f(-20, 0, i)
        glVertex3f(20, 0, i)
    glEnd()   
    draw_walls()
    draw_collectibles()
    draw_enemies()
    draw_pulses()
    draw_text(10, height - 30, f"SCORE: {score}", 1, 1, 0)   
    if game_over:
        draw_text(width//2 - 80, height//2, "GAME OVER", 1, 0, 0, large=True)
        draw_text(width//2 - 90, height//2 - 30, "Press 'R' to Restart", 1, 1, 1)
    glutSwapBuffers()
def update_camera():
    glLoadIdentity()
    rad_yaw = to_rad(camera_yaw)
    rad_pitch = to_rad(camera_pitch)
    lx = math.cos(rad_yaw) * math.cos(rad_pitch)
    ly = math.sin(rad_pitch)
    lz = math.sin(rad_yaw) * math.cos(rad_pitch)
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
              camera_pos[0] + lx, camera_pos[1] + ly, camera_pos[2] + lz,
              0.0, 1.0, 0.0)
def keyboard_down(key, x, y):
    global velocity_y, is_jumping, mouse_locked
    try:
        if isinstance(key, bytes): key = key.decode('utf-8')
        key = key.lower()
    except: return
    if key == 'r' and game_over:
        reset_game()
        return
    if key in keys: keys[key] = True
    if key == ' ': 
        if not is_jumping:
            velocity_y = 0.15
            is_jumping = True
    if key == 'e': emit_sound_pulse()
    if key == 'm':
        mouse_locked = not mouse_locked
        if mouse_locked: glutSetCursor(GLUT_CURSOR_NONE)
        else: glutSetCursor(GLUT_CURSOR_LEFT_ARROW)
    if key == '\x1b': sys.exit()
def keyboard_up(key, x, y):
    try:
        if isinstance(key, bytes): key = key.decode('utf-8')
        key = key.lower()
    except: return
    if key in keys: keys[key] = False
def mouse_motion(x, y):
    global camera_yaw, camera_pitch
    if not mouse_locked or game_over: return
    dx = x - width // 2
    dy = y - height // 2
    camera_yaw += dx * 0.1
    camera_pitch -= dy * 0.1
    if camera_pitch > 89: camera_pitch = 89
    if camera_pitch < -89: camera_pitch = -89
    glutWarpPointer(width // 2, height // 2)
def timer(v):
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)
def reshape(w, h):
    global width, height
    width, height = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, w/h if h!=0 else 1, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(width, height)
    glutCreateWindow(b"ECHOFORM - Final Version")  
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) 
    create_environment()
    create_enemies() 
    glutSetCursor(GLUT_CURSOR_NONE)
    glutDisplayFunc(draw_scene)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_motion)
    glutTimerFunc(0, timer, 0)
    glutMainLoop()
if __name__ == "__main__":
    main()