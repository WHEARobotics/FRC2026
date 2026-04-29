from dataclasses import dataclass

@dataclass(frozen=True)
class ClimbConstants:

    MOTOR_ID = 16

    SCREW_INCHES_PER_ROT = 1.0
    GEAR_RATIO = 9

    BASE_HEIGHT = 0.0
    TOP_HEIGHT = 7.8

    STOP_CURRENT = 28
    TOP_HEIGHT_LIMIT = 7.9