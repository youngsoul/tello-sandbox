# Tello Drone Sandbox

This repo will contain various scripts to interact with the Tello Drone.

There will not be much rhyme or reason to the files other than just learning how to program the Tello drone.

![TelloGif](./media/Tello_Drone_face_following.gif)

## Drone
https://www.amazon.com/gp/product/B07H4W5YWB/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1

## Python API
The Python API I am using is:

[DJITelloPy](https://github.com/damiafuentes/DJITelloPy)

## Resources

https://www.murtazahassan.com/programming-drone-to-follow-object/

## Multiprocessing, Processes
MacOS security does not allow threads to be created normally

https://stackoverflow.com/questions/50168647/multiprocessing-causes-python-to-crash-and-gives-an-error-may-have-been-in-progr

```text
$ nano .bash_profile
```

```text
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```
## Following a detected face

The inspiration for this project was from the PyImageSearch book: 

[RaspberryPI for Computer Vision](https://www.pyimagesearch.com/raspberry-pi-for-computer-vision/)

In chapters 17 and 18 Adrian talks about a project to control a Pan/Tilt device to follow a face.  I wanted to take the same principals as described in his book and apply them to a drone tracking a face location.

## Architecture Overview

![TelloFaceArch](./media/tello_arch.png)
### Script
`tello_face_tracking.py`

This script starts up 3 processes to handle:

* Operating the Tello Drone.  Calculating where a face is and how much the drone has to move to follow the face.  This process will also send the video frame to two other processes

* Video Recorder. This process will record the video to a file in mp4 format.  

* Display Video.  This process will show the frames from the Tello Drone using OpenCV.  This process will also look for the 'q' command to quit the program and land the drone.  


