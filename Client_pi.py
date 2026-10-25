import socket
import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QTimer
from PyQt6.QtGui import (QPainter, QColor, QPen, QFont, QBrush,
                         QLinearGradient, QRadialGradient)

SERVER_ADDRESS = "2C:CF:67:95:AC:52"     # This NEEDS to be the server pi's mac address
PORT = 1                # Must match the server, 1-30

# Bluetooth socket
conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

# ---------------------------------------------------------------- styling
MARGIN = 20                  # shared top/bottom margin so the dB scale lines up with the faders
ROW_H = 18                   # height of the readout / name rows above and below each fader
DB_MIN, DB_MAX = -15, 15
BANDS = ["80 Hz", "240 Hz", "750 Hz", "2.2 kHz", "6.6 kHz"]

TICK_MINOR = QColor("#6a6a6a")
TICK_MAJOR = QColor("#d8d8d8")
LABEL = "#e4e4e4"
ORANGE = "#d9541e"


def led_color(frac):
    """Classic green -> yellow -> orange -> red LED ladder."""
    if frac < 0.55:
        return QColor("#31e04a")
    if frac < 0.75:
        return QColor("#d8e640")
    if frac < 0.90:
        return QColor("#ff9a1f")
    return QColor("#ff3a2a")


class Lamp(QWidget):
    """Small round indicator LED."""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.on = False
        self.setFixedSize(16, 16)

    def set_on(self, on):
        self.on = on
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QPointF(8, 8)
        p.setPen(Qt.PenStyle.NoPen)
        if self.on:
            for r, a in ((8, 40), (6.5, 80)):
                g = QColor(self.color)
                g.setAlpha(a)
                p.setBrush(QBrush(g))
                p.drawEllipse(c, r, r)
            p.setBrush(QBrush(self.color))
        else:
            p.setBrush(QBrush(self.color.darker(500)))
        p.drawEllipse(c, 4.5, 4.5)
        p.setPen(QPen(QColor("#000000"), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(c, 4.5, 4.5)


class Fader(QWidget):
    """EQ fader: tick marks, LED segment ladder, and a gray cap with a red stripe."""
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum, maximum, default, major_every=5, segments=24, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.default = default
        self.major_every = major_every
        self.segments = segments
        self._value = default
        self.setMinimumSize(58, 220)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def value(self):
        return self._value

    def setValue(self, v):
        v = max(self.minimum, min(self.maximum, int(round(v))))
        if v != self._value:
            self._value = v
            self.update()
            self.valueChanged.emit(v)

    def _val_to_y(self, v):
        top, bottom = MARGIN, self.height() - MARGIN
        frac = (v - self.minimum) / (self.maximum - self.minimum)
        return bottom - frac * (bottom - top)

    def _y_to_val(self, y):
        top, bottom = MARGIN, self.height() - MARGIN
        frac = (bottom - y) / (bottom - top)
        return self.minimum + frac * (self.maximum - self.minimum)

    # ---- input
    def mousePressEvent(self, e):
        self.setValue(self._y_to_val(e.position().y()))

    def mouseMoveEvent(self, e):
        self.setValue(self._y_to_val(e.position().y()))

    def mouseDoubleClickEvent(self, e):
        self.setValue(self.default)

    def wheelEvent(self, e):
        self.setValue(self._value + (1 if e.angleDelta().y() > 0 else -1))

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Up, Qt.Key.Key_Right):
            self.setValue(self._value + 1)
        elif e.key() in (Qt.Key.Key_Down, Qt.Key.Key_Left):
            self.setValue(self._value - 1)

    # ---- drawing
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() / 2
        top, bottom = MARGIN, self.height() - MARGIN
        span = bottom - top

        # tick marks either side of the LED ladder
        for v in range(self.minimum, self.maximum + 1):
            major = (v % self.major_every == 0)
            p.setPen(QPen(TICK_MAJOR if major else TICK_MINOR, 1))
            y = self._val_to_y(v)
            length = 9 if major else 4
            p.drawLine(QPointF(cx - 12 - length, y), QPointF(cx - 12, y))
            p.drawLine(QPointF(cx + 12, y), QPointF(cx + 12 + length, y))

        # dark slot behind everything
        p.setPen(QPen(QColor("#2a2a2a"), 1))
        p.setBrush(QBrush(QColor("#030303")))
        p.drawRect(QRectF(cx - 9, top - 3, 18, span + 6))

        # LED segments, lit from the bottom up to the cap
        n = self.segments
        seg_h = span / n
        p.setPen(Qt.PenStyle.NoPen)
        for k in range(n):
            frac = (k + 0.5) / n
            seg_val = self.minimum + frac * (self.maximum - self.minimum)
            y_top = bottom - (k + 1) * seg_h
            rect = QRectF(cx - 7, y_top + 1, 14, seg_h - 2)
            c = led_color(frac)
            if seg_val <= self._value:
                glow = QColor(c)
                glow.setAlpha(45)
                p.setBrush(QBrush(glow))
                p.drawRect(rect.adjusted(-2, -1, 2, 1))
                p.setBrush(QBrush(c))
            else:
                p.setBrush(QBrush(c.darker(600)))
            p.drawRect(rect)

        # fader cap
        y = self._val_to_y(self._value)
        cap = QRectF(cx - 15, y - 6, 30, 12)
        grad = QLinearGradient(0, y - 6, 0, y + 6)
        grad.setColorAt(0.0, QColor("#c4c4c4"))
        grad.setColorAt(0.5, QColor("#707070"))
        grad.setColorAt(1.0, QColor("#2c2c2c"))
        p.setPen(QPen(QColor("#050505"), 1.2))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(cap, 1.5, 1.5)
        glow = QColor("#ff3b30")
        glow.setAlpha(70)
        p.setPen(QPen(glow, 5))
        p.drawLine(QPointF(cap.left() + 3, y), QPointF(cap.right() - 3, y))
        p.setPen(QPen(QColor("#ff3b30"), 2))
        p.drawLine(QPointF(cap.left() + 3, y), QPointF(cap.right() - 3, y))


class Knob(QWidget):
    """Rotary LEVEL knob. Drag up/down, scroll, or double-click to reset."""
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum, maximum, default, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.default = default
        self._value = default
        self._drag_y = 0
        self._drag_v = 0
        self.setMinimumSize(86, 86)
        self.setCursor(Qt.CursorShape.SizeVerCursor)

    def value(self):
        return self._value

    def setValue(self, v):
        v = max(self.minimum, min(self.maximum, int(round(v))))
        if v != self._value:
            self._value = v
            self.update()
            self.valueChanged.emit(v)

    def mousePressEvent(self, e):
        self._drag_y = e.position().y()
        self._drag_v = self._value

    def mouseMoveEvent(self, e):
        self.setValue(self._drag_v + (self._drag_y - e.position().y()) * 0.5)

    def mouseDoubleClickEvent(self, e):
        self.setValue(self.default)

    def wheelEvent(self, e):
        self.setValue(self._value + (2 if e.angleDelta().y() > 0 else -2))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        r = min(self.width(), self.height()) / 2 - 16
        frac = (self._value - self.minimum) / (self.maximum - self.minimum)

        # scale dots, 270 degree sweep
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(11):
            f = i / 10
            a = math.radians(225 - f * 270)
            pos = QPointF(cx + (r + 10) * math.cos(a), cy - (r + 10) * math.sin(a))
            p.setBrush(QBrush(QColor("#e4e4e4") if f <= frac + 1e-6 else QColor("#4a4a4a")))
            p.drawEllipse(pos, 1.8, 1.8)

        # knob body
        grad = QRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 1.3)
        grad.setColorAt(0.0, QColor("#4c4c4c"))
        grad.setColorAt(1.0, QColor("#0b0b0b"))
        p.setPen(QPen(QColor("#707070"), 1.2))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # indicator
        a = math.radians(225 - frac * 270)
        p.setPen(QPen(QColor("#ffffff"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(cx + 0.35 * r * math.cos(a), cy - 0.35 * r * math.sin(a)),
                   QPointF(cx + 0.88 * r * math.cos(a), cy - 0.88 * r * math.sin(a)))


class DbScale(QWidget):
    """dB markings (-15 to +15) on the left, aligned to the faders."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(40)
        self.setMinimumHeight(220)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont("Monospace", 8))
        p.setPen(QColor("#b8b8b8"))
        top, bottom = MARGIN, self.height() - MARGIN
        for v in range(DB_MIN, DB_MAX + 1, 5):
            frac = (v - DB_MIN) / (DB_MAX - DB_MIN)
            y = bottom - frac * (bottom - top)
            label = f"{v:+d}" if v else "0"
            p.drawText(QRectF(0, y - 8, self.width() - 6, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        p.drawText(QRectF(0, 0, self.width() - 6, 14), Qt.AlignmentFlag.AlignRight, "dB")


class Faceplate(QWidget):
    """Black rack panel with screws."""
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#232323"))
        grad.setColorAt(0.08, QColor("#141414"))
        grad.setColorAt(1.0, QColor("#070707"))
        p.setPen(QPen(QColor("#3a3a3a"), 1.5))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(rect, 6, 6)

        for pos in (QPointF(16, 16), QPointF(self.width() - 16, 16),
                    QPointF(16, self.height() - 16), QPointF(self.width() - 16, self.height() - 16)):
            sg = QRadialGradient(pos.x() - 2, pos.y() - 2, 9)
            sg.setColorAt(0.0, QColor("#bdbdbd"))
            sg.setColorAt(1.0, QColor("#3a3a3a"))
            p.setPen(QPen(QColor("#000000"), 1))
            p.setBrush(QBrush(sg))
            p.drawEllipse(pos, 6, 6)
            p.setPen(QPen(QColor("#222222"), 1.5))
            p.drawLine(QPointF(pos.x() - 4, pos.y()), QPointF(pos.x() + 4, pos.y()))


def text_label(text, size=10, color=LABEL, bold=True, mono=False):
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedHeight(ROW_H)
    family = "Monospace" if mono else "Helvetica, Arial, sans-serif"
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(f"background: transparent; color: {color}; font-family: {family}; "
                      f"font-size: {size}px; font-weight: {weight};")
    return lbl


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Wireless EQ")
        self.resize(780, 470)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)

        plate = Faceplate()
        outer.addWidget(plate)
        main = QVBoxLayout(plate)
        main.setContentsMargins(34, 22, 34, 18)

        # ---- header: power LED, badge, link / tx lamps
        header = QHBoxLayout()
        main.addLayout(header)

        power_col = QVBoxLayout()
        self.power_lamp = Lamp("#ff2a2a")
        self.power_lamp.set_on(True)
        power_col.addWidget(self.power_lamp, alignment=Qt.AlignmentFlag.AlignHCenter)
        power_col.addWidget(text_label("POWER", 8))
        header.addLayout(power_col)

        header.addStretch(1)

        link_col = QVBoxLayout()
        self.link_lamp = Lamp("#31e04a")
        self.link_lamp.set_on(True)
        link_col.addWidget(self.link_lamp, alignment=Qt.AlignmentFlag.AlignHCenter)
        link_col.addWidget(text_label("LINK", 8))
        header.addLayout(link_col)

        tx_col = QVBoxLayout()
        self.tx_lamp = Lamp("#ff3a2a")
        tx_col.addWidget(self.tx_lamp, alignment=Qt.AlignmentFlag.AlignHCenter)
        tx_col.addWidget(text_label("TX", 8))
        header.addLayout(tx_col)

        # ---- sliders row
        row = QHBoxLayout()
        main.addLayout(row, 1)

        scale_col = QVBoxLayout()
        scale_col.addWidget(text_label(""))
        scale_col.addWidget(DbScale(), 1)
        scale_col.addWidget(text_label(""))
        row.addLayout(scale_col)

        for i, name in enumerate(BANDS):
            fader = Fader(DB_MIN, DB_MAX, 0)
            row.addLayout(self.make_column(fader, name, i, "dB"), 1)

        divider = QWidget()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #2c2c2c;")
        row.addWidget(divider)

        knob = Knob(0, 100, 50)
        row.addLayout(self.make_column(knob, "LEVEL", 5, "%"), 1)

        # ---- status line
        self.status_label = text_label("", 10, "#6a6a6a", bold=False, mono=True)
        main.addWidget(self.status_label)

        self.show()

    def make_column(self, control, name, index, unit):
        col = QVBoxLayout()
        readout = text_label(self.fmt(control.value(), unit), 10, "#ffffff", mono=True)

        def on_change(value):
            readout.setText(self.fmt(value, unit))
            self.send_val(value, index)

        control.valueChanged.connect(on_change)
        col.addWidget(readout)
        col.addWidget(control, 1)
        col.addWidget(text_label(name, 10))
        return col

    @staticmethod
    def fmt(value, unit):
        return f"{value:+d} dB" if unit == "dB" else f"{value}%"

    def send_val(self, value, slider_number):
        self.status_label.setText(f"Current slider: {slider_number}   Value: {value}")
        self.tx_lamp.set_on(True)
        self.tx_lamp.repaint()
        if slider_number != 5:      # IF the slider is not the volume knob
            value = int(round((value+15)/30, 2)*100)
            if value < 0:
                value = 0
        msg = f"{slider_number},{value}\n"
        try:
            conn.send(msg.encode('ascii'))
            data = conn.recv(1024)
            if not data:
                print("no connection")
                self.link_lamp.set_on(False)
            else:
                print(f"received message \n{data.decode('ascii')}")
        except OSError as e:
            self.link_lamp.set_on(False)
            self.status_label.setText(f"Send failed: {e}")
        QTimer.singleShot(120, lambda: self.tx_lamp.set_on(False))

    def paintEvent(self, _):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#1c130f"))
        grad.setColorAt(1.0, QColor("#2a1a10"))
        p.fillRect(self.rect(), QBrush(grad))


try:
    if __name__ == '__main__':
        conn.connect((SERVER_ADDRESS, PORT))
        app = QApplication(sys.argv)
        window = MainWindow()
        sys.exit(app.exec())

except Exception as e:
    print(f"ERROR [Failed Connection]:\n{e}\n")

finally:
    conn.close()
    print("Sockets closed, shutting down...")