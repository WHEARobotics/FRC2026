import wpilib
import commands2
from commands2.button import CommandXboxController
from wpimath import applyDeadband
from wpimath.geometry import Pose2d

from wpilib import SmartDashboard, SendableChooser


from constants.operatorinterfaceconstants import OperatorInterfaceConstants
from constants.visionconstant import VisionConstants

from subsystems.drive_subsystem import DriveSubsystem # doublecheck 
# from subsystems.shooter_subsystem import ShooterSubsystem
# from subsystems.intake_subsystem import IntakeSubsystem
from subsystems.vision_subsystem import VisionSubsystem


from commands.drive_with_joystick_command import DriveWithJoystickCommand
# from commands.shooter_idle_command import ShooterIdleCommand
# from commands.shoot_command import ShootCommand
from commands.reset_gyro_command import ResetGyroCommand # doublecheck
from commands.slow_mode_off_command import SlowModeOffCommand #doublecheck
from commands.slow_mode_on_command import SlowModeOnCommand # doublecheck
# from commands.intake_command import IntakeCommand
# from commands.intake_idle_command import IntakeIdleCommand
from commands.aim_at_hub_tag_command import AimAtHubTagCommand




class RobotContainer:
    def __init__(self):

        self.drive_subsystem = DriveSubsystem()
        # self.shooter_subsystem = ShooterSubsystem()
        # self.intake_subsystem = IntakeSubsystem()

        self.dr_controller = self._initialize_dr_controller()
        self.op_controller = self._initialize_op_controller()

        self._initialize_default_commands()

        self.vision = VisionSubsystem(
            add_vision_measurement_fn=self.drivetrain.add_vision_measurement
        # or lambda p, ts, std: self.drivetrain.odometry.addVisionMeasurement(p, ts, std)
        )

        wpilib.SmartDashboard.putString("Vision/Status", self.vision.debug_status())


    def _initialize_default_commands(self):
        teleop_command = DriveWithJoystickCommand(
            self.drive_subsystem, self.get_drive_value_from_joystick
        )
        self.drive_subsystem.setDefaultCommand(
            teleop_command
        )
        # self.shooter_subsystem.setDefaultCommand(
        #     ShooterIdleCommand(self.shooter_subsystem)
        # )
        # self.intake_subsystem.setDefaultCommand(
        #     IntakeIdleCommand(self.intake_subsystem)
        # )

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

        controller.a().whileTrue(AimAtHubTagCommand(self.vision, self.drivetrain))

        AUTOALIGN_X = 0
        AUTOALIGN_Y = 10
        AUTOALIGN_ANGLE = 45
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
        # controller.rightTrigger().whileTrue(
        #     ShootCommand(shoot = self.shooter_subsystem)
        # )
        # controller.leftTrigger().whileTrue(
        #     IntakeCommand(intake = self.intake_subsystem)
        # )


        return controller



