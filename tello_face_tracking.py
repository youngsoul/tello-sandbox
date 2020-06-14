from pyimagesearch.objcenter import ObjCenter
import cv2
from pyimagesearch.pid import PID
from djitellopy import Tello
import signal
import sys
import imutils
import time
from datetime import datetime
from multiprocessing import Manager, Process, Pipe, Event

tello = None
video_writer = None


# function to handle keyboard interrupt
def signal_handler(sig, frame):
    print("Signal Handler")
    if tello:
        try:
            tello.streamoff()
            tello.land()
        except:
            pass

    if video_writer:
        try:
            video_writer.release()
        except:
            pass

    sys.exit()


def track_face_in_video_feed(exit_event, show_video_conn, video_writer_conn, run_pid, track_face, fly=False,
                             max_speed_limit=40):
    """

    :param exit_event: Multiprocessing Event.  When set, this event indicates that the process should stop.
    :type exit_event:
    :param show_video_conn: Pipe to send video frames to the process that will show the video
    :type show_video_conn: multiprocessing Pipe
    :param video_writer_conn: Pipe to send video frames to the process that will save the video frames
    :type video_writer_conn: multiprocessing Pipe
    :param run_pid: Flag to indicate whether the PID controllers should be run.
    :type run_pid: bool
    :param track_face: Flag to indicate whether face tracking should be used to move the drone
    :type track_face: bool
    :param fly: Flag used to indicate whether the drone should fly.  False is useful when you just want see the video stream.
    :type fly: bool
    :param max_speed_limit: Maximum speed that the drone will send as a command.
    :type max_speed_limit: int
    :return: None
    :rtype:
    """
    global tello
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    max_speed_threshold = max_speed_limit

    tello = Tello()

    tello.connect()

    tello.streamon()
    frame_read = tello.get_frame_read()

    if fly:
        tello.takeoff()
        tello.move_up(70)

    face_center = ObjCenter("./haarcascade_frontalface_default.xml")
    pan_pid = PID(kP=0.7, kI=0.0001, kD=0.1)
    tilt_pid = PID(kP=0.7, kI=0.0001, kD=0.1)
    pan_pid.initialize()
    tilt_pid.initialize()

    while not exit_event.is_set():
        frame = frame_read.frame

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
            continue  # ignore the sample as it is too far from the previous sample

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

                # NOTE: if face is to the right of the drone, the distance will be negative, but
                # the drone has to have positive power so I am flipping the sign
                pan_update = pan_update * -1

                if tilt_update > max_speed_threshold:
                    tilt_update = max_speed_threshold
                elif tilt_update < -max_speed_threshold:
                    tilt_update = -max_speed_threshold

                print(int(pan_update), int(tilt_update))
                if track_face and fly:
                    # left/right: -100/100
                    tello.send_rc_control(pan_update // 3, 0, tilt_update // 2, 0)

        # send frame to other processes
        show_video_conn.send(frame)
        video_writer_conn.send(frame)
    # then we got the exit event so cleanup
    signal_handler(None, None)


def show_video(exit_event, pipe_conn):
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        frame = pipe_conn.recv()
        # display the frame to the screen
        cv2.imshow("Drone Face Tracking", frame)
        cv2.waitKey(1)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit_event.set()


def video_recorder(pipe_conn, save_video, height=300, width=400):
    global video_writer
    # create a VideoWrite object, recoring to ./video.avi
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if video_writer is None and save_video == True:
        video_file = f"video_{datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.mp4"
        video_writer = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'MP4V'), 30, (width, height))

    while True:
        frame = pipe_conn.recv()
        video_writer.write(frame)
        time.sleep(1 / 30)

    # then we got the exit event so cleanup
    signal_handler(None, None)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    run_pid = True
    track_face = True  # True - cause the Tello to start to track/follow a face
    save_video = True
    fly = True

    parent_conn, child_conn = Pipe()
    parent2_conn, child2_conn = Pipe()

    exit_event = Event()

    with Manager() as manager:
        p1 = Process(target=track_face_in_video_feed,
                     args=(exit_event, child_conn, child2_conn, run_pid, track_face, fly,))
        p2 = Process(target=show_video, args=(exit_event, parent_conn,))
        p3 = Process(target=video_recorder, args=(parent2_conn, save_video,))
        p2.start()
        p3.start()
        p1.start()

        p1.join()
        p2.terminate()
        p3.terminate()
        p2.join()
        p3.join()

    print("Complete...")
