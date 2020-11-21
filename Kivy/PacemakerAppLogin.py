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
from kivy.garden.graph import MeshLinePlot
from numpy import random


kv = Builder.load_file("pacemakerlogin.kv")


## Serial Details ----------------------------------------------------------------------

def serialConnect():
    notConnected = True
    global pacemaker_serial, hardwareConnected
    port = ["COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8"] ## set correct COM port!
    i = len(port)
    while notConnected:
        i -= 1
        try:
            pacemaker_serial = serial.Serial(port=port[i], baudrate=115200,timeout=1)
            notConnected = False
        except:
            notConnected = True
            print(port[i] + " failed")
        if (notConnected == False): 
            hardwareConnected = True
            print(port[i] + " connected")
            pacemaker_serial.flush()
            break


#pacemaker_serial = serial.Serial(port="COM7", baudrate=115200,timeout=1)

def serialSend():
    AtrAmp_DutyCycle = AtrAmp_value/5.0 *100
    VentAmp_DutyCycle = VentAmp_value/5.0 *100
    AtrSens_DutyCycle = AtrSens_value/3.3 *100
    VentSens_DutyCycle = VentSens_value/3.3 *100
    ## order of transmission: paceLocation, sensingTrue, LRL,   URL,    AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, ARP,    VRP     AtrSens,    VentSens
    ## types of transmission: u char        u char       uchar  uchar   float   float    float          float           float   float   float       float
    serialSend = struct.pack('<BBBBBBffffffff',0x16,0x55, paceLocation, sensingTrue, int(LRL_value), int(URL_value), AtrAmp_DutyCycle, VentAmp_DutyCycle, AtrPulseWidth_value, VentPulseWidth_value, ARP_value, VRP_value, AtrSens_DutyCycle, VentSens_DutyCycle) ## byte list of length 38 bytes
    pacemaker_serial.write(serialSend)
    print(len(serialSend))
    #print(serialSend)
    #print(serialSend.hex())
    print([0x16,0x55, paceLocation, sensingTrue, int(LRL_value), int(URL_value), AtrAmp_DutyCycle, VentAmp_DutyCycle, AtrPulseWidth_value, VentPulseWidth_value, ARP_value, VRP_value, AtrSens_DutyCycle,VentSens_DutyCycle])

def serialRequest():
    serialRequest = struct.pack('<BBBBBBffffffff',0x16,0x22, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0) ## byte list of length 38 bytes
    pacemaker_serial.write(serialRequest)

def serialReceive():
    inputRead = struct.unpack('<ff',pacemaker_serial.read(8)) # 2 floats
    return inputRead


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



## LoginWindow ---------------------------------------------------------------

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


