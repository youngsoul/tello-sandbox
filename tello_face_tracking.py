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
import argparse

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


def track_face_in_video_feed(exit_event, show_video_conn, video_writer_conn, track_face, fly=False,
                             max_speed_limit=40):
    """

    :param exit_event: Multiprocessing Event.  When set, this event indicates that the process should stop.
    :type exit_event:
    :param show_video_conn: Pipe to send video frames to the process that will show the video
    :type show_video_conn: multiprocessing Pipe
    :param video_writer_conn: Pipe to send video frames to the process that will save the video frames
    :type video_writer_conn: multiprocessing Pipe
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
    time.sleep(0.1)
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
        if frame is None:
            print("Failed to read video frame")
            tello.send_rc_control(0, 0, 0, 0)
            time.sleep(0.5)
            continue

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

            # send frame to other processes
            if show_video_conn:
                show_video_conn.put(frame)

            if video_writer_conn:
                video_writer_conn.put(frame)

            continue  # ignore the sample as it is too far from the previous sample

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

        # send frame to other processes
        if show_video_conn:
            show_video_conn.put(frame)

        if video_writer_conn:
            video_writer_conn.put(frame)

    # then we got the exit event so cleanup
    signal_handler(None, None)


def show_video(exit_event, pipe_conn):
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Start Show Video Process")

    while True:
        frame = pipe_conn.get()
        # display the frame to the screen
        cv2.imshow("Drone Face Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit_event.set()

def video_recorder(pipe_conn, height=300, width=400):
    global video_writer
    # create a VideoWrite object, recoring to ./video.avi
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Start Video Recorder")

    if video_writer is None:
        video_file = f"video_{datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.mp4"
        video_writer = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'mp4v'), 30, (width, height))

    while True:
        frame = pipe_conn.get()
        video_writer.write(frame)
        time.sleep(1 / 30)

    # then we got the exit event so cleanup
    signal_handler(None, None)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("****************")
    print("execute: export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES")
    print("****************")

    ap = argparse.ArgumentParser()
    ap.add_argument("--display-video", type=int, required=False, default=1,  help="Display Drone video using OpenCV.  Default: 1")
    ap.add_argument("--save-video", type=int, required=False, default=1, help="Save video as MP4 file.  Default: 1")
    ap.add_argument("--fly", type=int, required=False, default=0, help="Flag to control whether the drone should take flight. You also need to 'track-face' for the drone to follow the face.  Default: 0")
    ap.add_argument("--track-face", type=int, required=False, default=0, help="Flag to control whether Face detection should be used to control the drone.  Default: 0")

    args = vars(ap.parse_args())

    track_face = True if args['track_face'] == 1 else False
    save_video = True if args['save_video'] == 1 else False
    fly = True if args['fly'] == 1 else False
    print(f"Fly: {fly}")
    fly = False
    display_video = True if args['display_video'] == 1 else False

    display_video_queue = None
    if display_video:
        display_video_queue = Queue()

    save_video_queue = None
    if save_video:
        save_video_queue = Queue()

    exit_event = Event()

    with Manager() as manager:
        p1 = Process(target=track_face_in_video_feed,
                     args=(exit_event, display_video_queue, save_video_queue, track_face, fly,))

        if display_video:
            p2 = Process(target=show_video, args=(exit_event, display_video_queue,))
        else:
            p2 = None

        if save_video:
            p3 = Process(target=video_recorder, args=(save_video_queue,))
        else:
            p3 = None

        if p2:
            p2.start()

        if p3:
            p3.start()

        p1.start()

        p1.join()
        if p2:
            p2.terminate()

        if p3:
            p3.terminate()

        if p2:
            p2.join()

        if p3:
            p3.join()

    print("Complete...")
