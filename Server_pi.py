import sys
import reapy
from reapy import reascript_api as RPR
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtBluetooth import QBluetoothServer, QBluetoothServiceInfo, QBluetoothAddress, QBluetoothUuid

SERVER_ADDRESS = "2C:CF:67:95:AC:7A"     # Keep empty -> allows listening to all devices
PORT = 1                # 1-30 are available
SERVICE_UUID = "6c1d4f3a-8b2e-4f7d-9a35-2e5b7c0d1a94"   # Must match the client


class BTServer:
    def __init__(self, app):
        self.app = app
        self.conn = None
        self.conn_info = None
        self.track = None
        self.closing = False
        self.service_info = QBluetoothServiceInfo()

        # Bluethooth socket
        self.server = QBluetoothServer(QBluetoothServiceInfo.Protocol.RfcommProtocol)
        self.server.newConnection.connect(self.on_new_connection)

    def start(self):
        # listen() with a UUID creates, registers and advertises the service in one step
        # (the channel is assigned automatically, so PORT is no longer used here)
        self.service_info = self.server.listen(QBluetoothUuid(SERVICE_UUID), "Wireless EQ")
        if not self.service_info.isRegistered():
            raise RuntimeError("Failed to register Bluetooth service")
        print(f"Finding BT Device on port {self.server.serverPort()}...")

    # Called when a connection is established
    def on_new_connection(self):
        try:
            self.conn = self.server.nextPendingConnection()
            self.conn_info = (self.conn.peerAddress().toString(), PORT)
            self.server.close()  # single connection only, like listen(1)

            self.conn.readyRead.connect(self.on_ready_read)
            self.conn.disconnected.connect(self.on_disconnected)

            print("Connection established! \n")
            print("-----------------------------------------\n")
            print(f"{self.conn_info}\n")
            print("-----------------------------------------\n")

            project = reapy.Project()
            self.track = project.tracks[0]
        except Exception as e:
            print(f"ERROR:\n{e}\n")
            self.shutdown()

    # Called whenever data arrives
    def on_ready_read(self):
        try:
            data = bytes(self.conn.readAll())
            if not data:
                return

            msg = data.decode("ascii")
            print(f"Recieved MSG:\n{msg}")

            band = int(msg.split(",")[0])
            raw_gain= float(msg.split(",")[1])
            gain = ((raw_gain / 100) * 24) - 12

            result = RPR.TrackFX_SetEQParam(self.track.id, 0, 2, band, 1, gain, False)
            print(f"EQ Output: {result}")

            fb = "ACK"
            self.conn.write(fb.encode("ascii"))
        except Exception as e:
            print(f"ERROR:\n{e}\n")
            self.shutdown()

    # Called when the client disconnects
    def on_disconnected(self):
        if not self.closing:
            print(f"Connection Terminated from {self.conn_info}")
        self.shutdown()

    def shutdown(self):
        if self.closing:
            return
        self.closing = True
        if self.conn is not None:
            self.conn.close()
        self.service_info.unregisterService()
        self.server.close()
        print("Sockets closed, shutting down...")
        self.app.quit()


app = QCoreApplication(sys.argv)
server = BTServer(app)

try:
    server.start()
except Exception as e:
    print(f"ERROR:\n{e}\n")
    server.shutdown()
    sys.exit(1)

sys.exit(app.exec())