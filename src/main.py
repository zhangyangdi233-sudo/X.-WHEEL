
import math
import random
import sys
from dataclasses import dataclass
from typing import Callable, Optional

import pygame

WIDTH, HEIGHT = 1280, 720
FPS = 60
DEEP_BLUE = (12, 23, 37)
DEEPER_BLUE = (5, 12, 22)
GREEN = (53, 161, 70)
GREEN_2 = (63, 169, 67)
DARK_LINE = (7, 18, 30)
RED = (190, 34, 42)
AMBER = (229, 147, 62)
WHITE_GREEN = (166, 240, 172)
BLACK = (0, 0, 0)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


class Fonts:
    def __init__(self):
        candidates = [
            "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "Yu Gothic UI",
            "MS Gothic", "Noto Sans CJK SC", "Arial Unicode MS", "Arial",
        ]
        self.small = self._font(candidates, 18)
        self.ui = self._font(candidates, 24)
        self.mid = self._font(candidates, 34, bold=True)
        self.big = self._font(candidates, 74, bold=True)
        self.mono = self._font(["Consolas", "MS Gothic", "Microsoft YaHei"], 22)

    def _font(self, names, size, bold=False):
        for name in names:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        return pygame.font.Font(None, size)


class Typewriter:
    def __init__(self, speed=38):
        self.text = ""
        self.visible = 0.0
        self.speed = speed
        self.done = True

    def set(self, text):
        self.text = text
        self.visible = 0.0
        self.done = False

    def update(self, dt):
        if not self.done:
            self.visible += dt * self.speed
            if self.visible >= len(self.text):
                self.visible = len(self.text)
                self.done = True

    def skip(self):
        self.visible = len(self.text)
        self.done = True

    def current(self):
        return self.text[: int(self.visible)]


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("X. WHEEL - Ether Spice Demo")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()
        self.state = MainMenu(self)
        self.running = True
        self.t = 0.0
        self.noise_points = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.random()) for _ in range(520)]

    def change(self, state):
        self.state = state

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.t += dt
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
            self.state.handle(events)
            self.state.update(dt)
            self.state.draw(self.screen)
            self.draw_crt_overlay(self.screen)
            pygame.display.flip()
        pygame.quit()

    def draw_crt_overlay(self, surf):
        # scanlines
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(surf, (0, 0, 0, 40), (0, y), (WIDTH, y))
        # animated sparse phosphor noise
        for x, y, seed in self.noise_points[:240]:
            if random.random() < 0.12:
                col = GREEN if random.random() > 0.08 else RED
                surf.set_at((x, y), mix(surf.get_at((x, y))[:3], col, 0.28))
        # vignette
        v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(20):
            a = int(i * 4.5)
            pygame.draw.rect(v, (0, 0, 0, a), (i * 7, i * 4, WIDTH - i * 14, HEIGHT - i * 8), 2)
        surf.blit(v, (0, 0))


