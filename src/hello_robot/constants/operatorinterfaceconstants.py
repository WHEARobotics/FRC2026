from dataclasses import dataclass
from wpilib import XboxController

@dataclass(frozen=True)
class OperatorInterfaceConstants:
    BUTTON_A: int = XboxController.Button.kA
    BUTTON_B: int = XboxController.Button.kB
    BUTTON_X: int = XboxController.Button.kX
    BUTTON_Y: int = XboxController.Button.kY

    BUMPER_RIGHT: int = XboxController.Button.kRightBumper
    BUMPER_LEFT: int = XboxController.Button.kLeftBumper

    LEFT_TRIGGER: int = XboxController.Axis.kLeftTrigger

    LEFT_JOYSTICK_PRESSED: int = XboxController.Button.kLeftStick
    RIGHT_JOYSTICK_PRESSED: int = XboxController.Button.kRightStick

    DRIVER_CONTROLLER_PORT: int = 0 # USB port number for the Xbox controller.
    OPERATOR_CONTROLLER_PORT: int = 1