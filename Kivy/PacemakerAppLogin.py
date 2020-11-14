# main.py

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

kv = Builder.load_file("pacemakerlogin.kv")

## Serial Details ----------------------------------------------------------------------

## set correct COM port!
pacemaker_serial = serial.Serial(port="COM7", baudrate=115200,timeout=1)

def serialSend():
    ## order of transmission: paceLocation, sensingTrue, LRL,   URL,    AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, ARP,    VRP
    ## types of transmission: u char        u char       uchar  uchar   float   float    float          float           float   float
    AtrAmp_DutyCycle = AtrAmp_value/5.0 *100
    VentAmp_DutyCycle = VentAmp_value/5.0 *100
    serialSend = struct.pack('BBBBBBffffff',0x16,0x55, paceLocation, sensingTrue, int(LRL_value), int(URL_value), AtrAmp_DutyCycle, VentAmp_DutyCycle, AtrPulseWidth_value, VentPulseWidth_value, ARP_value, VRP_value) ## byte list of length 30 bytes
    pacemaker_serial.write(serialSend)
    print(len(serialSend))
    print(serialSend)
    print([0x16,0x55, paceLocation, sensingTrue, int(LRL_value), int(URL_value), AtrAmp_DutyCycle, VentAmp_DutyCycle, AtrPulseWidth_value, VentPulseWidth_value, ARP_value, VRP_value])

#serialReceive = ....









## Declare all the Screens ----------------------------------------------------------------------

## WelcomeWindow ----------------------------------------

class WelcomeWindow(Screen):
    def goToLogin(self):
        manageWin.transition = SlideTransition()
        manageWin.transition.direction = "up"
        manageWin.current = "loginWin"
    
    def goToReg(self):
        if(len(userDatabase.users) < 10):       ## there are less than 10 accounts
            manageWin.transition = SlideTransition()
            manageWin.transition.direction = "right"
            manageWin.current = "registerWin"
        else:
            ## 10 account maximum reached
            accountLimitReached()



## LoginWindow ----------------------------------------

class LoginWindow(Screen):
    nameField = ObjectProperty(None)
    passwField = ObjectProperty(None)


    def btnLogin(self):
        user = self.nameField.text
        password = self.passwField.text

        ## Check username and password for correctness
        ## if good...
        if(userDatabase.credentialCheck(user, password)):
            manageWin.transition = RiseInTransition()
            manageWin.transition.duration = 0.15
            manageWin.current = "mainWin"
            MainWindow.currentUsername = user
            self.reset() ## clear the form
        ## if bad
        else:
            invalidLogin()

    
    ## Go Back to Welcome
    def btnBack(self):
        self.reset() ## clear the form
        manageWin.transition = SlideTransition()
        manageWin.transition.direction = "down"
        manageWin.current = "welcomeWin"

    def reset(self):
        self.nameField.text = ""
        self.passwField.text = ""


## RegisterWindow ----------------------------------------

class RegisterWindow(Screen):
    firstName_Field = ObjectProperty(None)
    lastName_Field = ObjectProperty(None)
    username_Field = ObjectProperty(None)
    password_Field = ObjectProperty(None)

    def regUser(self):

        fname = self.firstName_Field.text
        lname = self.lastName_Field.text
        username = self.username_Field.text
        password = self.password_Field.text

        ## check for non empty strings and no forbitten characters, ie: ";"
        if (self.notEmpty(username, fname, lname, password) and self.noBadChars(username, fname, lname, password)): 
            ## register user in database
            if(userDatabase.add_user(username, fname, lname, password) == 1):
                ## user added succesfully
                self.reset() ## clear the form
                manageWin.transition = SlideTransition()
                manageWin.transition.direction = "left"
                manageWin.transition.duration = 0.15
                manageWin.current = "welcomeWin"
                registerComplete() # popup
            else:
                invalidRegister() ## username already taken
                self.reset()  ## clear the form
        else:
            invalidRegister()
            self.reset()  ## clear the form
    
    def notEmpty(self,username,firstName,lastName,password):
        if(username.strip() != "" and firstName.strip() != "" and lastName.strip() != "" and password.strip() != ""):
            return 1
        else: return 0

    def noBadChars(self,username,firstName,lastName,password):
        badChars = [";","/"] ## all the illegal characters
        for char in badChars:
            if((char in username) or (char in firstName) or (char in lastName) or (char in password)):
                return 0
        else: return 1


    ## Go Back to Welcome
    def btnBack(self):
        self.reset() ## clear the form
        manageWin.transition = SlideTransition()
        manageWin.transition.direction = "left"
        manageWin.current = "welcomeWin"

    def reset(self):
        self.firstName_Field.text = ""
        self.lastName_Field.text = ""
        self.username_Field.text = ""
        self.password_Field.text = ""


## MainWindow ----------------------------------------

