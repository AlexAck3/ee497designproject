import socket
from time import sleep

SERVER_ADDRESS = "2C:CF:67:95:AC:52"     # This NEEDS to be the server pi's mac address
PORT = 1                # Must matcht the server, 1-30

# Bluethooth socket
conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

try:
    print(f"Finding MAC Address {SERVER_ADDRESS} on port {PORT}...")
    conn.connect((SERVER_ADDRESS, PORT))
    print(f"Connection Success!!!")

    # Sends dummy data for now
    while True:
        msg = "Test Passed!"
        conn.send(msg.encode("ascii"))

        data = conn.recv(1024)
        if not data:
            print(f"Connection Terminated from {SERVER_ADDRESS}")
            break
        
        msg = data.decode("ascii")
        print(f"Recieved MSG:\n{msg}")

        sleep(2)        # Wait a couple seconds
        

except Exception as e:
    print(f"ERROR [Failed Connection]:\n{e}\n")

finally:
    conn.close()
    print("Sockets closed, shutting down...")