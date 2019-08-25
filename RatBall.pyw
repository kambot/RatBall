from time import strftime, sleep, time, mktime
# from datetime import datetime
# from calendar import monthrange
import math, random

import sys, os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeyEvent, QPainter ,QImage, QPen, QIcon, QPixmap, QColor, QBrush, QCursor, QFont, QPalette, QTextOption
from PyQt5.QtCore import Qt, QPoint, QPointF, QSize, QEvent, QTimer, QCoreApplication, QRectF

from random import choice

class BallConfig():
    def __init__(self, name, color, d, index, prob):
        self.name = name
        self.color = color
        self.d = d
        self.index = index
        self.prob = prob

class Ball():
    def __init__(self):

        self.bx = 0
        self.by = 0
        self.bd = 0

        self.bst = 0
        self.bs = 0
        self.bxt = 0
        self.byt = 0

        self.dur = 0
        self.life = 0
        self.delete = False
        self.active = 0

        self.angle = 0
        self.random_angle = False
        self.random_change = 0
        self.colliding = False
        self.collidingp = False # prior

        # self.kill_ball = False
        # self.large_ball = False
        self.btype = ""
        self.bcolor = Qt.gray


    def init(self):

        self.pi = math.pi
        self.conv = self.pi / 180

        self.trajectory()

    def trajectory(self):
        self.bxt = math.cos(self.angle)
        self.byt = math.sin(self.angle)

    def update(self, dt, w, h, p_active):

        if p_active:
            self.dur += dt
            if self.dur >= self.life:
                self.delete = True
                return

        self.random_change += dt
        randomize = False
        if self.random_angle:
            if self.random_change >= 1:
                randomize = True
                self.random_change = 0

        if self.dur >= 2 and not self.active:
            self.active = True

        self.trajectory()

        self.bx += dt * (self.bs / self.bst) * self.bxt
        self.by += dt * (self.bs / self.bst) * self.byt

        ycollision = False
        xcollision = False

        # right side of screen
        if self.bx  + self.bd/2 > w:
            self.bx = w - self.bd/2
            xcollision = True
        # left side
        elif self.bx - self.bd/2 < 0:
            self.bx = 0 + self.bd/2
            xcollision = True

        # bottom
        if self.by + self.bd/2 > h:
            self.by = h - self.bd/2
            ycollision = True
        # top
        elif self.by - self.bd/2 < 0:
            self.by = 0 + self.bd/2
            ycollision = True

        if xcollision:
            self.angle = (self.pi - self.angle)
        if ycollision:
            self.angle = (self.pi * 2 - self.angle)

        if self.random_angle and randomize:
            self.angle = choice(range(360)) * self.conv



