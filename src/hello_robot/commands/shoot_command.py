# import commands2

# from subsystems.shooter_subsystem import ShooterSubsystem


# class ShootCommand(commands2.Command):   
#     """
#     Shooter go Pew PEW
#     """

#     def __init__(self, shoot: ShooterSubsystem):
#         super().__init__()

#         self.shoot = shoot
#         self.addRequirements(shoot)

#     def execute(self):
#         self.shoot.shooter_action(0.4)

#     """
#     Makes sure code is finished
#     """
#     def isFinished(self) -> bool:
#         return True