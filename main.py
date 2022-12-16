from kivy.app import App
from kivy.uix.gridlayout import GridLayout


class LoginScreen(GridLayout):
    pass

class MainApp(App):
    def build(self):
        return LoginScreen()


if __name__ == "__main__":
    MainApp().run()