class MainWindow(Screen):
    currentUser = ObjectProperty(None)
    display_active_pacingMode = ObjectProperty(None)

    display_LRL_parameter = ObjectProperty(None)
    display_URL_parameter = ObjectProperty(None)
    display_AtrAmp_parameter = ObjectProperty(None)
    display_VentAmp_parameter = ObjectProperty(None)
    display_AtrPulseWidth_parameter = ObjectProperty(None)
    display_VentPulseWidth_parameter = ObjectProperty(None)
    display_VRP_parameter = ObjectProperty(None)
    display_ARP_parameter = ObjectProperty(None)

    #for later ### display_heartbeat_bpm = ObjectProperty(None) ## in progress


    currentUsername = "" ## initialize the local variable, takes it's value from loginWindow btnLogin

    ## Indicator for connected Hardware
    indicatorColour = ListProperty([1,0,0,1]) ## defaults to red, becomes green if connected
    
    #declare text values
    global pacingMode, LRL, URL, AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, VRP, ARP
    pacingMode, LRL, URL, AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, VRP, ARP = 9*["Not Set"]

    # declare values
    global paceLocation, sensingTrue, LRL_value, URL_value, AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value
    ## uints
    paceLocation, sensingTrue, LRL_value, URL_value = 4*[0]
    #floats
    AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value = 6*[0.0]

    global heartBPM #### in progress
    global hardwareConnected
    #change this for assignment 2
    hardwareConnected = False ## set to board for assignment 2
    heartBPM = 100 ## temporary

    def on_enter(self, *args):
        ##initialize the text labels
        self.currentUser.text = "Active User: " + userDatabase.get_user(self.currentUsername)[0]
        self.display_active_pacingMode.text = "Pacing Mode: " + pacingMode
        self.display_LRL_parameter.text = "Lower Rate Limit: " + LRL
        self.display_URL_parameter.text = "Upper Rate Limit: " + URL
        self.display_AtrAmp_parameter.text = "Atrium Aplitude: " + AtrAmp
        self.display_VentAmp_parameter.text = "Ventricle Amplitude: " + VentAmp
        self.display_AtrPulseWidth_parameter.text = "AtrPulseWidth: " + AtrPulseWidth
        self.display_VentPulseWidth_parameter.text = "VentPulseWidth: " + VentPulseWidth
        self.display_ARP_parameter.text = "Atrium Refractory Period: " + ARP
        self.display_VRP_parameter.text = "Ventricular Refractory Period: " + VRP
        #self.display_heartbeat_bpm.text = "BPM: " + str(heartBPM) ####  for later 
        


        ## set hardware connected indicator
        if(hardwareConnected):
            self.indicatorColour = [0,1,0,1] ## green
        else: 
            self.indicatorColour = [1,0,0,1] ## defaults to red

    def logout(self):
        #edit transition
        manageWin.transition = FallOutTransition()
        manageWin.transition.duration = 0.15
        manageWin.current = "welcomeWin"
        ## popup "Logout Successful"
        signOut_Complete()
    
    ## Option to delete account
    def deleteAccount(self):
        userDatabase.remove_user(self.currentUsername)
        manageWin.transition = FallOutTransition()
        manageWin.transition.duration = 0.15
        manageWin.current = "welcomeWin"
        userDeleted()
    
    ## Mode Popup window is displayed
    def open_modeSelector(self):
        show = modeSelectorPopup()
        global popupWindow
        popupWindow = Popup(title="Pacemaker Modes", content=show,size_hint=(None,None), size=(500,500))
        popupWindow.open()

    ## Programmable Parameters Popup window is displayed
    def open_programmableParameters(self):
        show = programmableParametersPopup()
        global popupWindow
        popupWindow = Popup(title="Programmable Parameters", content=show,size_hint=(None,None), size=(500,500))
        popupWindow.open()
    


## Declare all Popups Layout Classes ----------------------------------------------------------------------

## Main page popups
class modeSelectorPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

    def setPacingMode(self,mode):
        setPacingModetext(mode)

# Popup for programmableParameterPopup
class programmableParametersPopup(FloatLayout):
    
    # Store the index variable to keep track of which parameter to be changed
    def setIndex(self, num):
        global index
        index = num

    # Open popup for text input
    def open_textInput(self, title):
        show = textInputPopup()
        global popupWindow_editParameter
        popupWindow_editParameter = Popup(title=title, content=show,size_hint=(None,None), size=(350,300))
        popupWindow_editParameter.open()

    def closePopup(self):
        popupWindow.dismiss()
        manageWin.transition = NoTransition()
        manageWin.current = "welcomeWin"
        manageWin.current = "mainWin"
        serialSend()

# Popup for text input
class textInputPopup(FloatLayout):

    inputField = ObjectProperty(None)

    # Check which parameter is being changed and set it to the text inputted
    def selectProgParam(self):
        num = self.inputField.text

        if index == 1:
            setLRL(num)
        elif index == 2:
            setURL(num)
        elif index == 3:
            setAtrAmp(num)
        elif index == 4:
            setAtrPulseWidth(num)
        elif index == 5:
            setARP(num)
        elif index == 6:
            setVentAmp(num)
        elif index == 7:
            setVentPulseWidth(num)
        elif index == 8:
            setVRP(num)

    def closePopup(self):
        popupWindow_editParameter.dismiss()
        manageWin.transition = NoTransition()
        manageWin.current = "welcomeWin"
        manageWin.current = "mainWin"


