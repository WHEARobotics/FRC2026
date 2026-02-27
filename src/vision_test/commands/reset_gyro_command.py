import commands2

from subsystems.drive_subsystem import DriveSubsystem

"""
class used to reset the gyro on the motors
"""
class ResetGyroCommand(
    commands2.Command
):  # Class type command from the library command2
    def __init__(self, drive_subsystem: DriveSubsystem):
        super().__init__()
        self.drive_subsystem = drive_subsystem

        self.addRequirements(drive_subsystem)  # Requires this subsystem

    """
    Executes code and resets gyro's set_yew to 0.0
    """
    def execute(self):
        print("reset gyro")
        self.drive_subsystem.gyro.set_yaw(0.0)
    """
    makes sure the code doesnt keep reseting the gyro
    """
    def isFinished(self) -> bool:
        return True