def draw_text(surface, font, text, pos, color=GREEN, max_width=None, line_gap=6):
    x, y = pos
    if max_width is None:
        surface.blit(font.render(text, True, color), (x, y))
        return y + font.get_height()
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if font.size(test)[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    for line in lines:
        surface.blit(font.render(line, True, color), (x, y))
        y += font.get_height() + line_gap
    return y


def corrupt(text, amount, rng=None):
    if amount <= 0:
        return text
    rng = rng or random
    marks = ["�", "░", "▓", "▯", "ﾐ", "ｻ", "//", "00", "NULL"]
    out = []
    for ch in text:
        if ch.strip() and rng.random() < amount:
            out.append(rng.choice(marks))
        else:
            out.append(ch)
    return "".join(out)


class MainMenu:
    def __init__(self, app):
        self.app = app
        self.hover_start = False
        self.snow = [(random.randrange(500), random.randrange(260), random.randrange(80, 210)) for _ in range(1300)]

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.change(Opening(self.app))
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if pygame.Rect(905, 308, 170, 48).collidepoint(e.pos):
                    self.app.change(Opening(self.app))
                if pygame.Rect(905, 370, 170, 48).collidepoint(e.pos):
                    self.app.running = False

    def update(self, dt):
        pass

    def draw(self, s):
        s.fill(DEEP_BLUE)
        mx, my = pygame.mouse.get_pos()
        px = (mx - WIDTH / 2) / WIDTH
        py = (my - HEIGHT / 2) / HEIGHT
        # room perspective
        floor = [(130 + px * 26, 650), (1150 + px * 26, 650), (930 + px * 90, 360 + py * 25), (350 + px * 90, 360 + py * 25)]
        back = pygame.Rect(230 + px * 35, 82 + py * 20, 820, 365)
        pygame.draw.rect(s, DEEPER_BLUE, back)
        pygame.draw.polygon(s, (9, 19, 31), floor)
        pygame.draw.line(s, GREEN, (back.left, back.bottom), (floor[0][0], floor[0][1]), 2)
        pygame.draw.line(s, GREEN, (back.right, back.bottom), (floor[1][0], floor[1][1]), 2)
        pygame.draw.rect(s, (20, 42, 54), (720 + px * 45, 206 + py * 18, 330, 255), border_radius=14)
        self.draw_crt(s, 748 + px * 48, 228 + py * 18)
        self.draw_emida_sitting(s, 365 + px * 70, 286 + py * 20)
        # menus on CRT side
        draw_text(s, self.app.fonts.mid, "X. WHEEL", (888, 236), WHITE_GREEN)
        start = pygame.Rect(905, 308, 170, 48)
        quit_r = pygame.Rect(905, 370, 170, 48)
        for rect, label in [(start, "START"), (quit_r, "EXIT")]:
            active = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(s, mix(DEEP_BLUE, GREEN, 0.18 if active else 0.08), rect, 1)
            draw_text(s, self.app.fonts.ui, label, (rect.x + 24, rect.y + 10), GREEN_2 if active else GREEN)
        draw_text(s, self.app.fonts.small, "鼠标轻微环视 / ENTER 开始", (890, 460), (90, 170, 102))

    def draw_crt(self, s, x, y):
        pygame.draw.rect(s, DARK_LINE, (x, y, 250, 175), border_radius=16)
        pygame.draw.rect(s, (3, 10, 15), (x + 16, y + 15, 218, 132), border_radius=8)
        for _ in range(600):
            nx = x + 18 + random.randrange(214)
            ny = y + 17 + random.randrange(128)
            c = random.choice([(25, 70, 35), (60, 130, 70), (12, 23, 37), (100, 160, 100)])
            s.set_at((int(nx), int(ny)), c)
        if random.random() < 0.08:
            draw_text(s, self.app.fonts.small, "エーテル・スパイス", (x + 38, y + 67), RED)
        pygame.draw.rect(s, GREEN, (x + 16, y + 15, 218, 132), 2, border_radius=8)
        pygame.draw.rect(s, DARK_LINE, (x + 82, y + 150, 82, 18))

    def draw_emida_sitting(self, s, x, y):
        # beanbag
        pygame.draw.ellipse(s, (14, 35, 45), (x - 70, y + 232, 360, 105))
        pygame.draw.ellipse(s, (26, 61, 55), (x - 45, y + 218, 300, 85), 3)
        # simplified green silhouette in supplied style
        g = GREEN
        pygame.draw.polygon(s, g, [(x+25,y+45),(x+70,y+20),(x+150,y+34),(x+190,y+86),(x+176,y+180),(x+198,y+260),(x+42,y+258),(x+8,y+178)])
        pygame.draw.circle(s, g, (int(x+100), int(y+112)), 78)
        for dx, dy, w, h in [(-4,88,54,160),(150,78,60,175),(23,24,54,160),(115,26,68,155),(-30,115,60,135)]:
            pygame.draw.ellipse(s, g, (x+dx, y+dy, w, h))
        pygame.draw.rect(s, g, (x+58, y+182, 92, 98))
        # dark facial/line details
        for pts in [
            [(x+58,y+104),(x+86,y+100),(x+104,y+109)],
            [(x+121,y+104),(x+150,y+98),(x+168,y+108)],
            [(x+80,y+158),(x+111,y+163),(x+139,y+158)],
            [(x+98,y+129),(x+106,y+140),(x+101,y+145)],
        ]:
            pygame.draw.lines(s, DARK_LINE, False, pts, 3)
        for lx in [x+34, x+54, x+164, x+184, x+9, x+213]:
            pygame.draw.line(s, DARK_LINE, (lx, y+80), (lx-18, y+235), 3)
        pygame.draw.line(s, DARK_LINE, (x+62, y+213), (x+150, y+213), 3)


class Opening:
    def __init__(self, app):
        self.app = app
        self.idx = 0
        self.timer = 0
        self.tw = Typewriter(54)
        self.segments = []
        chats = [
            ("CLOCK_99", "还有二十几分钟就2000年了，银行、电车、医院会不会一起报错啊？哈哈……应该不会吧？"),
            ("NEON_KO", "我听说零点以后，系统会把“不存在的人”直接删掉。"),
            ("NORTHLINE", "老旧电塔会收到未来信号这个说法你们看了吗？有人贴了照片。"),
            ("404MAMA", "电视雪花里能看到明天。别笑，我表哥真的看见过。"),
            ("Y2K_KID", "如果玩笑被很多人当真，那它是不是就不算玩笑了？"),
            ("SALTROOT", "城市里所有塔都在等零点，像一群不知道自己信什么的人。"),
        ]
        self.segments.append(("tower", "风从塔架之间穿过去。埃弥亣不知道自己为什么站在这里。"))
        for i, chat in enumerate(chats):
            self.segments.append(("chat", chat))
            self.segments.append(("tower", self.tower_line(i)))
        self.tw.set(self.current_text())

    def tower_line(self, i):
        lines = [
            "远处的信号灯闪了一下。刚才那句话从天线里漏出来。",
            "栏杆震动。她听见“删掉”这个词在风里重复。",
            "梯子、天线、雪花和聊天室文字短暂重叠。",
            "CRT雪花像灰尘一样落在塔顶。红色颗粒一闪而过。",
            "绿色噪点中混进一小片红。它不像线索，更像某种味道。",
            "塔顶现实裂开。以太香料没有名字，却已经附着在每一句话上。",
        ]
        return lines[i]

    def current_text(self):
        typ, data = self.segments[self.idx]
        if typ == "chat":
            name, msg = data
            return f"{name}: {msg}"
        return data

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.next()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.next()

    def next(self):
        if not self.tw.done:
            self.tw.skip()
            return
        self.idx += 1
        if self.idx >= len(self.segments):
            self.app.change(ChapterTitle(self.app))
            return
        self.tw.set(self.current_text())

    def update(self, dt):
        self.timer += dt
        self.tw.update(dt)

    def draw(self, s):
        typ, data = self.segments[self.idx]
        if typ == "chat":
            self.draw_chatroom(s, data)
        else:
            self.draw_tower(s, data)

    def draw_tower(self, s, line):
        s.fill(DEEP_BLUE)
        # city
        for i in range(34):
            x = i * 42 + int(math.sin(i) * 18)
            h = 70 + (i * 17) % 160
            pygame.draw.rect(s, (6, 14, 24), (x, HEIGHT - h, 34, h))
            if i % 4 == 0:
                pygame.draw.rect(s, GREEN, (x + 8, HEIGHT - h + 20, 5, 5))
        # tower lattice
        base_y = 650
        top = (WIDTH // 2 + int(math.sin(self.timer) * 8), 80)
        left_base = (430, base_y)
        right_base = (850, base_y)
        pygame.draw.line(s, GREEN, top, left_base, 4)
        pygame.draw.line(s, GREEN, top, right_base, 4)
        for y in range(130, 640, 62):
            t = (y - 80) / (base_y - 80)
            lx = int(lerp(top[0], left_base[0], t))
            rx = int(lerp(top[0], right_base[0], t))
            pygame.draw.line(s, GREEN_2, (lx, y), (rx, y), 2)
            pygame.draw.line(s, GREEN_2, (lx, y), (rx, y + 48), 1)
            pygame.draw.line(s, GREEN_2, (rx, y), (lx, y + 48), 1)
        # ladder language
        ladder_x = 585
        pygame.draw.line(s, GREEN, (ladder_x, 160), (ladder_x, 638), 3)
        pygame.draw.line(s, GREEN, (ladder_x + 42, 160), (ladder_x + 42, 638), 3)
        for y in range(172, 630, 28):
            pygame.draw.line(s, mix(GREEN, RED, 0.15 if self.idx > 7 else 0), (ladder_x, y), (ladder_x + 42, y + int(math.sin(self.timer * 4 + y) * 2)), 2)
        # Emida small silhouette
        pygame.draw.circle(s, GREEN, (642, 370), 22)
        pygame.draw.rect(s, GREEN, (626, 392, 34, 62))
        pygame.draw.line(s, DARK_LINE, (634, 369), (653, 370), 2)
        # ether spice red particles later
        if self.idx >= 7:
            for _ in range(80):
                angle = random.random() * math.tau
                r = random.random() * 130
                x = 640 + math.cos(angle) * r
                y = 330 + math.sin(angle) * r * 0.6
                col = RED if random.random() < 0.35 else GREEN
                pygame.draw.rect(s, col, (x, y, 2, 2))
        panel = pygame.Rect(150, 565, 980, 98)
        pygame.draw.rect(s, (4, 13, 22), panel)
        pygame.draw.rect(s, GREEN, panel, 2)
        draw_text(s, self.app.fonts.ui, self.tw.current(), (178, 592), WHITE_GREEN, 920)
        draw_text(s, self.app.fonts.small, "SPACE / CLICK", (1015, 670), (70, 140, 82))

    def draw_chatroom(self, s, data):
        s.fill((3, 8, 16))
        name, msg = data
        pygame.draw.rect(s, (9, 17, 29), (110, 60, 1060, 600))
        pygame.draw.rect(s, GREEN, (110, 60, 1060, 600), 2)
        pygame.draw.rect(s, (16, 35, 42), (110, 60, 1060, 44))
        draw_text(s, self.app.fonts.mono, "1999/12/31 23:5?  Y2K_PUBLIC_CHAT", (132, 70), GREEN)
        pygame.draw.rect(s, (5, 12, 20), (146, 145, 988, 330))
        pygame.draw.rect(s, (40, 80, 56), (146, 145, 988, 330), 1)
        draw_text(s, self.app.fonts.mono, f"<{name}>", (176, 182), GREEN_2)
        amount = 0.02 + self.idx * 0.002
        draw_text(s, self.app.fonts.ui, corrupt(self.tw.current(), amount), (176, 226), WHITE_GREEN, 890)
        # chat noise lines
        for i in range(11):
            y = 505 + i * 12
            pygame.draw.line(s, (10, 35, 24), (170, y), (1090 - i * 14, y), 1)
        if self.idx >= 9 and random.random() < 0.85:
            pygame.draw.rect(s, RED, (1010 + random.randrange(30), 390 + random.randrange(60), 4, 4))
        draw_text(s, self.app.fonts.small, "每个网友一句话。然后塔顶会回答。", (150, 620), (88, 160, 95))


class ChapterTitle:
    def __init__(self, app):
        self.app = app
        self.timer = 0

    def handle(self, events):
        pass

    def update(self, dt):
        self.timer += dt
        if self.timer > 3.2:
            self.app.change(ChatDemo(self.app))

    def draw(self, s):
        s.fill(BLACK)
        a = clamp((self.timer - 0.25) / 0.6, 0, 1) * clamp((3.0 - self.timer) / 0.5, 0, 1)
        col = mix(BLACK, GREEN, a)
        title = self.app.fonts.big.render("Capitolo 1", True, col)
        subtitle = self.app.fonts.mid.render("小打小闹的人们", True, mix(BLACK, WHITE_GREEN, a))
        s.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 34)))
        s.blit(subtitle, subtitle.get_rect(center=(WIDTH//2, HEIGHT//2 + 55)))


@dataclass
class Message:
    speaker: str
    text: str
    contact: str = "麦乐芬"
    pollution: float = 0.0
    action: Optional[str] = None


class MeditationPopup:
    def __init__(self):
        self.rect = pygame.Rect(735, 180, 355, 155)
        self.drag = False
        self.offset = (0, 0)
        self.time_left = 8.0
        self.finished = False
        self.closed = False

    def handle(self, e):
        if self.closed:
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if pygame.Rect(self.rect.right - 28, self.rect.y + 6, 18, 18).collidepoint(e.pos):
                self.closed = True
            elif pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 30).collidepoint(e.pos):
                self.drag = True
                self.offset = (e.pos[0] - self.rect.x, e.pos[1] - self.rect.y)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = False
        elif e.type == pygame.MOUSEMOTION and self.drag:
            self.rect.x = clamp(e.pos[0] - self.offset[0], 20, WIDTH - self.rect.w - 20)
            self.rect.y = clamp(e.pos[1] - self.offset[1], 20, HEIGHT - self.rect.h - 20)

    def update(self, dt):
        if not self.closed and not self.finished:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.finished = True

    def draw(self, s, fonts):
        if self.closed:
            return
        pygame.draw.rect(s, (190, 202, 188), self.rect)
        pygame.draw.rect(s, (2, 54, 30), self.rect, 2)
        pygame.draw.rect(s, (18, 81, 46), (self.rect.x, self.rect.y, self.rect.w, 30))
        draw_text(s, fonts.small, "冥想.exe", (self.rect.x + 10, self.rect.y + 5), (220, 245, 222))
        pygame.draw.rect(s, (92, 0, 0), (self.rect.right - 28, self.rect.y + 7, 18, 16))
        draw_text(s, fonts.small, "x", (self.rect.right - 24, self.rect.y + 4), (255, 220, 220))
        if self.finished:
            text = "你好像参悟到了什么，\n又好像什么也没有参悟到。"
        else:
            text = f"请等待 {self.time_left:04.1f} 秒完成冥想。\n你可以把这个窗口放在一旁。"
        y = self.rect.y + 50
        for line in text.split("\n"):
            draw_text(s, fonts.small, line, (self.rect.x + 24, y), (8, 35, 22))
            y += 30
        if not self.finished:
            pygame.draw.rect(s, (30, 65, 45), (self.rect.x + 24, self.rect.y + 119, 305, 15), 1)
            pygame.draw.rect(s, (40, 130, 62), (self.rect.x + 26, self.rect.y + 121, int(301 * (1 - self.time_left / 8.0)), 11))


class ChatDemo:
    def __init__(self, app):
        self.app = app
        self.tw = Typewriter(44)
        self.msg_i = 0
        self.popup = None
        self.contacts = ["麦乐芬", "智者", "同学", "系统"]
        self.messages = [
            Message("系统", "联系人『麦乐芬』已上线。联系人『智者』已上线。", "系统", 0.02),
            Message("麦乐芬", "呀。你也在等世界结束吗？那太好了，等的时候总得找点乐子。", "麦乐芬", 0.02),
            Message("埃弥亣", "我只是……想找人说话。", "麦乐芬", 0.0),
            Message("麦乐芬", "说话很好啊。说出来就会变成真的。变成真的以后，就可以拿来玩。", "麦乐芬", 0.03),
            Message("同学", "别这样嘛，我们只是小打小闹。你不会当真了吧？", "同学", 0.04),
            Message("埃弥亣", "差不多两三岁的时候，我用火柴烧掉过一整栋房子。", "系统", 0.0),
            Message("埃弥亣", "还好是旧房子。整个院子也没什么人。没有谁出事。", "系统", 0.0),
            Message("埃弥亣", "我总是能看见一片红色。红色慢慢扩散，像是在吃掉整个世界。", "系统", 0.0),
            Message("系统", "检测到以太香料 / エーテル・スパイス。", "系统", 0.06, "spawn_popup"),
            Message("麦乐芬", "冥想窗口弹出来了！别管它，倒计时也是一种娱乐。", "麦乐芬", 0.05),
            Message("智者", "", "智者", 0.0),
            Message("系统", "智者 已读。", "智者", 0.02),
            Message("同学", "你看，大家都在说你是千年虫的▯▯。这不就很有人气吗？", "同学", 0.1),
            Message("麦乐芬", "如果2012真的会来，那今天先玩到今天结束就好了。", "麦乐芬", 0.08),
            Message("系统", "梯子表面出现无法擦掉的红色颗粒。", "系统", 0.12),
        ]
        self.tw.set(self.format_msg(self.messages[0]))
        self.pollution = 0.03

    def format_msg(self, msg):
        if msg.speaker == "智者" and msg.text == "":
            return "智者："
        return f"{msg.speaker}：{msg.text}"

    def handle(self, events):
        for e in events:
            if self.popup:
                self.popup.handle(e)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.next()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # avoid consuming popup drag start as advance if on popup
                if self.popup and self.popup.rect.collidepoint(e.pos):
                    continue
                self.next()

    def next(self):
        if not self.tw.done:
            self.tw.skip()
            return
        current = self.messages[self.msg_i]
        if current.action == "spawn_popup" and self.popup is None:
            self.popup = MeditationPopup()
        self.msg_i += 1
        if self.msg_i >= len(self.messages):
            self.app.change(DemoFinale(self.app))
            return
        self.pollution = min(0.18, self.pollution + 0.012)
        self.tw.set(self.format_msg(self.messages[self.msg_i]))

    def update(self, dt):
        self.tw.update(dt)
        if self.popup:
            self.popup.update(dt)

    def draw(self, s):
        s.fill(DEEP_BLUE)
        # desktop background
        for i in range(0, WIDTH, 32):
            pygame.draw.line(s, (8, 20, 32), (i, 0), (i, HEIGHT))
        for i in range(0, HEIGHT, 32):
            pygame.draw.line(s, (8, 20, 32), (0, i), (WIDTH, i))
        pygame.draw.rect(s, (7, 15, 25), (70, 55, 1140, 595))
        pygame.draw.rect(s, GREEN, (70, 55, 1140, 595), 2)
        pygame.draw.rect(s, (15, 50, 38), (70, 55, 1140, 36))
        draw_text(s, self.app.fonts.small, "XW_CHAT_2010 - contacts", (88, 63), WHITE_GREEN)
        # contacts
        pygame.draw.rect(s, (4, 13, 22), (92, 115, 250, 500))
        for idx, c in enumerate(self.contacts):
            y = 142 + idx * 78
            active = self.messages[self.msg_i].contact == c
            pygame.draw.rect(s, mix(DEEP_BLUE, GREEN, 0.16 if active else 0.04), (112, y, 210, 52))
            pygame.draw.rect(s, GREEN if active else (34, 80, 48), (112, y, 210, 52), 1)
            dot = RED if c == "智者" else GREEN
            pygame.draw.circle(s, dot, (132, y + 26), 6)
            label = c if c != "智者" else "智者   已读"
            draw_text(s, self.app.fonts.ui, label, (150, y + 12), WHITE_GREEN if active else GREEN)
        # chat panel
        pygame.draw.rect(s, (5, 12, 20), (370, 115, 805, 500))
        pygame.draw.rect(s, GREEN, (370, 115, 805, 500), 1)
        # Emida avatar style
        self.draw_avatar(s, 405, 150)
        msg = self.messages[self.msg_i]
        shown = corrupt(self.tw.current(), msg.pollution + self.pollution * 0.4)
        draw_text(s, self.app.fonts.ui, shown, (535, 160), WHITE_GREEN, 575)
        # ether spice visual specks on key moments
        if self.msg_i >= 8:
            for _ in range(70):
                x = random.randrange(370, 1170)
                y = random.randrange(115, 615)
                col = RED if random.random() < 0.45 else GREEN
                if random.random() < 0.35:
                    pygame.draw.rect(s, col, (x, y, 2, 2))
        draw_text(s, self.app.fonts.small, "SPACE / CLICK 推进。冥想弹窗出现后可以拖动。", (375, 625), (80, 150, 90))
        if self.popup:
            self.popup.draw(s, self.app.fonts)

    def draw_avatar(self, s, x, y):
        pygame.draw.rect(s, (2, 9, 15), (x, y, 90, 90))
        pygame.draw.rect(s, GREEN, (x, y, 90, 90), 1)
        pygame.draw.circle(s, GREEN, (x + 45, y + 40), 29)
        pygame.draw.polygon(s, GREEN, [(x+14,y+28),(x+30,y+8),(x+54,y+12),(x+76,y+30),(x+66,y+82),(x+21,y+82)])
        pygame.draw.line(s, DARK_LINE, (x+28, y+38), (x+42, y+36), 2)
        pygame.draw.line(s, DARK_LINE, (x+51, y+36), (x+68, y+38), 2)
        pygame.draw.line(s, DARK_LINE, (x+38, y+61), (x+55, y+61), 2)


class DemoFinale:
    def __init__(self, app):
        self.app = app
        self.timer = 0
        self.choice = 0

    def handle(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.choice = 1 - self.choice
                if e.key == pygame.K_ESCAPE:
                    self.app.change(MainMenu(self.app))
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if pygame.Rect(390, 590, 190, 44).collidepoint(e.pos):
                    self.choice = 0
                elif pygame.Rect(700, 590, 190, 44).collidepoint(e.pos):
                    self.choice = 1

    def update(self, dt):
        self.timer += dt

    def draw(self, s):
        s.fill(DEEP_BLUE)
        # distant second babel tower
        cx = WIDTH // 2
        pygame.draw.polygon(s, (8, 17, 28), [(cx-220,690),(cx+220,690),(cx+78,95),(cx-56,95)])
        for y in range(150, 680, 46):
            w = int(60 + (y - 100) * 0.34)
            pygame.draw.line(s, GREEN, (cx - w, y), (cx + w, y + int(math.sin(self.timer + y) * 4)), 2)
        pygame.draw.line(s, GREEN, (cx-50, 100), (cx-200, 690), 4)
        pygame.draw.line(s, GREEN, (cx+75, 100), (cx+210, 690), 4)
        for _ in range(180):
            x = random.randrange(cx-240, cx+240)
            y = random.randrange(80, 680)
            if random.random() < 0.45:
                pygame.draw.rect(s, RED, (x, y, 2, 2))
        draw_text(s, self.app.fonts.mid, "第二巴别塔的轮廓在远处浮现。", (365, 70), WHITE_GREEN)
        draw_text(s, self.app.fonts.ui, "以太香料变得更明显。它仍然没有解释自己。", (390, 126), GREEN, 520)
        opts = [("发射信号", 390), ("停下", 700)]
        for i, (label, x) in enumerate(opts):
            rect = pygame.Rect(x, 590, 190, 44)
            pygame.draw.rect(s, mix(DEEP_BLUE, RED if i == 0 else GREEN, 0.22 if self.choice == i else 0.08), rect)
            pygame.draw.rect(s, RED if i == 0 else GREEN, rect, 2)
            draw_text(s, self.app.fonts.ui, label, (x + 42, 599), WHITE_GREEN)
        if self.choice == 0:
            draw_text(s, self.app.fonts.small, "世界只收到乱码。", (560, 650), RED)
        else:
            draw_text(s, self.app.fonts.small, "今天的落日好美啊。", (548, 650), AMBER)
        draw_text(s, self.app.fonts.small, "ESC 返回标题", (30, 680), (90, 150, 95))


def main():
    try:
        App().run()
    except Exception as exc:
        pygame.quit()
        raise exc


if __name__ == "__main__":
    main()
