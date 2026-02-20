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
        self.shoot.shooter_action(0.7)
        if self.shoot.check_shooter_velocity() == True:
            self.shoot.kick()
        else:
            self.shoot.stop_kicking()

    """
    Makes sure code is finished
    """
    def isFinished(self) -> bool:
        return True