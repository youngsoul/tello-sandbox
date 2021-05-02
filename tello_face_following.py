from pyimagesearch.objcenter import ObjCenter
import cv2
from pyimagesearch.pid import PID
from djitellopy import Tello
import signal
import sys
import imutils
import time
from datetime import datetime
from multiprocessing import Manager, Process, Pipe, Event, Queue

pan_pid = None
tilt_pid = None
face_center = None
max_speed_threshold = 40

def init(tello, fly=False, max_speed=40):
    global pan_pid, tilt_pid, face_center, max_speed_threshold
    max_speed_threshold = max_speed
    face_center = ObjCenter("./haarcascade_frontalface_default.xml")
    pan_pid = PID(kP=0.7, kI=0.0001, kD=0.1)
    tilt_pid = PID(kP=0.7, kI=0.0001, kD=0.1)
    pan_pid.initialize()
    tilt_pid.initialize()

    if fly:
        tello.takeoff()
        tello.move_up(70)




def handler(tello, frame, track_face, fly):

    frame = imutils.resize(frame, width=400)
    H, W, _ = frame.shape

    # calculate the center of the frame as this is (ideally) where
    # we will we wish to keep the object
    centerX = W // 2
    centerY = H // 2

    # draw a circle in the center of the frame
    cv2.circle(frame, center=(centerX, centerY), radius=5, color=(0, 0, 255), thickness=-1)

    # find the object's location
    frame_center = (centerX, centerY)
    objectLoc = face_center.update(frame, frameCenter=None)
    # print(centerX, centerY, objectLoc)

    ((objX, objY), rect, d) = objectLoc
    if d > 25 or d == -1:
        # then either we got a false face, or we have no faces.
        # the d - distance - value is used to keep the jitter down of false positive faces detected where there
        #                   were none.
        # if it is a false positive, or we cannot determine a distance, just stay put
        # print(int(pan_update), int(tilt_update))
        if track_face and fly:
            tello.send_rc_control(0, 0, 0, 0)
            return

    if rect is not None:
        (x, y, w, h) = rect
        cv2.rectangle(frame, (x, y), (x + w, y + h),
                      (0, 255, 0), 2)

        # draw a circle in the center of the face
        cv2.circle(frame, center=(objX, objY), radius=5, color=(255, 0, 0), thickness=-1)

        # Draw line from frameCenter to face center
        cv2.arrowedLine(frame, frame_center, (objX, objY), color=(0, 255, 0), thickness=2)

        # calculate the pan and tilt errors and run through pid controllers
        pan_error = centerX - objX
        pan_update = pan_pid.update(pan_error, sleep=0)

        tilt_error = centerY - objY
        tilt_update = tilt_pid.update(tilt_error, sleep=0)

        # print(pan_error, int(pan_update), tilt_error, int(tilt_update))
        cv2.putText(frame, f"X Error: {pan_error} PID: {pan_update:.2f}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2, cv2.LINE_AA)

        cv2.putText(frame, f"Y Error: {tilt_error} PID: {tilt_update:.2f}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255), 2, cv2.LINE_AA)

        if pan_update > max_speed_threshold:
            pan_update = max_speed_threshold
        elif pan_update < -max_speed_threshold:
            pan_update = -max_speed_threshold

        # NOTE: if face is to the right of the drone, the distance will be negative, but
        # the drone has to have positive power so I am flipping the sign
        pan_update = pan_update * -1

        if tilt_update > max_speed_threshold:
            tilt_update = max_speed_threshold
        elif tilt_update < -max_speed_threshold:
            tilt_update = -max_speed_threshold

        # print(int(pan_update), int(tilt_update))
        if track_face and fly:
            # left/right: -100/100
            tello.send_rc_control(pan_update // 3, 0, tilt_update // 2, 0)
        elif fly:
            # then we are not tracking the face, but we are flying
            # so send tello a command of 'stay where you are' but this
            # will keep the tello flying.  otherwise after a timeout
            # of no commands it lands
            tello.send_rc_control(0, 0, 0, 0)


    return
