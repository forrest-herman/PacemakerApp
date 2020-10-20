# main.py

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
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

kv = Builder.load_file("pacemakerlogin.kv")


## Declare all the Screens ----------------------------------------------------------------------

## WelcomeWindow ----------------------------------------

class WelcomeWindow(Screen):
    def goToLogin(self):
        manageWin.transition = SlideTransition()
        manageWin.transition.direction = "up"
        manageWin.current = "loginWin"
    
    def goToReg(self):
        if(len(userDatabase.users) < 10):
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
        ## Check username and password for correctness

        user = self.nameField.text
        password = self.passwField.text

        ## if good...
        if(userDatabase.credentialCheck(user, password)):
            manageWin.transition = RiseInTransition()
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

        if (self.notEmpty(username, fname, lname, password)):  ##### add check for forbitten characters, ie: ";"
            ## register user in database
            if(userDatabase.add_user(username, fname, lname, password) == 1):
                ## user added succesfully
                self.reset() ## clear the form
                manageWin.transition = SlideTransition()
                manageWin.transition.direction = "left"
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
    currentUsername = ""

    
    def on_enter(self, *args):
        self.currentUser.text = "Active User: " + userDatabase.get_user(self.currentUsername)[0]

    def logout(self):
        #edit transition
        manageWin.transition = FallOutTransition()
        manageWin.transition.duration = 0.15
        manageWin.current = "welcomeWin"
        ## idea! popout: "Logout Successful"
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
    


## Declare all Popups Layout Classes ----------------------------------------------------------------------

## Main page popups
class modeSelectorPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

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