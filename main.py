from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivymd.uix.button import MDFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton


class LoginScreen(MDWidget):
    pass


class MyToggle(MDFlatButton, MDToggleButton):
    pass


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style_switch_animation = True
        return LoginScreen()


if __name__ == "__main__":
    MainApp().run()
