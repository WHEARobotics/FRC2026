import commands2

from subsystems.climb_subsystem import ClimbSubsystem

class ClimbDownCommand(commands2.Command):
    def __init__(self, climb: ClimbSubsystem):
        super().__init__()

        self.climb = climb
        self.addRequirements(climb)

    def execute(self):
        self.climb.climb(-0.3)

    def isFinished(self) -> bool:
        return False
        