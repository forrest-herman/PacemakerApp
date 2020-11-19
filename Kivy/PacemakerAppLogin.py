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

kv = Builder.load_file("pacemakerlogin.kv")

## Serial Details

#pacemaker_serial = serial.Serial(port="COM#", baudrate=...,timeout=...)















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
    
    global pacingMode, LRL, URL, AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, VRP, ARP
    pacingMode, LRL, URL, AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, VRP, ARP = 9*["Not Set"]

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
    
    ## Saves the parameter data into the user_data.txt file to deploy in the future
    def deploy(self):
        self.file = open("user_data.txt", "w")
        self.data = {}
        self.file.write( self.currentUsername + ";" + URL + ";" + LRL + ";" + AtrAmp + ";" + VentAmp + ";" + AtrPulseWidth + ";" + VentPulseWidth + ";" + VRP + ";" + ARP + "\n")
        self.file.close()

    

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

# Popup for text input
class textInputPopup(FloatLayout):

    inputField = ObjectProperty(None)

    # Check which parameter is being changed and set it to the text inputted
    def selectProgParam(self):
        num = self.inputField.text

        if index == 1:
            if int(num) > 150 or int(num) < 40:
                show = errorPopup()
                global popupWindow
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                setLRL(num)

        elif index == 2:
            if int(num) > 150 or int(num) < 60:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                setURL(num)

        elif index == 3:
            if int(num) > 5 or int(num) < 0:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                setAtrAmp(num)

        elif index == 4:
            if float(num) > 100 or float(num) < 0:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                setAtrPulseWidth(num)

        elif index == 5:
            if float(num) > 600 or float(num) < 0:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                setARP(num)

        elif index == 6:
            if int(num) > 5 or int(num) < 0:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                 setVentAmp(num)

        elif index == 7:
            if float(num) > 100 or float(num) < 0:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
                  setVentPulseWidth(num)

        elif index == 8:
            if float(num) > 600 or float(num) < 0:
                show = errorPopup()
                popupWindow = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow.open()
            else:
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
    manageWin.transition = NoTransition()
    manageWin.current = "welcomeWin"
    manageWin.current = "mainWin"

    ##testing, for demo purpose only. remove for assignment 2
    global hardwareConnected
    hardwareConnected = True
    ## testing end


## Set programmable parameters
def setLRL(num):
    global LRL  ## double
    LRL = num + " BPM"   ##bpm rate between roughly 30 and 100
    print("LRL: " + LRL)

def setURL(num):
    global URL  ## double
    URL = num + " BPM"   ##bpm rate between roughly 80 and 150
    print("URL: " + URL)

def setAtrAmp(num):
    global AtrAmp
    AtrAmp = num + " V"   ##voltage between 0 and 5V
    print("AtrAmp: " + AtrAmp)
    
def setAtrPulseWidth(num):
    global AtrPulseWidth
    AtrPulseWidth = num + " ms"      ##time between ~1 to 30 msec
    print("AtrPulseWidth: " + AtrPulseWidth)
    
def setVentAmp(num):
    global VentAmp
    VentAmp = num + " V"   ##voltage between 0 and 5V
    print("VentAmp: " + VentAmp)
    
def setVentPulseWidth(num):
    global VentPulseWidth
    VentPulseWidth = num + " ms"    ##time between ~1 to 30 msec
    print("VentPulseWidth: " + VentPulseWidth)
    
def setVRP(num):
    global VRP
    VRP = num + " ms"           ##time between ~1 to 500 msec
    print("VRP: " + VRP)
    
def setARP(num):
    global ARP
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

if(os.path.isfile("user_data.txt")):
    print("file located successfuly")
else:
    f = open("user_data.txt", "w")
    f.close()
    print("no file found, new file was created")

## Load the database
userDatabase = Database("saved_users.txt")

## If a new database class needs to be created 
#parameterDatabase = paramDatabase("user_data.txt")


## Run the App ----------------------------------------------------------------------

class PacemakerApp(App):
    def build(self):
        return manageWin

if __name__ == "__main__":
    PacemakerApp().run()