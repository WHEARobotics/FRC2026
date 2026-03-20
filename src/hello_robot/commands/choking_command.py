# fuel getting stuck in hopper - make command to reverse intake
# we have a cough command so i'm calling this choke for now :)


import commands2

from subsystems.intake_subsystem import IntakeSubsystem

class ChokingCommand(commands2.Command):
    def __init__(self, intake: IntakeSubsystem):
        super().__init__()
    
        self.intake = intake
        self.addRequirements(intake)

    def execute(self):
        self.intake.intake_action(0.25)

    def isFinished(self) -> bool:
        return False
