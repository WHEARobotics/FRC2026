import commands2
from subsystems.intake_subsystem import IntakeSubsystem

class IntakeIdleCommand(commands2.Command):
    """Tam made me do it"""

    def __init__(self, intakeIdle: IntakeSubsystem ):
        super().__init__()

        self.IntakeIdle = intakeIdle
        self.addRequirements(intakeIdle)

    def execute(self):
        self.intake_stop()
        
    def isFinished(self) -> bool:
        return False