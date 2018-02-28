from umqtt.simple import MQTTClient
from machine import Pin
import ubinascii
import machine
import ujson
import neopixel
import ure
import time
import urandom


# Default MQTT server to connect to
SERVER = "192.168.168.112"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
TOPIC = b"home/rgb1/set"


class Rainbow:
    """ Cycles through the colors of the rainbow

    i + x is the offsett for the different leds so they don't have the same color.
    """
    np = neopixel.NeoPixel(machine.Pin(0), 5)

    def __init__(self):
        print('Rainbow created!')

    def show(self, delay):
        for i in range(0,256):
            self.wheel(i, 0, self.np)
            self.wheel(i + 10, 1, self.np)
            self.wheel(i + 20, 2, self.np)
            self.wheel(i + 30, 3, self.np)
            self.wheel(i + 40, 4, self.np)

            self.np.write()
            time.sleep_ms(delay)

    def wheel(self, i, j, np):
        wheel_pos = ((i+j) & 255)
        wheel_pos = 255 - wheel_pos

        if wheel_pos < 85:
            np[j] = (255 - wheel_pos * 3, 0, wheel_pos * 3)
            return
        if wheel_pos < 170:
            wheel_pos -= 85
            np[j] = (0, wheel_pos * 3, 255 - wheel_pos * 3)
            return 
        wheel_pos -= 170
        np[j] = (wheel_pos * 3, 255 - wheel_pos * 3, 0)

class Led:
    np = neopixel.NeoPixel(machine.Pin(0), 5)
    startvalues = (0,0,0)
    defaultred = 0
    defaultgreen = 0
    defaultblue = 0
    red = 0
    green = 0
    blue = 0
    r_positive = 1
    g_positive = 1
    b_positive = 1
    counter = 0

    def __init__(self):
        print('Led object created')
    
    def update_colors(self, red, green, blue):
        self.startvalues = (red, green, blue)
        self.defaultred = red
        self.defaultgreen = green
        self.defaultblue = blue
        self.red = red
        self.blue = blue
        self.green = green

        for led in range(self.np.n):
            self.np[led] = self.startvalues

        self.np.write()
        
    def turn_off(self):
        for led in range(self.np.n):
            self.np[led] = (0,0,0)

        self.np.write() 

    def change_nyance(self):
        if self.startvalues != (0,0,0):
            if self.counter == 0:
                self.randomnum = int(urandom.getrandbits(8) / 52)
                self.counter = 30

            stepsize = 1
            offset = 30
            self.np[self.randomnum] = (self.update_led_color(stepsize, offset))
            self.np.write()
            self.counter -= 1        


    def update_led_color(self, step, offset):
        """ Chose a random color and increase or decrease its value
        
        The value will change up to the ofset value and down to the offset value.
        As long as the new value isn't below 0 or above 255. If thats the case, the
        value will be changed to the closest min/max.
        """
        random_color = urandom.getrandbits(2)

        # Red LED
        if random_color == 0:
            self.red = self.new_color_value(self.r_positive, self.red, step)
            self.r_positive = self.change_direction(self.r_positive, offset,
                                                    self.red, self.defaultred)

        # Green LED
        elif random_color == 1:
            self.green = self.new_color_value(self.g_positive, self.green, step)
            self.g_positive = self.change_direction(self.g_positive, offset,
                                                    self.green, self.defaultgreen)

        # Blue LED
        elif random_color == 2:
            self.blue = self.new_color_value(self.b_positive, self.blue, step)
            self.b_positive = self.change_direction(self.b_positive, offset,
                                                    self.blue, self.defaultblue)

        # print('New color: {} {} {}'.format(self.red, self.green, self.blue))
        return (self.red, self.green, self.blue)


    def change_direction(self, positive, offset, currentcolor, defaultvalue):
        """ Checks to see if we hit min/max and should go the other way. """
        if positive == 1:
            if currentcolor > (defaultvalue + offset) or currentcolor >= 255:
                return 0
            return 1
        else:
            if currentcolor < (defaultvalue - offset) or currentcolor <= 0:
                return 1
            return 0

    def new_color_value(self, positiveincrease, color, step):
        """ Returns a color between 0 - 255. """
        if positiveincrease == 1:
            newcolor = color + step
            if newcolor > 255:
                return 255
            else:
                return newcolor
        else:
            newcolor = color - step
            if newcolor < 0:
                return 0
            else:
                return newcolor


class HA_Client:
    percentage = 1
    ledstate = 'OFF'
    effect = 'None'
    updated = False
    raw_red = 0
    raw_green = 0
    raw_blue = 0
    red = 0
    green = 0
    blue = 0

    def __init__(self):
        print('Home assistant client object created!')

    def sub_callback(self, topic, msg):
        """ Callback triggers when information in Homeassistant changes

        Formats the message from homeassistant and saves the data. Variable "updated"
        let the main loop know there where a change. Homeassistant will only send state +
        the thing that was changed. In order to handle the variation i use try/exception.
        """
        self.updated = True
        msg_type, payload = msg.split(b":", 1)
        print('Received MQTT packed: {}'.format(msg))
        testjson = ujson.loads(msg.decode('utf-8'))

        # Save ledstate (on or off)
        self.ledstate = testjson['state']

        # Check color values
        try:
            self.raw_red = int(testjson['color']['r'])
            self.red = int(self.raw_red * self.percentage)
            if self.red < 0:
                self.red = 0

            self.raw_green = int(testjson['color']['g'])
            self.green = int(self.raw_green * self.percentage) 
            if self.green < 0:
                self.green = 0

            self.raw_blue = int(testjson['color']['b'])
            self.blue = int(self.raw_blue * self.percentage)
            if self.blue < 0:
                self.blue = 0 

            print('Red: {} Green: {} Blue: {}'.format(self.raw_red, self.raw_green, self.raw_blue))
        except KeyError:
            pass
        
        # Check brighness level
        try:
            passed = True
            self.percentage = int(testjson['brightness']) / 255
            self.red = int(self.raw_red * self.percentage)
            if self.red < 0:
                self.red = 0
            self.green = int(self.raw_green * self.percentage) 
            if self.green < 0:
                self.green = 0
            self.blue = int(self.raw_blue * self.percentage)
            if self.blue < 0:
                self.blue = 0 

            print('Brightness = {} %'.format(self.percentage))

        except KeyError:
            pass

        # Check if effect is changed
        try:
            self.effect = testjson['effect']
        except KeyError:
            pass

    def run(self, server=SERVER):
        """ Connects to Homeassistant, listen for changes and update led """
        led = Led()
        rainbow = Rainbow()

        c = MQTTClient(CLIENT_ID, server)
        c.set_callback(self.sub_callback)
        c.connect()
        c.subscribe(TOPIC)
        print("Connected to %s, subscribed to %s topic" % (server, TOPIC))

        try:
            while True:
                c.check_msg()
                if self.updated == True:
                    print('Updateing color')
                    led.update_colors(self.red, self.green, self.blue)
                    self.updated = False

                if ure.match('OFF', self.ledstate): 
                    led.turn_off()
                elif ure.match('rainbow', self.effect):
                    rainbow.show(60)
                elif ure.match('rainbow_slow', self.effect):
                    rainbow.show(100)
                elif ure.match('rainbow_fast', self.effect):
                    rainbow.show(30)
                else:
                    led.change_nyance()
                    time.sleep_ms(10)

        finally:
            c.disconnect()