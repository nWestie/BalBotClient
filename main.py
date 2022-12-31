from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.slider import MDSlider
from kivy.core.window import Window

class SprungSlider(MDSlider):

    def sliderReleased(self):
        if(not self.active):
            self.value = 0    
pidStep = 1
class PIDButton(MDRectangleFlatButton, MDToggleButton):
    def pressed(self, buttonText: str):
        global pidStep
        pidStep = float(buttonText)

class ControllerMain(MDWidget):
    pObj = ObjectProperty(None)
    iObj = ObjectProperty(None)
    dObj = ObjectProperty(None)
    trimObj = ObjectProperty(None)
    
    def sendPID(self):
        print(self.pObj.value, self.iObj.value, self.dObj.value)
    def savePID(self):
        print(self.pObj.value, self.iObj.value, self.dObj.value)

class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = '600'
        self.theme_cls.primary_dark_hue = '800'
        self.theme_cls.primary_light_hue = '400'
        self.theme_cls.accent_palette = "Orange"
        return ControllerMain()

class NumSpinner(MDBoxLayout):

    def plusPressed(self):
        self.value += pidStep

    def minusPressed(self):
        self.value -= pidStep

    def textUpdated(self, str):
        self.value = max(float(str),0)


if __name__ == "__main__":
    Window.custom_titlebar = True
    Window.maximize()
    MainApp().run()
