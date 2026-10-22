import socket
from time import sleep
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QSlider, QHBoxLayout, QLabel, QVBoxLayout
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
        self.resize(400,300)

        # create a grid layout
        # main layout: sliders row on top, label below
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # horizontal layout for side-by-side sliders
        slider_layout = QHBoxLayout()
        main_layout.addLayout(slider_layout)


        slider_low = QSlider(Qt.Orientation.Vertical, self)
        slider_low_mid = QSlider(Qt.Orientation.Vertical, self)
        slider_mid = QSlider(Qt.Orientation.Vertical, self)
        slider_high_mid = QSlider(Qt.Orientation.Vertical, self)
        slider_high = QSlider(Qt.Orientation.Vertical, self)

        # Initialize Sliders
        self.slider_init(slider_low, slider_layout,0 )
        self.slider_init(slider_low_mid, slider_layout, 1)
        self.slider_init(slider_mid, slider_layout, 2)
        self.slider_init(slider_high_mid, slider_layout, 3)
        self.slider_init(slider_high, slider_layout, 4)
        

        self.result_label = QLabel('', self)
        main_layout.addWidget(self.result_label)
        
        # show the window
        self.show()

    def update(self, value, slider_number):
        self.result_label.setText(f'Current slider: {slider_number} current Value: {value}')
        

    def slider_init(self, slider: QSlider, slider_layout: QHBoxLayout, i):
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setSingleStep(5)
        slider.setPageStep(10)
        slider.setTickPosition(QSlider.TickPosition.TicksAbove)

        slider.valueChanged.connect(lambda value: self.update(value, i)) # .setText(f'Slider {n + 1}: {value}')
        slider_layout.addWidget(slider)
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