import commands2
from subsystems.intake_subsystem import IntakeSubsystem

class IntakeCommand(commands2.Command):

    """Command for intake mechanism"""

    def __init__(self, intake: IntakeSubsystem):
        super().__init__()

        self.intake = intake
        self.addRequirements(intake)

    def execute(self):
        self.intake.intake_action(-0.3)

    def isFinished(self) -> bool:
        return False