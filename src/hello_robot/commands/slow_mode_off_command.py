import commands2
from subsystems.drive_subsystem import DriveSubsystem

class SlowModeOffCommand(commands2.Command):
    """
    Code used to turn off slow mode
    adds driveSubsystem_init code to use variables
    """
    def __init__(self, drive: DriveSubsystem):
        super().__init__()
        self.drive = drive
        self.addRequirements(drive)

    """
    turns off slow mode
    """
    def execute(self):
        self.drive.slow_mode = False

    """
    Makes sure code is finished
    """
    def isFinished(self) -> bool:
        return True