from djitellopy import Tello
import time

print("Create Tello object")
tello = Tello()

print("Connect to Tello Drone")
tello.connect()

print(f"Battery Life Pecentage: {tello.get_battery()}")


print("Takeoff - hoser!")
tello.takeoff()

time.sleep(1)
print("Move Left 100 cm")
tello.move_left(50)

time.sleep(1)
print("Rotate clockwise")
tello.rotate_clockwise(90)

time.sleep(1)
print("Move forward 100 cm")
tello.move_forward(50)

print("Prepare floor to land.... you have 1 second")
time.sleep(1)
print("landing")
tello.land()
print("touchdown.... goodbye")
