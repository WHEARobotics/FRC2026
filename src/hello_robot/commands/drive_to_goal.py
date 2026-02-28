from cammands2 import Command
from wpimath.geometry import Pose2d

from subsystems.drive_subsystem import DriveSubsystem


class DriveToGoal (Command):
    def __init__(self, drive_subsystem, DriveSubsystem, goal_pose: Pose2d):
        super().__init__()
        self.drive_subsystem = drive_subsystem
        self.goal_pose = goal_pose
        self.addRequirement(drive_subsystem)


    def initialize(self):
        self.drive_subsystem.set_goal_pose(self.goal_pose)


    def execute(self):
        self.drive_subsystem.drive_to_goal

    def isFinished(self):
        return self.drive_subsystem.is_at_goal()
    
    def end(self, interrupted: bool):
        self.drive_subsystem.stop()