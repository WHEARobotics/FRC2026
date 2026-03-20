import commands2

from subsystems.shooter_subsystem import ShooterSubsystem

class CoughCommand(commands2.Command):
    def __init__(self, shoot: ShooterSubsystem):
        super().__init__()

        self.shoot = shoot
        self.addRequirements(shoot)

    def execute(self):
        
        self.shoot.kick_cough()

    def isFinished(self) -> bool:
        return True
        