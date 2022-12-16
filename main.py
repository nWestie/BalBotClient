from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, BoundedNumericProperty
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
    ball = ObjectProperty()
    plr1 = ObjectProperty()
    plr2 = ObjectProperty()

    def update(self, dt):
        self.ball.move()

        self.plr1.bounceBall(self.ball)
        self.plr2.bounceBall(self.ball)

        if (self.ball.y < 0) or (self.ball.top > self.height):
            self.ball.velY *= -1
            self.ball.vel = Vector(self.ball.velX, self.ball.velY)
        if (self.ball.x < 0):
            self.plr2.score *= 2
            self.serveBall((4, 0))
        if (self.ball.right > self.width):
            self.plr1.score += 1
            self.serveBall((-4, 0))

    def serveBall(self, vel=(4, 0)):
        self.ball.center = self.center
        self.ball.vel = vel

    def on_touch_move(self, touch):
        y = touch.y
        h2 = self.plr1.height / 2
        if (y + h2) > self.height:
            y = self.height-h2
        if (y - h2) < 0:
            y = 0+h2

        if touch.x < self.width/3:
            self.plr1.center_y = y
        if touch.x > self.width * 2/3:
            self.plr2.center_y = y


class PongApp(App):
    def build(self):
        game = PongGame()
        game.serveBall()
        Clock.schedule_interval(game.update, 1.0/60.0)
        return game


if __name__ == '__main__':
    PongApp().run()
