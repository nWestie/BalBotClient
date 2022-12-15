from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from random import randint


class PongBall(Widget):
    velY = NumericProperty(0)
    velX = NumericProperty(0)
    vel = ReferenceListProperty(velX, velY)

    def move(self):
        self.pos = Vector(*self.vel) + self.pos


class PongPlayer(Widget):

    score = NumericProperty(0)

    def bounceBall(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.vel
            # changes bounce angle if hit near edge
            offset = (ball.center_y-self.center_y)/(self.height/2)
            vel = 1.1 * Vector(-vx, vy)
            ball.vel = vel.x, vel.y + offset


class PongGame(Widget):
    ball = ObjectProperty(None)
    plr1 = ObjectProperty(None)
    plr2 = ObjectProperty(None)

    def update(self, dt):
        self.ball.move()

        self.plr1.bounceBall(self.ball)
        self.plr2.bounceBall(self.ball)
        
        if (self.ball.y < 0) or (self.ball.top > self.height):
            self.ball.velY *= -1
        if (self.ball.x < 0) or (self.ball.right > self.width):
            self.ball.velX *= -1

    def serveBall(self):
        self.ball.center = self.center
        self.ball.vel = Vector(4, 0).rotate(45)

    def on_touch_move(self, touch):
        if touch.x < self.width/3:
            self.plr1.center_y = touch.y
        if touch.x > self.width * 2/3:
            self.plr2.center_y = touch.y


class PongApp(App):
    def build(self):
        game = PongGame()
        game.serveBall()
        Clock.schedule_interval(game.update, 1.0/60.0)
        return game


if __name__ == '__main__':
    PongApp().run()
