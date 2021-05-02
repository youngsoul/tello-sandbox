import cv2
import threading

mouse_click_x = None
mouse_click_y = None
image_to_show = None
''
def click_capture(event, x, y, flags, param):
    global mouse_click_x, mouse_click_y
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Click Capture: {x},{y}")
        mouse_click_y = y
        mouse_click_x = x

def app_thread():
    global image_to_show
    # load the image, clone it, and setup the mouse callback function
    image = cv2.imread("../media/tello_arch.png")
    image_to_show = image.copy()
    cv2.setMouseCallback("image", click_capture)
    while True:
        if image_to_show is None:
            image_to_show = image.copy()
        # display the image and wait for a keypress
        if mouse_click_x is not None and mouse_click_y is not None:
            cv2.circle(image_to_show, center=(mouse_click_x, mouse_click_y), radius=8, color=(255, 0, 0), thickness=-1)



if __name__ == '__main__':
    cv2.namedWindow("image")

    t = threading.Thread(target=app_thread)
    t.setDaemon(True)
    t.start()
    # keep looping until the 'q' key is pressed
    while True:
        if image_to_show is not None:
            cv2.imshow("image", image_to_show)

        key = cv2.waitKey(1) & 0xFF
        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            image_to_show = None
            mouse_click_y = mouse_click_x = None
        # if the 'c' key is pressed, break from the loop
        elif key == ord("c"):
            break

    cv2.destroyWindow('image')
    cv2.destroyAllWindows()
