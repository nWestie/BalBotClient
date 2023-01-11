from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.widget import MDWidget
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, StringProperty
from kivymd.uix.slider import MDSlider
from kivy_garden.graph import Graph, MeshLinePlot
import BTHandler


class SprungSlider(MDSlider):

    def sliderReleased(self):
        if (not self.active):
            self.value = 0


class Toggle(MDRectangleFlatButton, MDToggleButton):
    pass


class MainGraph(Graph, MDWidget):
    pass


class VoltGraph(Graph, MDWidget):
    pass


class ControllerMain(MDWidget):
    pObj = ObjectProperty(None)
    iObj = ObjectProperty(None)
    dObj = ObjectProperty(None)
    trimObj = ObjectProperty(None)
    speedObj = ObjectProperty(None)
    enableObj = ObjectProperty(None)
    connectBtn = ObjectProperty(None)
    btStatus = ObjectProperty(None)
    graphStack = ObjectProperty(None)
    pidLockOut = BooleanProperty(None)
    consoleText = StringProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btHandler = BTHandler.BTHandler("COM8", 1/20)
        Clock.schedule_interval(self.regularBTUpdate, 1/22)
        self.initGraphs()

    def regularBTUpdate(self, _):
        if (self.btStatus.working):
            status = self.btHandler.connectionStatus()
            if (status):
                self.btStatus.working = False
                self.btStatus.text = status
                if status.lower().find("error") != -1:
                    self.connectBtn.disabled = False
                    self.connectBtn.text = 'Connect'
                    self.connectBtn.state = 'normal'
                else:
                    self.connectBtn.text = 'Disconnect' if self.connectBtn.state == 'down' else 'Connect'
                    self.connectBtn.disabled = False
        if (self.connectBtn.state != 'down'):  # if not connected, return
            return

        if self.pidLockOut and self.btHandler.get("PIDenable"):
            pidVals = self.btHandler.getMany('p', 'i', 'd')
            self.pObj.value = pidVals['p']
            self.iObj.value = pidVals['i']
            self.dObj.value = pidVals['d']
            self.pidLockOut = False
            print('PID enabled')
        elif not self.btHandler.get('PIDenable'):
            self.pidLockOut = True

        enabled = True if self.enableObj.state == 'down' else False
        self.btHandler.set(speed=self.speedObj.value,
                           trim=self.trimObj.value, enable=enabled)
        # get a bunch of things
        botData = self.btHandler.getMany("messages", "voltage", 'logs')
        # print messages to console
        for message in botData['messages']:
            self.consoleText += (message)
        if self.consoleText.count('\n') > 10:
            lines = self.consoleText.splitlines(True)[-10:]
            self.consoleText = "".join(lines)

    def initGraphs(self):
        self.voltLine = MeshLinePlot(color=[1, 0, 0, 1])
        self.voltLine.points = [(x, .05*x+10) for x in range(100)]
        vGraph = VoltGraph()
        vGraph.add_plot(self.voltLine)
        self.graphStack.add_widget(vGraph)
        self.actDegLine = MeshLinePlot(color=[1, 0, 0, 1])
        self.actDegLine.points = [(x, .2*x+70) for x in range(100)]
        mGraph = MainGraph()
        mGraph.add_plot(self.actDegLine)
        self.graphStack.add_widget(mGraph)

    def sendPID(self):
        self.btHandler.set(p=self.pObj.value,
                           i=self.iObj.value, d=self.dObj.value)
        self.btHandler.set(sendPID=True)
        print('sendPID')

    def savePID(self):
        self.btHandler.set(p=self.pObj.value,
                           i=self.iObj.value, d=self.dObj.value)
        self.btHandler.set(sendPID=True, savePID=True)
        print('savePID')

    def enablePressed(self, state):
        val = True if state == 'down' else False
        self.btHandler.set(enable=val)
        self.consoleText += "yeet{}\n".format(self.consoleText.count('\n'))

        print('enable')  # 'normal' or 'down'

    def stepPressed(self, buttonText: str):
        self.step = float(buttonText)

    def connectPressed(self, state):
        print(state)
        self.connectBtn.disabled = True
        self.btStatus.working = True
        if (state == 'down'):
            self.btHandler.requestConnect()
            self.connectBtn.text = "Disconnect"
            self.btStatus.text = "Connecting..."
        elif (state == 'normal'):
            self.btHandler.requestConnect(disconnect=True)
            self.btStatus.text = "disconnecting..."


class MainApp(MDApp):
    def build(self):
        self.title = "Balance Bot Controller"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = '600'
        self.theme_cls.primary_dark_hue = '900'
        self.theme_cls.primary_light_hue = '400'
        self.theme_cls.accent_palette = "DeepPurple"

        self.controller = ControllerMain()
        return self.controller

    def on_stop(self):
        self.controller.btHandler.exit()


class NumSpinner(MDBoxLayout):
    step = NumericProperty(1)
    min = NumericProperty(1)

    def plusPressed(self):
        self.value += self.step

    def minusPressed(self):
        self.value -= self.step

    def textUpdated(self, str):
        self.value = max(float(str), self.min)


if __name__ == "__main__":
    Window.custom_titlebar = True
    Window.maximize()
    MainApp().run()
