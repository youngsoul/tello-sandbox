import cv2
from djitellopy import Tello
import time

tello = Tello()
tello.connect()
time.sleep(2)

tello.streamon()

frame_read = tello.get_frame_read()

tello.takeoff()

print("I will take a picture in 2 seconds")
time.sleep(1)
print("I will take a picture in 1 seconds")
time.sleep(1)

cv2.imwrite("tello-picture.png", frame_read.frame)

tello.land()

tello.streamoff()
