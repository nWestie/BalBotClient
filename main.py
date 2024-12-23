import threading
from time import time
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


class Toggle(MDRectangleFlatButton, MDToggleButton):  # type:ignore
    pass


class MainGraph(Graph, MDWidget):  # type:ignore
    pass


class VoltGraph(Graph, MDWidget):  # type:ignore
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
    consoleText = StringProperty("Hello\nHello")
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
        self._joystick_val = 0
        self._joystick_lock: threading.Lock = threading.Lock()
        self.initGraphs()

    def connect_pressed(self, state):
        print(f"Connect pressed, state={state}")
        self.connectBtn.disabled = True
        if (state == 'down'):  # reqesting connect
            # reset variables
            self.trim = 0
            self.voltageText = ""
            self.consoleText = ""
            self.cleanup_graph_data(0)
            self.btHandler.request_action(self.btHandler.connect)

            Clock.schedule_interval(
                lambda dt: self.print_console(f"t={time():.2f}"), 1)
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

    def print_console(self, text: str):
        self.consoleText += "\n"
        self.consoleText += text
        # clip length of console
        # if self.consoleText.count('\n') > 30:
        #     lines = self.consoleText.splitlines(True)[-10:]
        #     self.consoleText = "".join(lines)

    def graph_gui_update(self, t: float, volt: float, set_angle: float, act_angle: float):
        self.volt_plot.points.append((t, volt))
        self.set_angle_plot.points.append((t, set_angle))
        self.act_angle_plot.points.append((t, act_angle))
        self.voltageText = f"{volt:.2f}V"
        # Scroll Graphs if needed
        if t + .5 > self.voltGraph.xmax:
            max = t + .5
            min = t - 14.5
            self.voltGraph.xmin = min
            self.voltGraph.xmax = max
            self.mainGraph.xmin = min
            self.mainGraph.xmax = max
        if (len(self.volt_plot.points) > 600):
            self.cleanup_graph_data(15*20)

    def cleanup_graph_data(self, keep_count):
        if (keep_count == 0):
            self.volt_plot.points = []
            self.set_angle_plot.points = []
            self.act_angle_plot.points = []
        self.volt_plot.points = self.volt_plot.points[-keep_count:]
        self.set_angle_plot.points = self.set_angle_plot.points[-keep_count:]
        self.act_angle_plot.points = self.act_angle_plot.points[-keep_count:]

    def initGraphs(self):
        self.volt_plot = MeshLinePlot(color=[1, 0, 0, 1])
        # self.voltLine.points = [(x/20, .1) for x in range(300)]
        self.voltGraph = VoltGraph()
        self.voltGraph.add_plot(self.volt_plot)
        self.graphStack.add_widget(self.voltGraph)
        self.set_angle_plot = MeshLinePlot(color=[1, 1, 0, 1])
        # self.setDegLine.points = [(x/20, 90) for x in range(300)]
        self.act_angle_plot = MeshLinePlot(color=[1, 0, 0, 1])
        # self.actDegLine.points = [(x/20, 0) for x in range(300)]
        self.mainGraph = MainGraph()
        self.mainGraph.add_plot(self.set_angle_plot)
        self.mainGraph.add_plot(self.act_angle_plot)
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