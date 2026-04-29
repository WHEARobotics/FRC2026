import commands2
from subsystems.climb_subsystem import ClimbSubsystem

class ClimbIdleCommand(commands2.Command):

    def __init__(self, climb: ClimbSubsystem):
        super().__init__()

        self.climb = climb
        self.addRequirements(climb)

    def initialize(self):
        self.climb.initialized_and_stop()

    def execute(self):
        self.climb.stop()

    def isFinished(self) -> bool:
        return False
