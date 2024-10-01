import threading
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


class NumSpinner(MDBoxLayout):
    step = NumericProperty(1)
    min = NumericProperty(1)
    value = NumericProperty(0)

    def textUpdated(self, str):
        try:
            self.value = max(float(str), self.min)
        except:
            self.text = "{0:.2f}".format(self.value)


class ControllerMain(MDWidget):
    enableObj = ObjectProperty(None)
    connectBtn = ObjectProperty(None)
    btStatus = ObjectProperty(None)
    graphStack = ObjectProperty(None)
    connectLockout = BooleanProperty(None)
    consoleText = StringProperty(None)
    voltageText = StringProperty("")
    pidLocked: BooleanProperty = BooleanProperty(None)
    trim: NumericProperty = NumericProperty(0)
    kP: NumericProperty = NumericProperty(0)
    kI: NumericProperty = NumericProperty(0)
    kD: NumericProperty = NumericProperty(0)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.btHandler: btHandler.BTHandler = btHandler.BTHandler(
            "COM6", self, 1/20)
        # Clock.schedule_interval(self.regularBTUpdate, 1/22)
        self._joystick_val = 0
        self._joystick_lock: threading.Lock = threading.Lock()
        self.initGraphs()

    def regularBTUpdate(self, _):
        # status = self.btHandler.connectionStatus()

        # # these should be called on connection:
        # self.voltageText = ""
        # self.consoleText = ""
        # self.voltLine.points = []
        # self.actDegLine.points = []
        # self.setDegLine.points = []

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

    def connect_pressed(self, state):
        print(f"Connect pressed, state={state}")
        self.connectBtn.disabled = True
        if (state == 'down'):
            self.trim = 0
            self.btHandler.request_action(self.btHandler.connect)
        elif (state == 'normal'):
            self.btHandler.request_action(self.btHandler.disconnect)

    def connect_gui_update(self, connected: bool, in_progress: bool, status: str):
        """When connection state changes, updates the gui lockouts, btStatus, and connect button states"""
        self.btStatus.working = in_progress
        self.connectBtn.disabled = in_progress
        self.connectBtn.state = 'down' if connected else 'normal'
        self.connectBtn.text = 'DISCONNECT' if connected else 'CONNECT'
        self.btStatus.text = status
        self.connectLockout = not connected
        # PID controls must be relocked when connection is lost
        if (not connected):
            self.pidLocked = True

    def sendPID_pressed(self, save=False):
        self.btHandler.request_action(
            partial(self.btHandler.sendPID, self.kP, self.kI, self.kD, save))

    def pid_gui_update(self, kp: float, ki: float, kd: float, enable_input):
        self.kP = kp
        self.kI = ki
        self.kD = kd
        self.pidLocked = not enable_input
        print("unlocking pid")

    def enable_pressed(self, state):
        self.btHandler.request_action(
            partial(self.btHandler.set_enable, state == 'down'))

    def enable_gui_update(self, enabled):
        self.enableObj.state = 'down' if enabled else 'normal'

    def trim_changed(self, spinner: NumSpinner):
        self.trim = spinner.value
        self.btHandler.request_action(
            partial(self.btHandler.send_trim, self.trim))

    def set_slider(self, val: int):
        with self._joystick_lock:
            self._joystick_val = val

    def get_joystick(self) -> tuple[int, int]:
        with self._joystick_lock:
            return self._joystick_val, 0

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


if __name__ == "__main__":
    # Window.custom_titlebar = True
    Window.maximize()
    MainApp().run()
