import commands2
import commands2.cmd
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.units import inchesToMeters

from subsystems.drive_subsystem import DriveSubsystem
from commands.drive_to_goal import DriveToGoal



class Autos:

    def __init__(self):
        raise Exception
    
    @staticmethod
    def forward(drive: DriveSubsystem):
        return DriveToGoal(drive, Pose2d(inchesToMeters(92), inchesToMeters(0.0), Rotation2d(0.0)))