from pyimagesearch.pid import PID
import time
# pan_pid = PID(kP=0.7, kI=0.0001, kD=0.09)
pan_pid = PID(kP=0.7, kI=0.0001, kD=0.09)
pan_pid.initialize()

if __name__ == '__main__':

    for i in range(-100,100):
        pid_value = pan_pid.update(30)
        print(i, int(pid_value))
        time.sleep(.05)

