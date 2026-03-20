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

    def initialize(self):
        print("Shooting")

    def execute(self):
        
        self.shoot.shooter_action(-0.65)
        self.shoot.check_shooter_velocity()
        if self.shoot.check_shooter_velocity() == True:
            self.shoot.kick()
        else:
            self.shoot.stop_kicking()

        # elif self.shoot.check_shooter_velocity() == False:

    """
    Makes sure code is finished
    """
    def isFinished(self) -> bool:
        return False