## Generic Errors
class errorPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

## maximum accounts reached 
class errorMaxPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

## Auto-timout Popup
class successPopup(FloatLayout):
    def __init__(self, **kwargs):
        super(successPopup, self).__init__(**kwargs)
        # call dismiss_popup after 1 second
        Clock.schedule_once(self.closePopup, 1)

    def closePopup(self, timer):
        popupWindow.dismiss()




## Global Vars and Functions ----------------------------------------------------------------------


def setPacingModetext(mode):
    global pacingMode
    pacingMode = mode
    print(pacingMode)

    global paceLocation, sensingTrue

    ## check if atrium, ventrial, or dual
    if(pacingMode=="AOO" or pacingMode=="AAI"):
        paceLocation = 1
    elif(pacingMode=="VOO" or pacingMode=="VVI"):
        paceLocation = 2

    ##check sensing or not
    if(pacingMode=="AAI" or pacingMode=="VVI"):
        sensingTrue = 1
    else: sensingTrue = 0

    manageWin.transition = NoTransition()
    manageWin.current = "welcomeWin"
    manageWin.current = "mainWin"

    ##testing, for demo purpose only. remove for assignment 2
    global hardwareConnected
    hardwareConnected = True
    ## testing end


## Set programmable parameters
def setLRL(num):
    global LRL  ##text
    global LRL_value ## uint
    LRL_value = num
    LRL = num + " BPM"   ##bpm rate between roughly 30 and 100
    print("LRL: " + LRL)

def setURL(num):
    global URL  ##text
    global URL_value ## uint
    URL_value = num
    URL = num + " BPM"   ##bpm rate between roughly 80 and 150
    print("URL: " + URL)

def setAtrAmp(num):
    global AtrAmp  ##text
    global AtrAmp_value ## single
    AtrAmp_value = float(num)
    AtrAmp = num + " V"   ##voltage between 0 and 5V
    print("AtrAmp: " + AtrAmp)
    
def setAtrPulseWidth(num):
    global AtrPulseWidth  ##text
    global AtrPulseWidth_value ## single
    AtrPulseWidth_value = float(num)
    AtrPulseWidth = num + " ms"      ##time between ~1 to 30 msec
    print("AtrPulseWidth: " + AtrPulseWidth)
    
def setVentAmp(num):
    global VentAmp  ##text
    global VentAmp_value ## single
    VentAmp_value = float(num)
    VentAmp = num + " V"   ##voltage between 0 and 5V
    print("VentAmp: " + VentAmp)
    
def setVentPulseWidth(num):
    global VentPulseWidth  ##text
    global VentPulseWidth_value ## single
    VentPulseWidth_value = float(num)
    VentPulseWidth = num + " ms"    ##time between ~1 to 30 msec
    print("VentPulseWidth: " + VentPulseWidth)
    
def setVRP(num):
    global VRP  ##text
    global VRP_value ## single
    VRP_value = float(num)
    VRP = num + " ms"           ##time between ~1 to 500 msec
    print("VRP: " + VRP)
    
def setARP(num):
    global ARP  ##text
    global ARP_value ## single
    ARP_value = float(num)
    ARP = num + " ms"          ##time between ~1 to 500 msec
    print("ARP: " + ARP)





## Initialize the Popups ------------------------------------------------------

def invalidLogin():
    show = errorPopup()
    global popupWindow
    popupWindow = Popup(title="Login Error", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()

def invalidRegister():
    show = errorPopup()
    global popupWindow
    popupWindow = Popup(title="Username not allowed or is already taken", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()

def registerComplete():
    show = successPopup()
    global popupWindow
    popupWindow = Popup(title="You are now Registered", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()

def signOut_Complete():
    show = successPopup()
    global popupWindow
    popupWindow = Popup(title="You have now signed out", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()

def accountLimitReached():
    show = errorMaxPopup()
    global popupWindow
    popupWindow = Popup(title="Error", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()

def userDeleted():
    show = successPopup()
    global popupWindow
    popupWindow = Popup(title="Account Deleted", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()




## WindowManager --------------------------------------------

class WindowManager(ScreenManager):
    pass

manageWin = WindowManager(transition=SlideTransition())

## Add all the pages ------------------------------------------
manageWin.add_widget(WelcomeWindow(name="welcomeWin"))
manageWin.add_widget(LoginWindow(name="loginWin"))
manageWin.add_widget(RegisterWindow(name="registerWin"))
manageWin.add_widget(MainWindow(name="mainWin"))

manageWin.current = "welcomeWin"


## Database Details ----------------------------------------------------------------------

#check if file exists
if(os.path.isfile("saved_users.txt")):
    print("file located successfuly")
else:
    f = open("saved_users.txt", "w")
    f.close()
    print("no file found, new file was created")

## Load the database
userDatabase = Database("saved_users.txt")


## Run the App ----------------------------------------------------------------------

class PacemakerApp(App):
    def build(self):
        return manageWin

if __name__ == "__main__":
    PacemakerApp().run()