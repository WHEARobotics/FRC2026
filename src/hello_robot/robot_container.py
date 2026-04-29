import commands2
from commands2.button import CommandXboxController
from wpimath import applyDeadband
from wpimath.geometry import Pose2d

from commands.autonomous_commands import Autos
from wpilib import SmartDashboard, SendableChooser

from constants.autoconsts import AutoConsts
from constants.operatorinterfaceconstants import OperatorInterfaceConstants
from constants.climbconstants import ClimbConstants

from subsystems.drive_subsystem import DriveSubsystem # doublecheck 
from subsystems.shooter_subsystem import ShooterSubsystem
from subsystems.intake_subsystem import IntakeSubsystem
from subsystems.climb_subsystem import ClimbSubsystem


from commands.drive_with_joystick_command import DriveWithJoystickCommand
from commands.shooter_idle_command import ShooterIdleCommand
from commands.shoot_command import ShootCommand
from commands.reset_gyro_command import ResetGyroCommand # doublecheck
from commands.slow_mode_off_command import SlowModeOffCommand #doublecheck
from commands.slow_mode_on_command import SlowModeOnCommand # doublecheck
from commands.intake_command import IntakeCommand
from commands.intake_idle_command import IntakeIdleCommand
from commands.cough_command import CoughCommand
from commands.choking_command import ChokingCommand
from commands.climb_down_command import ClimbDownCommand
from commands.climb_command import ClimbToGoalCommand
from commands.climb_up_command import ClimbUpCommand
from commands.climb_idle_command import ClimbIdleCommand




class RobotContainer:
    def __init__(self):

        self.drive_subsystem = DriveSubsystem()
        self.shooter_subsystem = ShooterSubsystem()
        self.intake_subsystem = IntakeSubsystem()
        self.climb_subsystem = ClimbSubsystem()

        self.dr_controller = self._initialize_dr_controller()
        self.op_controller = self._initialize_op_controller()

        self._initialize_default_commands()

        self.auto_chooser = self._initialize_shuffleboard()
        # Add chooser to SmartDashboard
        SmartDashboard.putData("Auto Command Selector", self.auto_chooser)


    def _initialize_default_commands(self):
        teleop_command = DriveWithJoystickCommand(
            self.drive_subsystem, self.get_drive_value_from_joystick
        )
        self.drive_subsystem.setDefaultCommand(
            teleop_command
        )
        self.shooter_subsystem.setDefaultCommand(
            ShooterIdleCommand(self.shooter_subsystem)
        )
        self.intake_subsystem.setDefaultCommand(
            IntakeIdleCommand(intake = self.intake_subsystem)
        )
        self.climb_subsystem.setDefaultCommand(
            ClimbIdleCommand(climb = self.climb_subsystem)
        )

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
    
    def _initialize_op_controller(self):
        """initialize the operator controller"""
        controller = CommandXboxController(
            OperatorInterfaceConstants.OPERATOR_CONTROLLER_PORT
        )
        controller.rightTrigger().whileTrue(
            ShootCommand(shoot = self.shooter_subsystem)
        )
        controller.leftTrigger().whileTrue(
            IntakeCommand(intake = self.intake_subsystem)
        )
        controller.rightBumper().onTrue(
            CoughCommand(shoot = self.shooter_subsystem)
        )
        controller.leftBumper().whileTrue(
            ChokingCommand(intake = self.intake_subsystem)
        )
        controller.leftStick().onTrue( 
            ClimbToGoalCommand(goal = ClimbConstants.TOP_HEIGHT, climb = self.climb_subsystem)
        )
        controller.rightStick().whileTrue(
            ClimbDownCommand(climb = self.climb_subsystem)
        )
        

        


        return controller
    
    @staticmethod
    def _initialize_shuffleboard():
        # Auto chooser
        auto_chooser = SendableChooser()
        auto_chooser.setDefaultOption("Backwards", AutoConsts.BACKWARD)
        
        # Add options
        auto_chooser.addOption("Shoot", AutoConsts.SHOOT)
        return auto_chooser

    def get_auto_command(self) -> commands2.Command:
        auto_reader = self.auto_chooser.getSelected()

        if (
            auto_reader == AutoConsts.BACKWARD
        ):  # checks which Autonomous command is being used
            return Autos.backward(self.drive_subsystem, self.shooter_subsystem, self.intake_subsystem)
        elif auto_reader == AutoConsts.SHOOT:
            return Autos.shoot(self.shooter_subsystem, self.intake_subsystem)
       