from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.widget import MDWidget
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivy.properties import ObjectProperty, NumericProperty
from kivymd.uix.slider import MDSlider
import BTHandler


class SprungSlider(MDSlider):

    def sliderReleased(self):
        if (not self.active):
            self.value = 0


class Toggle(MDRectangleFlatButton, MDToggleButton):
    pass


class ControllerMain(MDWidget):
    pObj = ObjectProperty(None)
    iObj = ObjectProperty(None)
    dObj = ObjectProperty(None)
    trimObj = ObjectProperty(None)
    enableObj = ObjectProperty(None)
    connectBtn = ObjectProperty(None)
    btStatus = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btHandler = BTHandler.BTHandler("COM8")

    def sendPID(self):
        print(self.pObj.value, self.iObj.value, self.dObj.value)

    def savePID(self):
        print(self.pObj.value, self.iObj.value, self.dObj.value)

    def enablePressed(self, state):
        print(state)  # 'normal' or 'down'

    def stepPressed(self, buttonText: str):
        self.step = float(buttonText)

    def connectPressed(self, state):
        print(state)
        if (state == 'down'):
            self.btStatus.text = "Connecting..."
            self.btStatus.working = True
            self.connectBtn.text = "Disconnect"
            if (self.btHandler.connect()):
                self.btStatus.text = "Connected on " + self.btHandler.port
            else:
                self.btStatus.text = "Connection Error"
                self.connectBtn.state = 'normal'
                self.connectBtn.text = "Connect"
            self.btStatus.working = False
        elif (state == 'normal'):
            self.connectBtn.disabled = True
            self.btStatus.text = "disconnecting..."
            self.btStatus.working = True
            if (self.btHandler.disconnect()):
                self.connectBtn.text = "Connect"
                self.btStatus.working = False
                self.btStatus.text = ''
            else:
                self.btStatus.working = False
                self.btStatus.text = 'Failed to Disconnect'
                self.connectBtn.text = 'Disconnect'
                # self.connectBtn.state = 'down'
            self.connectBtn.disabled = False


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = '600'
        self.theme_cls.primary_dark_hue = '900'
        self.theme_cls.primary_light_hue = '400'
        self.theme_cls.accent_palette = "DeepPurple"
        return ControllerMain()


class NumSpinner(MDBoxLayout):
    step = NumericProperty(1)

    def plusPressed(self):
        self.value += self.step

    def minusPressed(self):
        self.value -= self.step

    def textUpdated(self, str):
        self.value = max(float(str), 0)


if __name__ == "__main__":
    Window.custom_titlebar = True
    Window.maximize()
    MainApp().run()
