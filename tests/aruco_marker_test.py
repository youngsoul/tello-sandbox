import cv2
import time
from cv2 import aruco
from imutils.video import VideoStream
from imutils.perspective import order_points

vs = VideoStream(src=0).start()

# Setup the aruco marker detection
# aruco_dict = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)
aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)



aruco_params =  aruco.DetectorParameters_create()

# Loop until program is stopped with q on the keyboard
draw_corner_index = 0
while True:
    # Capture frame-by-frame
    frame = vs.read()

    # Convert the color frame to grayscale for marker detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Get marker corners and ids
    s = time.time()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    # image_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)
    image_markers = frame
    e = time.time()

    # Loop through the markers (in case more than one is detected)
    if ids is not None:
        for index, id in enumerate(ids):
            print(id)

    # print(markers)
    print(len(corners))
    if len(corners) > 0:
        print(corners[0].shape)
    # print(draw_corner_index)

    try:
        corner_x_y = corners[0][0][0]

        cv2.circle(image_markers, center=(corner_x_y[0], corner_x_y[1]), radius=8, color=(255, 0, 0), thickness=-1)

        draw_corner_index += 1
        if draw_corner_index >= 4:
            draw_corner_index = 0

        ordered_corners = order_points(corners[0][0])
        print(corners)
        print(ordered_corners)
        # print(frame.shape)
        # print(image_markers.shape)
        cv2.line(image_markers, (ordered_corners[0][0], ordered_corners[0][1]), (ordered_corners[1][0],ordered_corners[1][1]), (0,0,255), 1)
        cv2.line(image_markers, (ordered_corners[1][0], ordered_corners[1][1]), (ordered_corners[2][0],ordered_corners[2][1]), (0,0,255), 1)
        cv2.line(image_markers, (ordered_corners[2][0], ordered_corners[2][1]), (ordered_corners[3][0],ordered_corners[3][1]), (0,0,255), 1)
        cv2.line(image_markers, (ordered_corners[3][0], ordered_corners[3][1]), (ordered_corners[0][0],ordered_corners[0][1]), (0,0,255), 1)

        center_pt_x = ordered_corners[0][0] + (ordered_corners[1][0]-ordered_corners[0][0])/2
        center_pt_y = ordered_corners[0][1] + (ordered_corners[3][1]-ordered_corners[0][1])/2
        print(center_pt_x, center_pt_y)

        cv2.putText(image_markers, f"ID: {id[0]}",(int(center_pt_x), int(center_pt_y)), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2, cv2.LINE_AA) #


    except:
        pass



    # Display the resulting frame
    cv2.imshow('Tello', image_markers)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyWindow('Tello')