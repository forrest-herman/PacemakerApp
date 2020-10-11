import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import (ScreenManager, Screen, NoTransition, SlideTransition, CardTransition, SwapTransition, FadeTransition, WipeTransition, FallOutTransition, RiseInTransition)
from kivy.graphics import Color
## database

kv = Builder.load_file("pacemakerlogin.kv")


#TEMP
user = ""
password = ""
# global password

## Windows

class WelcomeWindow(Screen):
    pass

class LoginWindow(Screen):
    nameField = ObjectProperty(None)
    passwField = ObjectProperty(None)


    def btnLogin(self):
        ## Check username and password for correctness

        ## TEMP
        global user
        user = self.nameField.text
        global password
        password = self.passwField.text

        ## if good...
        if(user == "Forrest" and password == "1234"):
            manageWin.transition = RiseInTransition()
            manageWin.current = "mainWin"
            self.reset()
        ## if bad
        else:
            invalidLogin()

    
    def reset(self):
        self.nameField.text = ""
        self.passwField.text = ""

    ## Back
    def btnBack(self):
        manageWin.transition = SlideTransition()
        manageWin.transition.direction = "down"
        manageWin.current = "welcomeWin"

class RegisterWindow(Screen):
    pass

class MainWindow(Screen):
    global password
    global user

    currentUser = ObjectProperty(None)

    def on_enter(self, *args):
        user
        self.currentUser.text = "Name: " + user


    # tempUser.text = user
    # tempPass = ObjectProperty(None)
    # tempPass.text = password
    pass



class WindowManager(ScreenManager):
    pass

manageWin = WindowManager(transition=SlideTransition())

## Add all the pages
manageWin.add_widget(WelcomeWindow(name="welcomeWin"))
manageWin.add_widget(LoginWindow(name="loginWin"))
manageWin.add_widget(RegisterWindow(name="registerWin"))
manageWin.add_widget(MainWindow(name="mainWin"))

manageWin.current = "welcomeWin"



## Error Popup stuff

class errorPopup(FloatLayout):
    def closePopup(self):
        popupWindow.dismiss()

def invalidLogin():
    show = errorPopup()
    global popupWindow
    popupWindow = Popup(title="Login Error", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()
    #return popupWindow
    #errorPopup(Button).bind(on_press=popupWindow.dismiss)

def invalidRegister():
    show = errorPopup()
    popupWindow = Popup(title="Email not legit", content=show,size_hint=(None,None), size=(300,200))
    popupWindow.open()






class PacemakerApp(App):
    def build(self):
        return manageWin

if __name__ == "__main__":
    PacemakerApp().run()