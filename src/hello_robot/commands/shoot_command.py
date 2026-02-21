import commands2

from subsystems.shooter_subsystem import ShooterSubsystem


class ShootCommand(commands2.Command):   
    """
    Shooter go Pew PEW
    """

    def __init__(self, shoot: ShooterSubsystem):
        super().__init__()

        self.shoot = shoot
        self.addRequirements(shoot)

    def execute(self):
        
        self.shoot.shooter_action(-0.6)
        self.shoot.check_shooter_velocity()
        if self.shoot.check_shooter_velocity() == True:
            self.shoot.kick()
        elif self.shoot.check_shooter_velocity() == False:
            self.shoot.stop_kicking()

    """
    Makes sure code is finished
    """
    def isFinished(self) -> bool:
        return False