## RegisterWindow --------------------------------------------------------------------------------

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
    display_AtrSens_parameter = ObjectProperty(None)
    display_VentSens_parameter = ObjectProperty(None)
    display_reactionTime_parameter = ObjectProperty(None)
    display_recoveryTime_parameter = ObjectProperty(None)

    #for later ### display_heartbeat_bpm = ObjectProperty(None) ## in progress

    currentUsername = "" ## initialize the local variable, takes it's value from loginWindow btnLogin

    ## Indicator for connected Hardware
    indicatorColour = ListProperty([1,0,0,1]) ## defaults to red, becomes green if connected
    
    global pacingMode, LRL, URL, AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, VRP, ARP, AtrSens, VentSens, reactionTime, recoveryTime
    pacingMode, LRL, URL, AtrAmp, VentAmp, AtrPulseWidth, VentPulseWidth, VRP, ARP, AtrSens, VentSens, reactionTime, recoveryTime = 13*["Not Set"]

    global paceLocation, sensingTrue, rateAdaptiveTrue, LRL_value, URL_value, AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value, AtrSens_value, VentSens_value, reactionTime_value, recoveryTime_value
    ## uints
    paceLocation, sensingTrue, responseFactor, rateAdaptiveTrue, LRL_value, URL_value, reactionTime_value, recoveryTime_value = 8*[0]

    #floats
    AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value, AtrSens_value, VentSens_value = 8*[0.0]

    #global heartBPM #### in progress
    #heartBPM = 100 ## temporary

    global hardwareConnected
    hardwareConnected = False

    def on_enter(self, *args):
        ##initialize the text labels
        self.currentUser.text = "Active User: " + userDatabase.get_user(self.currentUsername)[0]
        self.display_active_pacingMode.text = "Pacing Mode: " + pacingMode
        self.display_LRL_parameter.text = "Lower Rate Limit: " + LRL
        self.display_URL_parameter.text = "Maximum Sensor Rate: " + URL
        self.display_AtrAmp_parameter.text = "Atrium Aplitude: " + AtrAmp
        self.display_VentAmp_parameter.text = "Ventricle Amplitude: " + VentAmp
        self.display_AtrPulseWidth_parameter.text = "AtrPulseWidth: " + AtrPulseWidth
        self.display_VentPulseWidth_parameter.text = "VentPulseWidth: " + VentPulseWidth
        self.display_ARP_parameter.text = "Atrium Refractory Period: " + ARP
        self.display_VRP_parameter.text = "Ventricular Refractory Period: " + VRP
        self.display_AtrSens_parameter.text = "AtrSensitivity: " + AtrSens
        self.display_VentSens_parameter.text = "VentSensitivity: " + VentSens
        self.display_reactionTime_parameter.text = "Reaction Time: " + reactionTime
        self.display_recoveryTime_parameter.text = "Recovery Time: " + recoveryTime
        ##add new parameters
        #self.display_URL_parameter.text = "Upper Rate Limit: " + URL
        


        ## set hardware connected indicator
        #if(hardwareConnected):
            #self.indicatorColour = [0,1,0,1] ## green
        #else: 
            #self.indicatorColour = [1,0,0,1] ## defaults to red

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

    ## Heartbeat Graph Popup window is displayed
    def open_heartbeatGraph(self):
        show = heartbeatGraphPopup()
        global popupWindow
        popupWindow = Popup(title="Current Heartbeat", content=show,size_hint=(None,None), size=(1000,1000))
        popupWindow.open()
            
    ## Saves the parameter data into the user_data.txt file to deploy in the future
    def deploy(self):
        #if all values not zero
        self.file = open("user_data.txt", "w")
        self.data = {URL_value, LRL_value, AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value, AtrSens_value, VentSens_value, reactionTime_value, recoveryTime}
        self.file.write(self.currentUsername + ";" + str(URL_value) + ";" + str(LRL_value) + ";" + str(AtrAmp_value) + ";" + str(VentAmp_value) + ";" + str(AtrPulseWidth_value) + ";" + str(VentPulseWidth_value) + ";" + str(VRP_value) + ";" + str(ARP_value) + ";" + str(AtrSens_value) + ";" + str(VentSens_value) + ";" + str(reactionTime_value) + ";" + str(recoveryTime_value) + "\n")
        self.file.close()
        serialSend()


    # Saves the parameter data into the user_data.txt file to deploy in the future
    def load_data(self):

        self.file = open("user_data.txt", "r")
        self.data = {}

        for line in self.file:
            self.currentUsername, LRL_value, URL_value, AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value, AtrSens_value, VentSens_value, reactionTime_value, recoveryTime_value = line.strip().split(";")
            self.data[self.currentUsername] = (LRL_value, URL_value, AtrAmp_value, VentAmp_value, AtrPulseWidth_value, VentPulseWidth_value, VRP_value, ARP_value,AtrSens_value, VentSens_value, reactionTime_value, recoveryTime_value)
        
        self.file.close()
        #else, throw error!
    

    def save_data(self):
        self.data = {}
        with open("user_data.txt", "w") as f:
            for user in self.data:
                f.write(user + ";" + self.data[user][0] + ";" + self.data[user][1] + ";" + self.data[user][2] + ";" + self.data[user][3] + ";" + self.data[user][4] + ";" + self.data[user][5] + ";" + self.data[user][6] + ";" + self.data[user][7] + ";" + self.data[user][8] + ";" + self.data[user][9] + ";" + self.data[user][10] + self.data[user][11] + "\n")


    def serialConnectMain(self):
        serialConnect()
        if(hardwareConnected):
            self.indicatorColour = [0,1,0,1] ## green
        else: 
            self.indicatorColour = [1,0,0,1] ## defaults to red

    

## Declare all Popups Layout Classes -----------------------------------------------------------------------------------------------------------------------------------------------------------

## Main page popups
class modeSelectorPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

    def setPacingMode(self,mode):
        setPacingModetext(mode)


## Egram -----------------------------------------------------------------------

