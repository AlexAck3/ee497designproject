import socket
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

SERVER_ADDRESS = "2C:CF:67:95:AC:52"     # This NEEDS to be the server pi's mac address
PORT = 1                # Must match the server, 1-30

# Bluetooth socket
conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

# ---------------------------------------------------------------- styling
BG = QColor("#0a0a0a")
PANEL = QColor("#141414")
TRACK = QColor("#1c1c1c")
TRACK_EDGE = QColor("#3a3a3a")
TICK = QColor("#4a4a4a")
TICK_MAJOR = QColor("#8a8a8a")
TEXT = QColor("#9a9a9a")
NEON_EQ = QColor("#00f0ff")      # EQ handles
NEON_VOL = QColor("#ffb000")     # volume handle

MARGIN = 20          # shared top/bottom margin so the dB scale lines up with the sliders
DB_MIN, DB_MAX = -15, 15

BANDS = ["80 Hz", "240 Hz", "750 Hz", "2.2 kHz", "6.6 kHz"]


class EQSlider(QWidget):
    """Custom painted vertical slider with ticks and a glowing handle."""
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum, maximum, default, color, bipolar=True, major_every=5, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.default = default
        self.color = color
        self.bipolar = bipolar
        self.major_every = major_every
        self._value = default
        self.setMinimumSize(60, 220)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ---- value handling
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
        self.setValue(self.default)      # double-click resets

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

        # ticks
        for v in range(self.minimum, self.maximum + 1):
            major = (v % self.major_every == 0)
            p.setPen(QPen(TICK_MAJOR if major else TICK, 1))
            y = self._val_to_y(v)
            L = 12 if major else 6
            p.drawLine(int(cx - 10 - L), int(y), int(cx - 10), int(y))
            p.drawLine(int(cx + 10), int(y), int(cx + 10 + L), int(y))

        # slot
        slot = QRectF(cx - 3, top, 6, bottom - top)
        p.setPen(QPen(TRACK_EDGE, 1))
        p.setBrush(QBrush(TRACK))
        p.drawRoundedRect(slot, 3, 3)

        # filled portion
        y_val = self._val_to_y(self._value)
        y_ref = self._val_to_y(0) if self.bipolar else bottom
        fill = QColor(self.color)
        fill.setAlpha(150)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill))
        p.drawRoundedRect(QRectF(cx - 2, min(y_val, y_ref), 4, abs(y_ref - y_val)), 2, 2)

        # handle glow
        hw, hh = 36, 16
        handle = QRectF(cx - hw / 2, y_val - hh / 2, hw, hh)
        for i in range(6, 0, -1):
            glow = QColor(self.color)
            glow.setAlpha(14 + (6 - i) * 4)
            p.setBrush(QBrush(glow))
            p.drawRoundedRect(handle.adjusted(-i * 1.5, -i * 1.5, i * 1.5, i * 1.5), 6 + i, 6 + i)

        # handle body
        p.setPen(QPen(self.color, 1.5))
        p.setBrush(QBrush(QColor("#1e1e1e")))
        p.drawRoundedRect(handle, 4, 4)
        p.setPen(QPen(self.color, 2))
        p.drawLine(int(handle.left() + 5), int(y_val), int(handle.right() - 5), int(y_val))


class DbScale(QWidget):
    """The dB markings on the left (-15 to +15)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(42)
        self.setMinimumHeight(220)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont("Monospace", 8))
        p.setPen(TEXT)
        top, bottom = MARGIN, self.height() - MARGIN
        for v in range(DB_MIN, DB_MAX + 1, 5):
            frac = (v - DB_MIN) / (DB_MAX - DB_MIN)
            y = bottom - frac * (bottom - top)
            label = f"{v:+d}" if v else "0"
            p.drawText(QRectF(0, y - 8, self.width() - 6, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        p.drawText(QRectF(0, 0, self.width() - 6, 14),
                   Qt.AlignmentFlag.AlignRight, "dB")


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Wireless EQ")
        self.resize(560, 420)
        self.setStyleSheet(
            "QWidget { background-color: #0a0a0a; color: #9a9a9a; font-family: Monospace; }"
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("WIRELESS  EQ")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00f0ff; font-size: 16px; font-weight: bold; letter-spacing: 4px;")
        main_layout.addWidget(title)

        row = QHBoxLayout()
        main_layout.addLayout(row, 1)
        row.addWidget(DbScale())

        # 5 EQ bands
        for i, name in enumerate(BANDS):
            slider = EQSlider(DB_MIN, DB_MAX, 0, NEON_EQ, bipolar=True, major_every=5)
            row.addLayout(self.make_column(slider, name, i, unit="dB"), 1)

        # divider between EQ and volume
        divider = QWidget()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #2a2a2a;")
        row.addWidget(divider)

        # volume (0-100)
        vol = EQSlider(0, 100, 50, NEON_VOL, bipolar=False, major_every=25)
        row.addLayout(self.make_column(vol, "VOL", 5, unit="%"), 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555555; font-size: 10px;")
        main_layout.addWidget(self.status_label)

        self.show()

    def make_column(self, slider, name, index, unit):
        col = QVBoxLayout()
        readout = QLabel(self.fmt(slider.value(), unit))
        readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        readout.setStyleSheet(f"color: {slider.color.name()}; font-size: 11px;")

        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #cfcfcf; font-size: 11px; font-weight: bold;")

        def on_change(value):
            readout.setText(self.fmt(value, unit))
            self.send_val(value, index)

        slider.valueChanged.connect(on_change)

        col.addWidget(readout)
        col.addWidget(slider, 1)
        col.addWidget(label)
        return col

    @staticmethod
    def fmt(value, unit):
        return f"{value:+d} dB" if unit == "dB" else f"{value}%"

    def send_val(self, value, slider_number):
        self.status_label.setText(f"Current slider: {slider_number}   Value: {value}")
        msg = f"{slider_number},{value}\n"
        try:
            conn.send(msg.encode('ascii'))
            data = conn.recv(1024)
            if not data:
                print("no connection")
                return
            print(f"received message \n{data.decode('ascii')}")
        except OSError as e:
            self.status_label.setText(f"Send failed: {e}")


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