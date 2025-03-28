import sys
import random
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QRadialGradient
from pynput.mouse import Controller
from pynput import keyboard
from threading import Thread
from queue import Queue

# Queue to store mouse positions
mouse_positions = Queue()

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.streaks = []
        self.mouse_controller = Controller()
        self.current_target = None
        self.last_mouse_position = None
        

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WA_TransparentForMouseEvents |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Set the window to cover the entire screen
        geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(geometry)
        
        # Timer to update the display
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        
        # Timer for random mouse movement
        self.movement_timer = QTimer()
        self.movement_timer.timeout.connect(self.randomly_move_mouse)
        self.set_random_movement_timer()

        # Timer for checking mouse stillness and triggering paint explosion
        self.stillness_timer = QTimer()
        self.stillness_timer.timeout.connect(self.check_mouse_stillness)
        self.stillness_timer.start(1000)  # Check every second

    def add_streak(self, pos):
        self.streaks.append({'pos': pos, 'age': 0})

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Update streak ages and remove old ones
        self.streaks = [streak for streak in self.streaks if streak['age'] < 60]
        for streak in self.streaks:
            streak['age'] += 1
            opacity = max(0, 1 - streak['age'] / 60)
            gradient = QRadialGradient(QPoint(streak['pos'][0], streak['pos'][1]), 300)
            gradient.setColorAt(0, QColor(0, 0, 0, int(255 * opacity)))
            gradient.setColorAt(1, QColor(0, 0, 0, int(100 * opacity)))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(streak['pos'][0], streak['pos'][1]), 200, 200)
        painter.end()

    def update_streaks(self):
        while not mouse_positions.empty():
            if random.random() < 0.3:
                self.add_streak(mouse_positions.get())

    def set_random_movement_timer(self):
        self.movement_timer.start(random.randint(15000, 30000))

    def randomly_move_mouse(self):
        geometry = QApplication.primaryScreen().geometry()
        current_x, current_y = self.mouse_controller.position
        if current_x < geometry.width() / 2:
            target_x = geometry.width() - 1
        else:
            target_x = 0
        if current_y < geometry.height() / 2:
            target_y = geometry.height() - 1
        else:
            target_y = 0
        self.current_target = (target_x, target_y)
        self.drag_mouse_to_target()
        self.set_random_movement_timer()

    def drag_mouse_to_target(self):
        if not self.current_target:
            return

        target_x, target_y = self.current_target
        current_x, current_y = self.mouse_controller.position
        steps = 80  # Increased number of steps for smoother dragging
        delay = 0.05  # Set a fixed delay for dragging
        delta_x = (target_x - current_x) / steps
        delta_y = (target_y - current_y) / steps

        for step in range(steps):
            current_x += delta_x
            current_y += delta_y
            self.mouse_controller.position = (int(current_x), int(current_y))
            QApplication.processEvents()
            time.sleep(delay)
            if self.current_target:
                target_x, target_y = self.current_target
                delta_x = (target_x - current_x) / (steps - step)
                delta_y = (target_y - current_y) / (steps - step)

            self.mouse_controller.position = (int(current_x), int(current_y))

    def check_mouse_stillness(self):
        current_position = self.mouse_controller.position
        if current_position == self.last_mouse_position:
            self.mouse_still_time += 1
        else:
            self.mouse_still_time = 0
        
        self.last_mouse_position = current_position
        
        if self.mouse_still_time >= 5:  # Mouse has been still for 5 seconds
            self.quick_paint_explosion()
            self.mouse_still_time = 5  # Keep triggering every 5 seconds if still
            self.mouse_still_time = 0

    def quick_paint_explosion(self):
        geometry = QApplication.primaryScreen().geometry()
        for _ in range(200):
            random_x = random.randint(0, geometry.width() - 1)
            random_y = random.randint(0, geometry.height() - 1)
            self.add_streak((random_x, random_y))

# Mouse listener to track mouse movement
def start_mouse_listener():
    from pynput import mouse
    def on_move(x, y):
        mouse_positions.put((x, y))
    with mouse.Listener(on_move=on_move) as listener:
        listener.join()

mouse_thread = Thread(target=start_mouse_listener, daemon=True)
mouse_thread.start()


def main():
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    streak_timer = QTimer()
    streak_timer.timeout.connect(overlay.update_streaks)
    streak_timer.start(50)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
