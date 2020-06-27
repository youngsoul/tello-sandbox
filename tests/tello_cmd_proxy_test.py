import socket

def send(message):
  try:
    sock.sendto(message.encode(), tello_address)
    print("Sending message: " + message)
  except Exception as e:
    print("Error sending: " + str(e))

# Function that listens for messages from Tello and prints them to the screen
def receive():
  try:
    response, ip_address = sock.recvfrom(128)
    print("Received message: " + response.decode(encoding='utf-8') + " from Tello with IP: " + str(ip_address))
  except Exception as e:
    print("Error receiving: " + str(e))

if __name__ == '__main__':

    tello_address = ("192.168.1.208", 8888)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Let's be explicit and bind to a local port on our machine where Tello can send messages
    sock.bind(('', 9000))

    message = "command"

    send(message)
    print("message sent")

    receive()

    # Ask Tello about battery status
    send("battery?")

    # Receive battery response from Tello
    receive()

    send("takeoff")
    receive()

    send("land")
    receive()

    send("speed?")
    receive()

    send("time?")
    receive()

    send("wifi?")
    receive()
    send("sdk?")
    receive()
    # Close the UDP socket
    sock.close()