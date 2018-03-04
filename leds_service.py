# -*-: coding utf-8 -*-
""" Leds service for handling visual feedback for various states of
    the system. """

import random
import time
import struct
import threading

from colour import Color

from usb.core import USBError

from singleton import Singleton
from usb_utils import USB

try:
    import respeaker.usb_hid as usb_hid
except USBError:
    print("Error accessing microphone: insufficient permissions. " +
          "You may need to replug your microphone and restart your device.")


class LedsService:
    """ Leds service for handling visual feedback for various states of
        the system. """

    class State:
        """ Leds states.- """
        none, waking_up, standby, listening, loading, notify, error, intentParsed, speak = range(9)

    def __init__(self, thread_handler):
        self.thread_handler = thread_handler
        led_device = USB.get_boards()
        if led_device == USB.Device.respeaker:
            self.animator = ReSpeakerAnimator()
        else:
            self.animator = None

    def start_animation(self, animation_id):
        if not self.animator:
            return
        (animation, identifier) = self.get_animation(animation_id)

        self.thread_handler.run(target=self.animator.run,
                                args=(identifier, animation, ))

    def get_animation(self, animation):
        identifier = str(random.randint(1, 100000))
        return (Animation(identifier, animation), identifier)


class Animation(Singleton):

    def __init__(self, id, active=0):
        self.id = id
        self.active = active


class ReSpeakerAnimator(object):

    def __init__(self):
        self.hid = usb_hid.get()
        self.led_dict = {
            'LED_1': 3,
            'LED_2': 4,
            'LED_3': 4,
            'LED_4': 5,
            'LED_5': 6,
            'LED_6': 7,
            'LED_7': 8,
            'LED_8': 9,
            'LED_9': 10,
            'LED_10': 11,
            'LED_11': 12,
            'LED_12': 13,
            'LED_13': 14,
        }

        self.animation_waking_up = [
            {value: 2 * st for value in self.led_dict.values()} for st in range(127)]
        
        self.animation_standby = [{value: st for value in self.led_dict.values(
        )} for st in list(range(0,255))]

        def value(i, j, N):
            if i == j:
                return [0, 255, 255]
            elif i == (j - 1) % N:
                return [0, 128, 255]
            elif i == (j + 1) % N:
                return [0, 255, 0]
            elif i == (j - 2) % N:
                return [0, 0, 255]
            elif i == (j + 2) % N:
                return [255, 0, 0]
            elif i == (j + 3) % N:
                return [255, 0, 128]
            else:
                return [0,0,0]


        self.animation_listening = []
        leds = range(3, 15)
        N = len(leds)

        for i in range(0, N):
            self.animation_listening.append(
                {leds[j]: value(i, j, N) for j in range(0, N)})

        self.animation_loading = [{value: 16 * st for value in self.led_dict.values()}
                                  for st in list(range(15)) + list(reversed(range(15)))]

        colors = [(1,0,0),(1,1,0),(0,1,0),(0,1,1),(1,1,1),(1,0,1)]
        self.animation_speak = []
        for i in range(0, len(colors)-1):
            if i<len(colors)-1:
                j=i+1
            else:
                j=0
            self.animation_speak.append(list(Color(rgb=colors[i]).range_to(Color(rgb=colors[j]),10)))

        self.animation_notify = []
        for frame in range(0, 2):
            self.animation_notify.append(
                {value: int("0000ff", 16) for value in self.led_dict.values()})
            self.animation_notify.append(
                {value: int("000000", 16) for value in self.led_dict.values()})

        self.animation_error = []
        for frame in range(0, 3):
            self.animation_error.append(
                {value: [255,0,0] for value in self.led_dict.values()})
            self.animation_error.append(
                {value: [0,0,0] for value in self.led_dict.values()})

        # Set the ReSpeaker in the right mode
        try:
            init_addr = 0  # 0x0
            init_data = 6  # 0x00000006

            self.write(init_addr, init_data)
        except Exception as e:
            print(e.message)

    def off(self):
        self.set_color(rgb=0)

    def set_color(self, rgb=None, r=0, g=0, b=0):
        if rgb:
            self.write(0, [1, rgb & 0xFF, (rgb >> 8) & 0xFF, (rgb >> 16) & 0xFF])
        else:
            self.write(0, [1, b, g, r])

    def doa(self):
        self.write(0, [7, 0, 0, 0])

    def write(self, address, data):
        if not type(data) is list:
            if data > 0xFFFF:
                data = struct.pack('<I', data)
            elif data > 0xFF:
                data = struct.pack('<H', data)

        data = self.to_bytearray(data)
        length = len(data)
        if self.hid:
            packet = bytearray([address & 0xFF, (address >> 8) &
                                0x7F, length & 0xFF, (length >> 8) & 0xFF]) + data
            packet = list(packet)
            self.hid.write(packet)

    def read(self, address, length):
        if self.hid:
            self.hid.write(list(bytearray(
                [address & 0xFF, (address >> 8) & 0xFF | 0x80, length & 0xFF, (length >> 8) & 0xFF])))
            for _ in range(6):
                data = self.hid.read()
                # skip VAD data
                if int(data[0]) != 0xFF and int(data[1]) != 0xFF:
                    return data[4:(4 + length)]

    @staticmethod
    def to_bytearray(data):
        if type(data) is int:
            array = bytearray([data & 0xFF])
        elif type(data) is bytearray:
            array = data
        elif type(data) is str:
            array = bytearray(data)
        elif type(data) is list:
            array = bytearray(data)
        else:
            raise TypeError('%s is not supported' % type(data))

        return array

    def run(self, id, animation, run_event):
        if animation.active == LedsService.State.none:
            print ("Animation : none")
            self.off()
            time.sleep(0.2)
            self.doa()

        elif animation.active == LedsService.State.standby:
            print ("Animation : Standby")
            time.sleep(0.3)
            self.off()
            time.sleep(0.2)
            self.doa()

        elif animation.active == LedsService.State.listening:
            print ("Animation : Listening")
            try:
                init_addr = 0  # 0x0
                init_data = 6  # 0x00000006

                self.write(init_addr, init_data)
            except Exception as e:
                print(e.message)

            while True:
                if animation.id != id or not run_event.is_set():
                    break
                for item in self.animation_listening:
                    if animation.id != id or not run_event.is_set():
                        break
                    for k, v in item.items():
                        self.write(k, v)
                    time.sleep(0.025)

        elif animation.active == LedsService.State.intentParsed:
            print ("Animation : Intent Parsed")
            self.set_color(r=0, g=255, b=0)

        elif animation.active == LedsService.State.speak:
            print ("Animation: Speak")

            while True:
                if animation.id != id or not run_event.is_set():
                    break
                for item in self.animation_speak:
                    for v in item:
                        if animation.id != id or not run_event.is_set():
                            break
                        c=list(v.rgb)
                        self.set_color(r=int(255*c[0]),g=int(255*c[1]),b=int(255*c[2]))
                        time.sleep(0.05)
        
        elif animation.active == LedsService.State.error:
            print ("Animation: Error")
            """
            for item in self.animation_error:
                if animation.id != id or not run_event.is_set():
                    break
                for k, v in item.items():
                    self.write(k, v)
                time.sleep(0.2)
            """
            self.set_color(r=255, g=0, b=0)
