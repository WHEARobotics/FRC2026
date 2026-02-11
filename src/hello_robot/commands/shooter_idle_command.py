# import commands2

# from subsystems.shooter_subsystem import ShooterSubsystem


# class ShooterIdleCommand(commands2.Command):   
#     """
#     Shooter go Pew PEW
#     """

#     def __init__(self, shoot: ShooterSubsystem):
#         super().__init__()

#         self.shoot = shoot
#         self.addRequirements(shoot)

#     def execute(self):
#         self.shoot.shooter_stop() 

#     """
#     Makes sure code is finished
#     """
#     def isFinished(self) -> bool:
#         return False
    
#     def end(self, interrupted: bool):
#         # Since this is the default command, it should only end if it is interrupted.
#         pass