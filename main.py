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
import btHandler
from functools import partial


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

    # pObj = ObjectProperty(None)
    # iObj = ObjectProperty(None)
    # dObj = ObjectProperty(None)
    trimObj = ObjectProperty(None)
    speedObj = ObjectProperty(None)
    enableObj = ObjectProperty(None)
    connectBtn = ObjectProperty(None)
    btStatus = ObjectProperty(None)
    graphStack = ObjectProperty(None)
    connectLockout = BooleanProperty(None)
    consoleText = StringProperty(None)
    voltageText = StringProperty("")
    pidLocked: BooleanProperty = BooleanProperty(None)

    def __init__(self, *args, **kwargs):
        self.kP: float = 0
        self.kI: float = 0
        self.kD: float = 0
        
        super().__init__(*args, **kwargs)
        self.btHandler:btHandler.BTHandler = btHandler.BTHandler("COM6", self, 1/20)
        # Clock.schedule_interval(self.regularBTUpdate, 1/22)
        self.initGraphs()

    def regularBTUpdate(self, _):
        # status = self.btHandler.connectionStatus()

        # # these should be called on connection:
        # self.voltageText = ""
        # self.consoleText = ""
        # self.voltLine.points = []
        # self.actDegLine.points = []
        # self.setDegLine.points = []

        # if not connected, return

        # pid Locking
        # if self.pidLocked and self.btHandler.get("PIDenable"):
        #     pidVals = self.btHandler.getMany('p', 'i', 'd')
        #     self.pObj.value = pidVals['p']
        #     self.iObj.value = pidVals['i']
        #     self.dObj.value = pidVals['d']
        #     self.pidLocked = False
        #     print('PID enabled')
        # elif not self.btHandler.get('PIDenable'):
        #     self.pidLocked = True

        # update speed and trim
        # self.btHandler.set(speed=self.speedObj.value, trim=self.trimObj.value)
        # get logging and update UI
        # botData = self.btHandler.getMany("messages", 'logs')
        # self.btHandler.clearLists('messages', 'logs')

        # self.enableObj.state = 'down' if self.btHandler.isEnabled() else 'normal'

        # for message in botData['messages']:
        #     self.consoleText += (message)
        # if self.consoleText.count('\n') > 10:
        #     lines = self.consoleText.splitlines(True)[-10:]
        #     self.consoleText = "".join(lines)

        # if not botData['logs']:
        #     return
        # for packet in botData['logs']:
        #     self.voltLine.points.append((packet[0], packet[1]))
        #     self.setDegLine.points.append((packet[0], packet[2]))
        #     self.actDegLine.points.append((packet[0], packet[3]))
        # self.voltageText = str(self.voltLine.points[-1][1]) + ' V'
        # # Scroll Graphs if needed
        # if self.voltLine.points[-1][0] > self.voltGraph.xmax:
        #     self.voltLine.points = self.voltLine.points[-301:]
        #     self.setDegLine.points = self.setDegLine.points[-301:]
        #     self.actDegLine.points = self.actDegLine.points[-301:]
        #     max = self.voltLine.points[-1][0]
        #     min = max - 15
        #     self.voltGraph.xmin = min
        #     self.voltGraph.xmax = max
        #     self.mainGraph.xmin = min
        #     self.mainGraph.xmax = max
        pass

    def connect_gui_update(self, connected: bool, in_progress: bool, status: str):
        """When connection state changes, updates the gui lockouts, btStatus, and connect button states"""
        self.btStatus.working = in_progress
        self.connectBtn.disabled = in_progress
        self.connectBtn.state = 'down' if connected else 'normal'
        self.connectBtn.text = 'DISCONNECT' if connected else 'CONNECT'
        self.btStatus.text = status
        self.connectLockout = not connected
        # PID controls must be relocked when connection is lost
        if(not connected):
            self.pidLocked = True

    def set_pid_status(self, kp:float,ki:float,kd:float, enable_input):
        self.kP = kp
        self.kI = ki
        self.kD = kd
        self.pidLocked = not enable_input
        print("unlocking pid")
        
    def initGraphs(self):
        self.voltLine = MeshLinePlot(color=[1, 0, 0, 1])
        # self.voltLine.points = [(x/20, .1) for x in range(300)]
        self.voltGraph = VoltGraph()
        self.voltGraph.add_plot(self.voltLine)
        self.graphStack.add_widget(self.voltGraph)
        self.setDegLine = MeshLinePlot(color=[1, 1, 0, 1])
        # self.setDegLine.points = [(x/20, 90) for x in range(300)]
        self.actDegLine = MeshLinePlot(color=[1, 0, 0, 1])
        # self.actDegLine.points = [(x/20, 0) for x in range(300)]
        self.mainGraph = MainGraph()
        self.mainGraph.add_plot(self.setDegLine)
        self.mainGraph.add_plot(self.actDegLine)
        self.graphStack.add_widget(self.mainGraph)

    def sendPID_pressed(self, save=False):
        self.btHandler.request_action(partial(self.btHandler.sendPID, self.kP, self.kI, self.kD, save))

    def savePID(self):
        pass
        # self.btHandler.set(p=self.pObj.value,
        #                    i=self.iObj.value, d=self.dObj.value)
        # self.btHandler.set(sendPID=True, savePID=True)

    def connect_pressed(self, state):
        print(f"Connect pressed, state={state}")
        self.connectBtn.disabled = True
        if (state == 'down'):
            self.btHandler.request_action(self.btHandler.connect) 
        elif (state == 'normal'):
            self.btHandler.request_action(self.btHandler.disconnect) 


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
    # Window.custom_titlebar = True
    Window.maximize()
    MainApp().run()
