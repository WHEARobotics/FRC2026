import wpilib
import commands2
from commands2.button import CommandXboxController
from wpimath import applyDeadband
from wpimath.geometry import Pose2d

from wpilib import SmartDashboard, SendableChooser
from wpilib.shuffleboard import Shuffleboard

from constants.operatorinterfaceconstants import OperatorInterfaceConstants
from constants.driveconstants import DriveConstants

from subsystems.drive_subsystem import DriveSubsystem

from commands.aim_at_hub_tag_command import AimAtHubTagCommand
from commands.reset_gyro_command import ResetGyroCommand 
from commands.slow_mode_off_command import SlowModeOffCommand 
from commands.slow_mode_on_command import SlowModeOnCommand 




class RobotContainer:
    def __init__(self):

    
        self.drive_subsystem = DriveSubsystem(None)

        self.dr_controller = self._initialize_dr_controller()

    def get_drive_value_from_joystick(self) -> tuple[float, float, float]:
        """  
        Gets joystick values and scales them for improved operator control.
        Returns:
            Tuple of perentage values in the three joystick axes, leftX, leftY, rightX.
        """
        x_percent = applyDeadband(
            value=self.dr_controller.getLeftX(), deadband=0.1
        )
        y_percent = applyDeadband(value=self.dr_controller.getLeftY(), deadband=0.1)
        rot_percent = applyDeadband(value=self.dr_controller.getRightX(), deadband=0.1)

        x_percent = self.joystick_scaling(x_percent)
        y_percent = self.joystick_scaling(y_percent)
        rot_percent = self.joystick_scaling(rot_percent)
        return(
            x_percent,
            y_percent,
            rot_percent,
        )
    
    @staticmethod 
    def joystick_scaling(
        input,
    ):
        a = 1
        output = a * input * input * input + (1 - a) * input
        return output
    
    def _initialize_dr_controller(self):
        """initialize the driver controller"""
        controller = CommandXboxController(
            OperatorInterfaceConstants.DRIVER_CONTROLLER_PORT
        )
        
        controller.y().onTrue(SlowModeOffCommand(drive = self.drive_subsystem))
        controller.x().onTrue(SlowModeOnCommand(drive = self.drive_subsystem))

        controller.leftBumper().and_(controller.rightBumper()).whileTrue(
            ResetGyroCommand(self.drive_subsystem)
        )

        return controller
    
    def _initialize_dr_controller(self):
        """initialize the driver controller"""
        controller = CommandXboxController(
            OperatorInterfaceConstants.DRIVER_CONTROLLER_PORT
        )

        controller.a().onTrue(AimAtHubTagCommand(drivetrain = self.drive_subsystem))

        return controller



