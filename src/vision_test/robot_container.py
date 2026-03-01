import wpilib
import commands2
from commands2.button import CommandXboxController
from wpimath import applyDeadband
from wpimath.geometry import Pose2d

from wpilib import SmartDashboard, SendableChooser
from wpilib.shuffleboard import Shuffleboard

from constants.operatorinterfaceconstants import OperatorInterfaceConstants
from constants.visionconstant import VisionConstants

from subsystems.vision_subsystem import VisionSubsystem

from commands.aim_at_hub_tag_command import AimAtHubTagCommand




class RobotContainer:
    def __init__(self):

    
        self.vision_subsystem = VisionSubsystem(None)

        self.dr_controller = self._initialize_dr_controller()


    
    def _initialize_dr_controller(self):
        """initialize the driver controller"""
        controller = CommandXboxController(
            OperatorInterfaceConstants.DRIVER_CONTROLLER_PORT
        )

        controller.a().onTrue(AimAtHubTagCommand(vision = self.vision_subsystem))

        return controller



