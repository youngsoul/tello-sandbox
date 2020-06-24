"""
This script will use opencv to show the video feed from the tello
"""
import cv2
from djitellopy import Tello
import signal
import sys
import imutils

tello = None

# function to handle keyboard interrupt
def signal_handler(sig, frame):
    print("Signal Handler")
    if tello:
        try:
            tello.streamoff()
            tello.land()
        except:
            pass

    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    tello = Tello()

    tello.connect()

    tello.streamon()
    frame_read = tello.get_frame_read()

    while True:
        frame = frame_read.frame
        # print(frame.shape) # 720, 960, 3
        frame = imutils.resize(frame, width=400)
        # display the frame to the screen
        cv2.imshow("Drone Face Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

signal_handler(None, None)