import commands2
from subsystems.drive_subsystem import DriveSubsystem

class SlowModeOnCommand(commands2.Command):
    """
    Class used to turn on slow mode
    uses driveSubsystem_init to use variables
    """
    def __init__(self, drive: DriveSubsystem):
        super().__init__()
        self.drive = drive
        self.addRequirements(drive)

    """
    Turns on slow mode
    """
    def execute(self):
        self.drive.slow_mode = True

    """
    Makes sure code is finished
    """
    def isFinished(self) -> bool:
        return True