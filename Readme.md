# Tello Drone Sandbox

This repo will contain various scripts to interact with the Tello Drone.

There will not be much rhyme or reason to the files other than just learning how to program the Tell

## Drone
https://www.amazon.com/gp/product/B07H4W5YWB/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1

## Python API

The Python API I am using is:

[DJITelloPy](https://github.com/damiafuentes/DJITelloPy)

## Resources

https://www.murtazahassan.com/programming-drone-to-follow-object/

## Multiprocessing, Processes
macos security does not allow threads to be created normally

https://stackoverflow.com/questions/50168647/multiprocessing-causes-python-to-crash-and-gives-an-error-may-have-been-in-progr

```text
$ nano .bash_profile
```

```text
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```
