import commands2
from subsystems.intake_subsystem import IntakeSubsystem

class IntakeIdleCommand(commands2.Command):
    """Tam made me do it"""

    def __init__(self, intake: IntakeSubsystem):
        super().__init__()

        self.intake = intake
        self.addRequirements(intake)

    def execute(self):
        self.intake.intake_stop()
        
    def isFinished(self) -> bool:
        return False