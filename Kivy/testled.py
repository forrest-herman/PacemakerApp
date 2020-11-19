import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.properties import ListProperty
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import (ScreenManager, Screen, NoTransition, SlideTransition, CardTransition, SwapTransition, FadeTransition, WipeTransition, FallOutTransition, RiseInTransition)
from kivy.graphics import Color
from database import Database
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.base import runTouchApp
import os.path
from kivy.clock import Clock
import time
import serial
import struct


Builder.load_string("""
<MyPage>:
    Button:
        size_hint: 0.5,0.5
        pos_hint: {"center_x":0.5,"center_y":0.5}
        text: "Click Button for LED"
        on_press: root.btnclick()
""")

global a
a = 0

## Serial Details
pacemaker_serial = serial.Serial(port="COM7", baudrate=115200,timeout=1)


class MyPage(FloatLayout):
    def btnclick(self):
        global a
        if (a==0):
            array=struct.pack('BBBfH',0x16,0x55,1,0.5,100)
            print(len(array))
            print(array)
            ## slice terminator
            pacemaker_serial.write(struct.pack('BBBfH',0x16,0x55,1,0.5,100))
            #pacemaker_serial.close()
            a = 1
            print("LED ON")
        else:
            pacemaker_serial.write(struct.pack('BBBfH',0x16,0x55,0,0.5,100))
            #pacemaker_serial.close()
            a = 0
            print("LED OFF")


## Run the App ----------------------------------------------------------------------

class testledApp(App):
    def build(self):
        return MyPage()

if __name__ == "__main__":
    testledApp().run()