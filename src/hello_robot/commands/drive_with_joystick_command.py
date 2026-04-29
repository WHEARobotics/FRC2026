import commands2

from constants.driveconstants import DriveConstants
from subsystems.drive_subsystem import DriveSubsystem


class DriveWithJoystickCommand(
    commands2.Command
):  # Class type command from the library command2
    def __init__(
        self, drive: DriveSubsystem, drive_percent_fn: callable
    ):  # What value this needs to run
        super().__init__()
        self.drive_subsystem = drive  # Varible drive_subsystem is drive from __init__()
        self.drive_percent_fn = drive_percent_fn  # Same concept as above

        self.addRequirements(drive)  # Requires this subsystem

    def execute(self):  # What actions it does

        speed_divisor, rotation_divisor = (
            self.drive_subsystem.check_and_set_slow_mode()
        )
        
        x_speed, y_speed, rot_speed = (
            self.drive_percent_fn()
        )  # Set turn and drive speed to values got from function
        x_speed = x_speed * DriveConstants.MAX_SPEED_INCHES_PER_SECOND * -1 / speed_divisor
        y_speed = y_speed * DriveConstants.MAX_SPEED_INCHES_PER_SECOND * -1 / speed_divisor
        rot_speed = rot_speed * DriveConstants.MAX_DEGREES_PER_SECOND * -1 / rotation_divisor

        self.drive_subsystem.drive(
            x_speed=y_speed,
            y_speed=x_speed,
            rot_speed=rot_speed,
        )  # Give these values to drive function

    def isFinished(self):
        return False