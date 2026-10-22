import socket

SERVER_ADDRESS = "2C:CF:67:95:AC:52"     # Keep empty -> allows listening to all devices
PORT = 1                # 1-30 are available

# Bluethooth socket
s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

try:
    s.bind((SERVER_ADDRESS, PORT))
    s.listen(1)
    print(f"Finding BT Device on port {PORT}...")

    # Waits till connection is established
    conn, conn_info = s.accept()
    print("Connection established! \n")
    print("-----------------------------------------\n")
    print(f"{conn_info}\n")
    print("-----------------------------------------\n")

    while True:
        data = conn.recv(1024)
        if not data:
            print(f"Connection Terminated from {conn_info}")
            break

        msg = data.decode("ascii")
        print(f"Recieved MSG:\n{msg}")

        fb = "ACK"
        conn.send(fb.encode("ascii"))

except Exception as e:
    print(f"ERROR:\n{e}\n")

finally:
    if 'conn' in locals():
        conn.close()
    s.close
    print("Sockets closed, shutting down...")