class RatBall(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        # self.pid = os.getpid()
        # self.root = os.path.dirname(os.path.abspath(__file__))  + "\\"

        self.setWindowTitle("Rat Ball")

        self.setFont(QFont('Arial', 10))
        QToolTip.setFont(QFont('Arial', 8))

        self.pi = math.pi
        self.conv = self.pi / 180

        # default window size and heights
        self.w = 300
        self.h = 300

        self.p_x = self.w / 2 # player x coord
        self.p_y = self.h / 2 # player y coord

        self.p_d_def = 15
        self.p_d = self.p_d_def+0 # player width


        self.m_x = 0 # player x direction
        self.m_y = 0 # player y direction
        self.p_speed_def = 6 # player speed
        self.p_speed = self.p_speed_def+0
        self.p_speed_time = 50 / 1000 # 50 milliseconds

        self.bcollission = False # ball collission flag
        self.bcol_dur = 1
        self.bcol_timer = 0

        self.speed_incr = 1.5
        self.d_incr = 3.5 # diameter increase

        self.has_powerup = False

        self.wall_bounce = False
        self.wall_bounce_timer = 0
        self.wall_bounce_dur = 10 # seconds

        self.inv = False
        self.inv_timer = 0
        self.inv_dur = 5 # seconds

        self.max_balls = 9

        self.b_d = 9

        self.b_speed_min = 4
        self.b_speed_max = 9

        self.life_min = 7 # seconds
        self.life_max = 15

        self.spawn_min = 2 # seconds
        self.spawn_max = 5

        self.spawn_time = 0
        self.spawn_wait = random.choice(range(self.spawn_min, self.spawn_max+1))

        # x = BallConfig("red")
        # print(x.color)

        self.b_config = [
            BallConfig("speed incr", Qt.red, self.b_d, 0, 20),
            BallConfig("speed decr", Qt.darkGreen, self.b_d, 1, 15),
            BallConfig("kill ball", Qt.blue, self.b_d, 2, 25),
            BallConfig("enlarge", Qt.magenta, self.b_d, 3, 15),
            BallConfig("shrink", Qt.darkYellow, self.b_d, 4, 10),
            BallConfig("wall bounce", Qt.cyan, self.b_d, 5, 10),
            BallConfig("invincible", Qt.yellow, self.b_d, 6, 5)
        ]

        self.b_colors = [x.color for x in self.b_config]
        self.b_types = [x.name for x in self.b_config]
        self.b_probs = [x.prob for x in self.b_config]


        # self.b_colors = [Qt.red, Qt.darkGreen, Qt.blue, Qt.magenta, Qt.cyan, Qt.yellow]
        # self.b_types = ["speed incr","speed decr","kill ball","enlarge","wall bounce","invincible"]
        # self.b_probs = [25,20,25,15,10,5]
        self.cdf_list()

        self.balls = []
        self.init_balls()

        self.t0 = time()
        self.t1 = time()
        self.dt = 0

        self.widget = QWidget()

        self.setCentralWidget(self.widget)

        self.setGeometry(300, 300, self.w, self.h)
        self.center()

        self.timer = QTimer()
        self.timer.timeout.connect(self.updater)
        self.timer.start(10)

        self.installEventFilter(self)

        self.p_active = False
        self.paused = False
        self.tr0 = time()
        self.dur = 0

        # self.def_bg_color = self.widget.palette().color(QPalette.Background)
        # print(self.def_bg_color.getRgb())
        
        self.set_bg_color(QColor(240, 240, 240, 255))



    def cdf_list(self):
        self.b_probs = [int(x/sum(self.b_probs)*100000) for x in self.b_probs]
        self.b_cdf = []
        s = 0
        for i in self.b_probs:
            s += i
            self.b_cdf.append(s)
        print(self.b_cdf)

    def random_ball_type(self):
        r = random.choice(range(1,self.b_cdf[-1]+1))
        m = min([x for x in self.b_cdf if r <= x])
        i = self.b_cdf.index(m)
        return self.b_types[i]

    def init_balls(self):
        for _ in range( random.choice(range(1,min(5, self.max_balls))) ):
            self.balls.append(self.create_ball())

    def create_ball(self):
        balli = Ball()
        balli.bx = random.choice(range(self.w))
        balli.by = random.choice(range(self.h))

        balli.bs = random.choice(range(self.b_speed_min, self.b_speed_max+1))
        balli.bst = self.p_speed_time
        balli.angle = choice(range(360)) * self.conv
        balli.random_angle = random.choice([False]*7 + [True]*3)

        balli.btype = self.random_ball_type()

        config_index = self.b_types.index(balli.btype)
        balli.bd = self.b_config[config_index].d

        balli.bcolor = self.b_colors[config_index]
        balli.life = random.choice(range(self.life_min, self.life_max+1)) + 2
        balli.init()
        return balli

    def format_dur(self):
        return "{:.0f}".format(self.dur)

    def default_painter(self):
        self.pen.setWidth(1)
        self.pen.setColor(Qt.black)
        self.painter.setPen(self.pen)
        self.painter.setBrush(Qt.black)

    def set_painter(self, penColor, penWidth, brushColor):
        self.pen.setWidth(penWidth)
        self.pen.setColor(penColor)
        self.painter.setPen(self.pen)
        self.painter.setBrush(brushColor)

    def paintEvent(self, event):

        self.painter = QPainter(self)
        self.painter.setRenderHint(QPainter.Antialiasing, True)
        self.pen = QPen()
        self.default_painter()

        # draw the player ball first
        if self.wall_bounce:
            color = self.b_colors[self.b_types.index("wall bounce")]
            self.set_painter(color, 2, Qt.black)
        elif self.inv:
            color = self.b_colors[self.b_types.index("invincible")]
            self.set_painter(color, 2, Qt.black)

        self.painter.drawEllipse(self.p_x - self.p_d/2,self.p_y - self.p_d/2,self.p_d, self.p_d)

        self.default_painter()

        # draw the other balls
        for i in range(len(self.balls)):
            balli = self.balls[i]
            if balli.active:
                self.set_painter(Qt.black, 1, balli.bcolor)
            else:
                self.set_painter(Qt.black, 1, Qt.gray)
            self.painter.drawEllipse(balli.bx - balli.bd/2,balli.by - balli.bd/2, balli.bd, balli.bd)

        self.default_painter()

        # time remaining for wall bounce
        if self.wall_bounce:
            tr = "{:.1f}".format(self.wall_bounce_dur - self.wall_bounce_timer)
            self.painter.drawText(QRectF(QPoint(0,0),QPoint(self.w,self.h)),Qt.AlignTop | Qt.AlignRight, tr)
        elif self.inv:
            tr = "{:.1f}".format(self.inv_dur - self.inv_timer)
            self.painter.drawText(QRectF(QPoint(0,0),QPoint(self.w,self.h)),Qt.AlignTop | Qt.AlignRight, tr)

        # if collission
        if self.bcollission:
            self.bcol_timer += self.dt
            if self.bcol_timer < self.bcol_dur:
                self.painter.drawText(QRectF(QPoint(0,0),QPoint(self.w,self.h)),Qt.AlignBottom | Qt.AlignRight, "x")
            else:
                self.bcol_timer = 0
                self.bcollission = False

        if not self.paused:
            self.dur = time() - self.tr0
            self.painter.drawText(QRectF(QPoint(0,0),QPoint(self.w,self.h)),Qt.AlignTop | Qt.AlignLeft, self.format_dur())

            if not self.p_active:

                y = 35
                self.painter.drawText(QRectF(QPoint(0,35),QPoint(self.w,self.h)),Qt.AlignCenter, "Press Any Arrow Key To Start")

                y += 1
                for i in range(len(self.b_types)):
                    y += 35
                    self.painter.setPen(Qt.black)
                    self.painter.drawText(QRectF(QPoint(-1,1.5+y),QPoint(self.w,self.h)),Qt.AlignCenter, self.b_types[i])
                    self.painter.setPen(self.b_colors[i])
                    self.painter.drawText(QRectF(QPoint(0,y),QPoint(self.w,self.h)),Qt.AlignCenter, self.b_types[i])
        else:

            self.set_painter(Qt.white, 1, Qt.black)
            self.painter.drawText(QRectF(QPoint(-1,1.5),QPoint(self.w,self.h)),Qt.AlignCenter, "SCORE: " + self.format_dur())

            self.default_painter()
            self.painter.drawText(QRectF(QPoint(0,0),QPoint(self.w,self.h)),Qt.AlignCenter, "SCORE: " + self.format_dur())


            self.set_painter(Qt.white, 1, Qt.black)
            self.painter.drawText(QRectF(QPoint(-1,35+1.5),QPoint(self.w,self.h)),Qt.AlignCenter, "Press Enter to Restart")

            self.default_painter()
            self.painter.drawText(QRectF(QPoint(0,35),QPoint(self.w,self.h)),Qt.AlignCenter, "Press Enter to Restart")

            self.balls = []

        del self.painter



    def update_player(self):

        if self.m_x != 0 or self.m_y != 0:
            self.p_active = True

        self.wall_bounce_timer += self.dt
        if self.wall_bounce_timer >= self.wall_bounce_dur and self.wall_bounce:
            self.wall_bounce = False
            self.has_powerup = False

        self.inv_timer += self.dt
        if self.inv_timer >= self.inv_dur and self.inv:
            self.inv = False
            self.has_powerup = False

        # update player
        self.p_x += (self.m_x * self.p_speed / self.p_speed_time * self.dt) * (not self.paused)
        self.p_y += (self.m_y * self.p_speed / self.p_speed_time * self.dt) * (not self.paused)

        collission = False

        # right side of screen
        if self.p_x  + self.p_d/2 > self.w:
            self.p_x = self.w - self.p_d/2
            self.m_x = -1
            collission = True

        # left side
        elif self.p_x - self.p_d/2 < 0:
            self.p_x = 0 + self.p_d/2
            self.m_x = 1
            collission = True

        # bottom
        if self.p_y + self.p_d/2 > self.h:
            self.p_y = self.h - self.p_d/2
            self.m_y = -1
            collission = True

        # top
        elif self.p_y - self.p_d/2 < 0:
            self.p_y = 0 + self.p_d/2
            self.m_y = 1
            collission = True

        if collission:

            if not self.wall_bounce and not self.inv:
                self.dur = time() - self.tr0
                self.tr0 = time()
                self.paused = True
                self.p_active = False

    def update_balls(self):
        balls = []
        for i in range(len(self.balls)):
            self.balls[i].update(self.dt, self.w, self.h, self.p_active)
            if not self.balls[i].delete:
                balls.append(self.balls[i])
        self.balls = [x for x in balls]

    def updater(self):

        self.t1 = time()
        self.dt = self.t1 - self.t0
        self.t0 = self.t1+0

        self.spawn_time += self.dt

        self.update_player()

        self.update_balls()

        # check for ball collissions
        for i in range(len(self.balls)):
            balli = self.balls[i]

            if not balli.active:
                continue

            dx = (balli.bx) - (self.p_x)
            dy = (balli.by) - (self.p_y)
            h = ((dx)**2 + (dy)**2)**0.5

            if (balli.bd/2 + self.p_d/2) >= h:
                if balli.collidingp == False:
                    # print("collission", i)

                    btype = balli.btype

                    if not self.inv:
                        if btype == "kill ball":
                            self.end = True
                            self.paused = True
                        elif btype == "speed incr":
                            self.p_speed += self.speed_incr
                        elif btype == "speed decr":
                            self.p_speed -= self.speed_incr
                            self.p_speed = max(1, self.p_speed)
                        elif btype == "enlarge":
                            self.p_d += self.d_incr
                            self.p_d = min(100,self.p_d)
                        elif btype == "shrink":
                            self.p_d -= self.d_incr
                            self.p_d = max(6,self.p_d)

                        
                        self.balls[i].collidingp = True


                    if btype == "wall bounce":
                        # if not(self.has_powerup) or self.wall_bounce:
                        self.wall_bounce = True
                        self.wall_bounce_timer = 0
                        self.has_powerup = True
                        self.inv = False
                        self.balls[i].collidingp = False

                    elif btype == "invincible":
                        # if not(self.has_powerup) or self.inv:
                        self.inv = True
                        self.inv_timer = 0
                        self.has_powerup = True
                        self.wall_bounce = False
                        self.balls[i].collidingp = False
                        


                    self.balls[i].colliding = True

                    self.bcol_timer = 0
                    self.bcollission = True

            else:
                self.balls[i].colliding = False
                self.balls[i].collidingp = False


        # spawn new ball
        if self.spawn_time >= self.spawn_wait:
            self.spawn_wait = random.choice(range(self.spawn_min, self.spawn_max+1))
            self.spawn_time = 0
            if len(self.balls) < self.max_balls:
                self.balls.append(self.create_ball())

        self.repaint()


    def resizeEvent(self, event):
        qr = self.geometry()
        self.w = qr.width()
        self.h = qr.height()

    def set_bg_color(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def custom_close(self):
        QCoreApplication.instance().quit()

    def eventFilter(self,source,event):

        # if self.m_x == 0 and self.m_y == 0:
        if not self.p_active:
            self.t0 = time()
            self.tr0 = time()

        p = False
        if event.type() == QEvent.KeyPress:
            modifiers = QApplication.keyboardModifiers()

            if event.key() == Qt.Key_Right:
                self.m_x = 1
                self.m_y = 0
                # p = True
            elif event.key() == Qt.Key_Left:
                self.m_x = -1
                self.m_y = 0
                # p = True
            elif event.key() == Qt.Key_Up:
                self.m_y = -1
                self.m_x = 0
                # p = True
            elif event.key() == Qt.Key_Down:
                self.m_y = 1
                self.m_x = 0
                # p = True
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                p = True

            if p and self.paused:
                self.reset_game()

        return 0


    def reset_game(self):
        self.balls = []
        self.init_balls()
        self.spawn_time = 0

        # reset player stuff
        self.p_speed = self.p_speed_def+0
        self.paused = False
        self.p_active = False
        self.dur = 0
        self.tr0 = time()
        self.p_x = self.w/2
        self.p_y = self.h/2
        self.p_d = self.p_d_def+0
        self.m_x = 0
        self.m_y = 0

        self.wall_bounce = False
        self.has_powerup = False


    def closeEvent(self, event):
        self.custom_close()



if __name__ == '__main__':

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ratball_gui_ctypes_thing")
    except:
        pass

    app = QApplication(sys.argv)
    # QApplication.setQuitOnLastWindowClosed(False)
    gui = RatBall()
    gui.show()
    app.exec_()
