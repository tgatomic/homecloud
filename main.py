import webrepl
import machine
import neopixel
import time
import math
import utime

from os import listdir
from micropython import mem_info
from Homecloud import HA_Client

def set_color(color):
    """ Set the same color on all devices

    Preferably use 0xFFEE88 as argument so that you can control each color.
    """
    np = neopixel.NeoPixel(machine.Pin(0), 5)
    for led in range(np.n):
        np[led] = (((color >> 16) & 0xFF), ((color >> 8) & 0xFF), (color & 0xFF))

    print(color)
    np.write()

def reboot(second):
    """ Does a hard reset, make sure to disconnect webclient before it resets. """
    print('\nRebooting..')
    time.sleep(second)
    machine.reset()

def system_information():
    """ Prints out stored files and memory information. """
    print('\nFiles on system:\n{}\n'.format(listdir()))
    print('Memory information:')
    mem_info()
    print('\n')

def custom_demo(delay):
    """ Breathes between the colors. """
    np = neopixel.NeoPixel(machine.Pin(0), 5)

    red = 0
    blue = 0
    green = 0
    redstep = 50
    bluestep = 100
    greenstep = 250
    intensity = 90 # normal = 127

    while True:

        for i in range(np.n):
            red = int((math.sin(redstep * 0.0174533)+1)*intensity)
            blue = int((math.sin(bluestep * 0.0174533)+1)*intensity)
            green = int((math.sin(greenstep * 0.0174533)+1)*intensity)
            np[i] = (red, blue, green)

        np.write()

        redstep += 1
        bluestep += 1
        greenstep += 1

        if redstep == 360:
            redstep = 0
            intensity += 1

        if bluestep == 360:
            bluestep = 0

        if greenstep == 360:
            greenstep = 0

        if intensity == 127:
            intensity = 80

        time.sleep_ms(delay)

def demo(np):
    """ Demo that came with Micropython on ESP8266. """
    n = np.n

    # cycle
    for i in range(4 * n):
        for j in range(n):
            np[j] = (0, 0, 0)
        np[i % n] = (255, 255, 255)
        np.write()
        time.sleep_ms(25)

    # bounce
    for i in range(4 * n):
        for j in range(n):
            np[j] = (0, 0, 128)
        if (i // n) % 2 == 0:
            np[i % n] = (0, 0, 0)
        else:
            np[n - 1 - (i % n)] = (0, 0, 0)
        np.write()
        time.sleep_ms(60)

    # fade in/out
    for i in range(0, 4 * 256, 8):
        for j in range(n):
            if (i // 256) % 2 == 0:
                val = i & 0xff
            else:
                val = 255 - (i & 0xff)
            np[j] = (val, 0, 0)
        np.write()

    # clear
    for i in range(n):
        np[i] = (0, 0, 0)
    np.write()


if __name__ == "__main__":
    # Starts the server wich enable you to connect to it through webbrowser
    webrepl.start()

    # Blink leds to see it started
    np = neopixel.NeoPixel(machine.Pin(0), 5)
    demo(np)

    # Wait so we have time to interrupt processor if something goes wrong
    utime.sleep_ms(5000)

    # Prints information about system
    print('\n\nSystem started')
    print('Files on system:\n{}\n'.format(listdir()))
    print('Memory information:')
    mem_info()

    #Start the main programloop
    print('\nStarting program...')
    try:
        client = HA_Client()
        client.run()
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print('Exception: {}'.format(ex))
        utime.sleep_ms(3000)
        machine.reset()