class heartbeatGraphPopup(FloatLayout):
    
    def __init__(self,):
        super(heartbeatGraphPopup, self).__init__()
        self.plot1 = MeshLinePlot(color=[1, 0, 0, 1])
        self.plot2 = MeshLinePlot(color=[1, 0, 0, 1])
    
    def startHeartbeat(self):
        serialRequest()

        global ATR_graphArray, VENT_graphArray
        ATR_graphArray = 150*[0.0]
        VENT_graphArray = 150*[0.0]

        self.ids.graphAtr.add_plot(self.plot1)
        Clock.schedule_interval(self.get_value_atr, 0.005)

        self.ids.graphVent.add_plot(self.plot2)
        Clock.schedule_interval(self.get_value_vent, 0.005)


    def stopHeartbeat(self):
        Clock.unschedule(self.get_value_atr)
        Clock.unschedule(self.get_value_vent)

    def get_value_atr(self, dt):
        #time.sleep(0.5) #how long does it take to accumulate data
        global ATR_graphArray,tupleInput
        
        tupleInput = serialReceive()
        serialRequest()
        print(tupleInput)
        ATR_graphArray.pop(0)
        ATR_graphArray.append(tupleInput[0]) ## 0 = -3.3 V || 0.5 = 0 V || 1 = 3.3 V
        self.plot1.points = [(i, j) for i, j in enumerate(ATR_graphArray)]

        
    def get_value_vent(self, dt):
        # serial receive
        global VENT_graphArray,tupleInput
        VENT_graphArray.pop(0)
        VENT_graphArray.append(tupleInput[1])
        self.plot2.points = [(i, j) for i, j in enumerate(VENT_graphArray)]

    def closePopup(self):
        popupWindow.dismiss()

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
        global popupWindow_paramError

        ## LRL -------
        if index == 1:
            if int(num) > 150 or int(num) < 40:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                setLRL(num) ##typecast float to int

        ## URL -------
        elif index == 2:
            if int(num) > 180 or int(num) < 60:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                setMSR(num) ##typecast float to int

        ## AtrAmp -------
        elif index == 3:
            if int(num) > 5 or int(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                setAtrAmp(num)

        ## AtrPulseWidth -------
        elif index == 4:
            if float(num) > 100 or float(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                setAtrPulseWidth(num)

        ## ARP -------
        elif index == 5:
            if float(num) > 600 or float(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                setARP(num)

        ## VentAmp -------
        elif index == 6:
            if int(num) > 5 or int(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                 setVentAmp(num)

        ## VentPulseWidth -------
        elif index == 7:
            if float(num) > 100 or float(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                  setVentPulseWidth(num)

        ## VRP -------
        elif index == 8:
            if float(num) > 600 or float(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                  setVRP(num)
        
        elif index == 9:
            if float(num) > 3 or float(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                  setAtrSens(num)
        
        elif index == 10:
            if float(num) > 3.3 or float(num) < 0:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                  setVentSens(num)
        
        elif index == 11:
            if (float(num) > 50 or float(num) < 10):
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                  setreactionTime(num)
        
        elif index == 12:
            if float(num) > 960 or float(num) < 60:
                show = paramErrorPopup()
                popupWindow_paramError = Popup(title="Input Error", content=show,size_hint=(None,None), size=(300,200))
                popupWindow_paramError.open()
            else:
                  setrecoveryTime(num)

    def closePopup(self):
        popupWindow_editParameter.dismiss()
        manageWin.transition = NoTransition()
        manageWin.current = "welcomeWin"
        manageWin.current = "mainWin"
    
    
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

def setAtrSens(num):
    global AtrSens
    global AtrSens_value
    AtrSens_value = float(num)
    AtrSens = num + " V"          ##time between ~1 to 500 msec
    print("AtrSensitivity: " + AtrSens)

def setVentSens(num):
    global VentSens
    global VentSens_value
    VentSens_value = float(num)
    VentSens = num + " V"          ##time between ~1 to 500 msec
    print("VentSensitivity: " + VentSens)

def setreactionTime(num):
    global reactionTime
    global reactionTime_value
    reactionTime_value = num
    reactionTime = num + " ms"          ##time between ~1 to 500 msec
    print("reactionTime: " + reactionTime)

def setrecoveryTime(num):
    global recoveryTime
    global recoveryTime_value
    recoveryTime_value = num
    recoveryTime = num + " ms"          ##time between ~1 to 500 msec
    print("recoveryTime: " + recoveryTime)

### PULL THESE CHANGES>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

## Generic Errors
class errorPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

## maximum accounts reached 
class errorMaxPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

class paramErrorPopup(FloatLayout):
    def closePopup(self):
        popupWindow_paramError.dismiss()

## Auto-timout Popup
class successPopup(FloatLayout):
    def __init__(self, **kwargs):
        super(successPopup, self).__init__(**kwargs)
        # call dismiss_popup after 1 second
        Clock.schedule_once(self.closePopup, 1)

    def closePopup(self, timer):
        popupWindow.dismiss()




## Global Vars and Functions -----------------------------------------------------------------------------------------------------------------

## Set pacing mode
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


## Set programmable parameters
def setLRL(num):
    global LRL  ##text
    global LRL_value ## uint
    LRL_value = num
    LRL = num + " BPM"   ##bpm rate between roughly 30 and 100
    print("LRL: " + LRL)

def setMSR(num):
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




## WindowManager ------------------------------------------------------------------------------------------------------------------------------------

class WindowManager(ScreenManager):
    pass

manageWin = WindowManager(transition=SlideTransition())

## Add all the pages ------------------------------------------------------------------------------------------------------------------------------
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