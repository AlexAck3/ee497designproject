import socket
from time import sleep

SERVER_ADDRESS = "2C:CF:67:95:AC:52"     # This NEEDS to be the server pi's mac address
PORT = 1                # Must matcht the server, 1-30

# Bluethooth socket
conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

class Brandon_is_gui:
    def __init__(self):
        slider = QSlider(Qt.Orientation.Vertical, self)
    def send_slider_data(self):
        pass

try:
    if __name__ == "__main__":
        pass

        

except Exception as e:
    print(f"ERROR [Failed Connection]:\n{e}\n")

finally:
    conn.close()
    print("Sockets closed, shutting down...")