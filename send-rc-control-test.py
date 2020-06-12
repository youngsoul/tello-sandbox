from djitellopy import Tello
import time

"""
This script use the `send_rc_control` method to change the speed instead of the other methods that
move the drone a particular distance.

The 
"""
speed = 10

up_down_speed = 0
left_right_speed = 0

tello = None


def set_speeds(ud, lr):
    global up_down_speed, left_right_speed
    up_down_speed = ud
    left_right_speed = lr
    tello.send_rc_control(lr, 0, ud, 0)


if __name__ == '__main__':
    tello = Tello()
    tello.connect()
    time.sleep(0.5)

    print(f"Battery Life Pecentage: {tello.get_battery()}")

    is_flying = False

    while True:
        print("1 - UP")
        print("2 - DOWN")
        print("3 - LEFT")
        print("4 - RIGHT")
        print("5 - Battery")
        print("6 - Stop (set speed to 0)")
        print("7 - +10 to speed")
        print("8 - -10 to speed")
        print("9 - Land")
        print("0 - Takeoff")

        cmd = input()
        if cmd == '':
            continue
        cmd = int(cmd)
        print(cmd)

        if cmd == 0:
            if not is_flying:
                tello.takeoff()
                is_flying = True
        elif cmd == 1:
            set_speeds(speed, 0)
        elif cmd == 2:
            set_speeds(-speed, 0)
        elif cmd == 5:
            print(f"Battery Life Percentage: {tello.get_battery()}")
        elif cmd == 6:
            set_speeds(0, 0)
        elif cmd == 7:
            if speed <=100:
                speed += 10
        elif cmd == 8:
            if speed >= -100:
                speed -= 10
        elif cmd == 9:
            tello.land()
            break

