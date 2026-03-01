from typing import Optional
import wpilib

import commands2.command
from commands2 import CommandScheduler

import robot_container 

class Robot(wpilib.TimedRobot):
    def __init__(self):
        super().__init__()

        self.container = robot_container.RobotContainer()
        self.autonomous_command: Optional[commands2.Command] = None
        if Robot.isReal():
            print("Robot is real")
        else:
            print("Robot is not real")

        wpilib.CameraServer.launch()



    def robotPeriodic(self):
        CommandScheduler.getInstance().run()


    def autonomousInit(self):
        pass

    

    def disabledPeriodic(self):
        pass



    def teleopInit(self):

        CommandScheduler.getInstance().cancelAll()

    def disabledInit(self):
        pass
    


    def testInit(self):
        CommandScheduler.getInstance().cancelAll