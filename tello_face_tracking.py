from pyimagesearch.objcenter import ObjCenter
import cv2
from pyimagesearch.pid import PID
from djitellopy import Tello
import signal
import sys
import imutils
from threading import Thread
import time
from datetime import datetime


tello = Tello()
run_pid = True
track_face = True  # True - cause the Tello to start to track/follow a face

max_speed_threshold = 40

video = None

# function to handle keyboard interrupt
def signal_handler(sig, frame):
    print("Signal Handler")
    tello.streamoff()
    tello.land()
    if video:
        video.release()

    sys.exit()


def track_face_in_video_feed():
    global video
    face_center = ObjCenter("./haarcascade_frontalface_default.xml")
    pan_pid = PID(kP=0.7, kI=0.0001, kD=0.09)
    tilt_pid = PID(kP=0.7, kI=0.0001, kD=0.09)
    pan_pid.initialize()
    tilt_pid.initialize()


    while True:
        frame = frame_read.frame

        frame = imutils.resize(frame, width=400)
        H, W, _ = frame.shape

        if video is None:
            video_file = f"video_{datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.avi"

            video = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'XVID'), 30, (W, H))

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
        if d > 50:
            # print(f"SKIP SAMPLE: {d}")
            continue  # ignore the sample as it is too far from the previous sample
            # trying to reduce gitter

        if rect is not None:
            (x, y, w, h) = rect
            cv2.rectangle(frame, (x, y), (x + w, y + h),
                          (0, 255, 0), 2)

            # draw a circle in the center of the face
            cv2.circle(frame, center=(objX, objY), radius=5, color=(255, 0, 0), thickness=-1)

            # Draw line from frameCenter to face center
            cv2.arrowedLine(frame, frame_center, (objX, objY), color=(0, 255, 0), thickness=2)

            if run_pid:
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

                if tilt_update > max_speed_threshold:
                    tilt_update = max_speed_threshold
                elif tilt_update < -max_speed_threshold:
                    tilt_update = -max_speed_threshold

                # print(int(pan_update), int(tilt_update))
                if track_face:
                    tello.send_rc_control(0, 0, tilt_update//2, 0)
        video.write(frame)
        time.sleep(1 / 30)


        # display the frame to the screen
        # cv2.imshow("Face Tracking", frame)
        # cv2.waitKey(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    tello.connect()

    tello.streamon()
    frame_read = tello.get_frame_read()

    face_thread = Thread(target=track_face_in_video_feed)
    face_thread.start()
    time.sleep(1)

    tello.takeoff()
    tello.move_up(70)

    cmd = input("Press q to land: ")
    if cmd == 'q':
        tello.land()
        tello.streamoff()
