from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.slider import Slider


class LoginScreen(MDWidget):
    pass
class SprungSlider(Slider):
    sVal = NumericProperty(None)

    def sliderReleased(self):
        print(self.sVal)
        self.sVal +=10

    
pidStep = 1
class PIDButton(MDRectangleFlatButton, MDToggleButton):
    def pressed(self, buttonText: str):
        global pidStep
        pidStep = float(buttonText)



class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.primary_hue = '600'
        self.theme_cls.primary_dark_hue = '900'
        self.theme_cls.primary_light_hue = '400'
        self.theme_cls.accent_palette = "Orange"
        return LoginScreen()

class NumSpinner(MDBoxLayout):
    value = NumericProperty(None)

    def plusPressed(self):
        self.value += pidStep

    def minusPressed(self):
        self.value -= pidStep

    def textUpdated(self, str):
        self.value = max(float(str),0)


if __name__ == "__main__":
    MainApp().run()
