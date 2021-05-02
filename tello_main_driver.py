import cv2
from djitellopy import Tello
import signal
import sys
import time
from datetime import datetime
from multiprocessing import Manager, Process, Queue
import argparse
import importlib

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


def _process_keyboard_commands(tello):
    """
    Process keyboard commands via OpenCV.
    :param tello:
    :type tello:
    :return: 0 - Exit, 1 - continue processing, 2 - suspend processing handler
    :rtype:
    """
    exit_flag = 1
    key = cv2.waitKey(1) & 0xff
    if key == 27: # ESC
        exit_flag = 0

    elif key == ord('w'):
        tello.move_forward(30)

    elif key == ord('s'):
        tello.move_back(30)

    elif key == ord('a'):
        tello.move_left(30)

    elif key == ord('d'):
        tello.move_right(30)

    elif key == ord('e'):
        tello.rotate_clockwise(30)

    elif key == ord('q'):
        tello.rotate_counter_clockwise(30)

    elif key == ord('r'):
        tello.move_up(30)

    elif key == ord('f'):
        tello.move_down(30)

    elif key == ord('l'):
        tello.land()
        exit_flag = 0

    elif key == ord('x'):
        exit_flag = 2 # stop processing the handler function but continue to fly and see video

    return exit_flag



def process_tello_video_feed(handler_file, show_video_queue, video_writer_queue, track_face, fly=False,
                             max_speed_limit=40):
    """

    :param exit_event: Multiprocessing Event.  When set, this event indicates that the process should stop.
    :type exit_event:
    :param show_video_queue: Pipe to send video frames to the process that will show the video
    :type show_video_queue: multiprocessing Pipe
    :param video_writer_queue: Pipe to send video frames to the process that will save the video frames
    :type video_writer_queue: multiprocessing Pipe
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

    init_method = None
    handler_method = None

    if handler_file:
        handler_file = handler_file.replace(".py", "")
        handler_module = importlib.import_module(handler_file)
        init_method =  getattr(handler_module, 'init')
        handler_method = getattr(handler_module, 'handler')

    tello = Tello()

    rtn = tello.connect()
    print(f"Connect Return: {rtn}")

    init_method(tello, max_speed=max_speed_limit, fly=fly)

    tello.streamon()
    time.sleep(2)
    frame_read = tello.get_frame_read()

    processing_flag = _process_keyboard_commands(tello)
    while processing_flag != 0:
        frame = frame_read.frame
        if frame is None:
            print("Failed to read video frame")
            tello.send_rc_control(0, 0, 0, 0)
            time.sleep(0.5)
            processing_flag = _process_keyboard_commands(tello)
            continue

        if processing_flag == 1:
            handler_method(tello, frame, track_face, fly)
        else:
            # stop let keyboard commands take over
            tello.send_rc_control(0, 0, 0, 0)


        # send frame to other processes
        if show_video_queue:
            show_video_queue.put(frame)

        if video_writer_queue:
            video_writer_queue.put(frame)

        processing_flag = _process_keyboard_commands(tello)

    # then we got the exit event so cleanup
    signal_handler(None, None)


def show_video(frame_queue):
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Start Show Video Process")

    while True:
        frame = frame_queue.get()
        # display the frame to the screen
        cv2.imshow("Drone Face Tracking", frame)

def video_recorder(frame_queue, height=300, width=400):
    global video_writer
    # create a VideoWrite object, recoring to ./video.avi
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Start Video Recorder")

    if video_writer is None:
        video_file = f"video_{datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.mp4"
        video_writer = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'mp4v'), 30, (width, height))

    while True:
        frame = frame_queue.get()
        video_writer.write(frame)
        time.sleep(1 / 30)

    # then we got the exit event so cleanup
    signal_handler(None, None)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("****************")
    print("execute: export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  ")
    print("****************")

    ap = argparse.ArgumentParser()
    ap.add_argument("--display-video", type=int, required=False, default=1,  help="Display Drone video using OpenCV.  Default: 1")
    ap.add_argument("--save-video", type=int, required=False, default=1, help="Save video as MP4 file.  Default: 1")
    ap.add_argument("--fly", type=int, required=False, default=0, help="Flag to control whether the drone should take flight. You also need to 'track-face' for the drone to follow the face.  Default: 0")
    ap.add_argument("--handler-file", type=str, required=False, default="", help="Name of the python file with an init and handler method.  Do not include the .py extension and it has to be in the same folder as this main driver")
    ap.add_argument("--max-speed", type=int, required=False, default=40, help="0-100 value")

    args = vars(ap.parse_args())

    track_face = True if args['track_face'] == 1 else False
    save_video = True if args['save_video'] == 1 else False
    fly = True if args['fly'] == 1 else False
    print(f"Fly: {fly}")
    display_video = True if args['display_video'] == 1 else False
    max_speed = args['max_speed']
    handler_file = args['handler_file']

    display_video_queue = None
    if display_video:
        display_video_queue = Queue()

    save_video_queue = None
    if save_video:
        save_video_queue = Queue()

    with Manager() as manager:
        p1 = Process(target=process_tello_video_feed,
                     args=(handler_file, display_video_queue, save_video_queue, track_face, fly,max_speed,))

        if display_video:
            p2 = Process(target=show_video, args=(display_video_queue,))
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
