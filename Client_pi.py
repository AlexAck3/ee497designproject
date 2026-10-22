import socket
from time import sleep
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QSlider, QLabel, QFormLayout
from PyQt6.QtCore import Qt

SERVER_ADDRESS = "2C:CF:67:95:AC:52"     # This NEEDS to be the server pi's mac address
PORT = 1                # Must matcht the server, 1-30

# Bluethooth socket
conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('PyQt QSlider')
        self.setMinimumWidth(200)

        # create a grid layout
        layout = QFormLayout()
        self.setLayout(layout)

        slider = QSlider(Qt.Orientation.Vertical, self)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setSingleStep(5)
        slider.setPageStep(10)
        slider.setTickPosition(QSlider.TickPosition.TicksAbove)

        slider.valueChanged.connect(self.update)

        self.result_label = QLabel('', self)

        layout.addRow(slider)
        layout.addRow(self.result_label)

        # show the window
        self.show()

    def update(self, value):
        self.result_label.setText(f'Current Value: {value}')

try:
    if __name__ == '__main__':
        app = QApplication(sys.argv)
        window = MainWindow()
        sys.exit(app.exec()) 

        

except Exception as e:
    print(f"ERROR [Failed Connection]:\n{e}\n")

finally:
    conn.close()
    print("Sockets closed, shutting down...")