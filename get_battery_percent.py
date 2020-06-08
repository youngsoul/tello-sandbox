from djitellopy import Tello
import time

print("Create Tello object")
tello = Tello()

print("Connect to Tello Drone")
tello.connect()

print(f"Battery Life Pecentage: {tello.get_battery()}")


