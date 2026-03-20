import commands2
import commands2.cmd
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.units import inchesToMeters

from subsystems.drive_subsystem import DriveSubsystem
from subsystems.shooter_subsystem import ShooterSubsystem
from subsystems.intake_subsystem import IntakeSubsystem
# from subsystems.climb_subsystem import ClimbSubsystem
from commands.shoot_command import ShootCommand
from commands.intake_command import IntakeCommand
from commands.drive_to_goal import DriveToGoal
from commands.cough_command import CoughCommand



class Autos:

    def __init__(self):
        raise Exception
    
    @staticmethod
    def backward(drive: DriveSubsystem, shoot: ShooterSubsystem):
        return DriveToGoal(drive, Pose2d(inchesToMeters(-55), inchesToMeters(0.0), Rotation2d(0.0))) \
            .andThen(ShootCommand(shoot))
    
           # .andThen(print("Finished reverse")) \
            # .andThen(print("shooting!")) \
    
    def shoot(shoot: ShooterSubsystem, intake: IntakeSubsystem):
        
        return commands2.cmd.parallel(
            ShootCommand(shoot),
            IntakeCommand(intake),
        )
  

    # def climb(climb: ClimbSubsystem):

    #     return 
    
    
    # def shoot(shoot: ShooterSubsystem, intake: IntakeSubsystem):
         
    #     return commands2.cmd.parallel(
    #         ShootCommand(shoot),
    #         IntakeCommand(intake),
    #     )