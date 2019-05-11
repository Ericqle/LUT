from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.config import Config
import sys
from LUT import Lut


class LUTApp(App):
    from kivy.lang import Builder
    Builder.load_file('Default.kv')

    os = None
    if sys.platform == 'darwin':
        os = 'osx'
    elif sys.platform == 'win32' or sys.platform == 'win64':
        os = 'win32'

    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(Lut(name='lut'))
        screen_manager.get_screen('lut').set_os(self.os)
        return screen_manager


if __name__ == '__main__':
    Window.size = (750, 400)
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    Config.set('graphics', 'default_font', 'RobotoMono-Regular.ttf')
    LUTApp().run()
