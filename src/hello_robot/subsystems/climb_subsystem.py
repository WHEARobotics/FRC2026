import commands2
import wpimath
from phoenix6.controls import PositionVoltage, NeutralOut
from phoenix6.hardware.talon_fx import TalonFX
from phoenix6.configs import TalonFXConfiguration
from phoenix6.signals import InvertedValue, NeutralModeValue
from wpimath.geometry import Rotation2d
from wpimath.units import degrees, meters, inches, meters_per_second
from wpimath.units import (
    metersToInches,
    inchesToMeters,
    degreesToRotations,
    rotationsToDegrees,
)

import wpilib 

from constants.newtypes import percentage, inches_per_second

from constants.climbconstants import ClimbConstants


class ClimbSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()
    
        self.climb_motor = TalonFX(ClimbConstants.MOTOR_ID)

    def climb(self, speed: percentage):
        self.climb_motor.set(speed)

    def stop(self):
        self.climb_motor.stopMotor()
