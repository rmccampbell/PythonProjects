#!/usr/bin/env python2
from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()

        self.environ = self.loader.loadModel("models/environment")
        self.environ.reparentTo(self.render)
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)

        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        self.pandaActor = Actor("models/panda-model",
                                {"walk": "models/panda-walk4"})
        self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.reparentTo(self.render)
        self.pandaActor.loop("walk")

        pandaPosInterval1 = self.pandaActor.posInterval(
            13, Point3(0, -10, 0), startPos=Point3(0, 10, 0))
        pandaPosInterval2 = self.pandaActor.posInterval(
            13, Point3(0, 10, 0), startPos=Point3(0, -10, 0))
        pandaHprInterval1 = self.pandaActor.hprInterval(
            13, Point3(180, 0, 0), startHpr=Point3(0, 0, 0))
        pandaHprInterval2 = self.pandaActor.hprInterval(
            13, Point3(0, 0, 0), startHpr=Point3(180, 0, 0))

        self.pandaPace = Sequence(pandaPosInterval1, pandaHprInterval1,
                                  pandaPosInterval2, pandaHprInterval2,
                                  name="pandaPace")
        self.pandaPace.loop()

    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

app = MyApp()
app.run()
