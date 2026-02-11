from dataclasses import dataclass
from wpimath.units import metersToInches

from constants.new_types import (
    inches_per_second,
    inches,
    degrees_per_second,
    degrees,
    inches_per_second_squared,
    degrees_per_second_squared,
)


@dataclass(frozen=True)
class DriveConstants:
    """Drivetrain related constants"""

    # CANcoder CAN bus IDs
    CAN_FR = 11 
    CAN_FL = 8
    CAN_BL = 5
    CAN_BR = 2

    # CANcoder (magnet) offsets in rotations that we got from the CANcoder using Phoenix Tuner X 
    # Not really needed
    BR_OFFSET = -0.245361  # -0.242
    BL_OFFSET = -0.180176 # -0.175
    FR_OFFSET = 0.031738 # 0.033
    FL_OFFSET = -0.096680  # -0.081

    # Kraken IDs
    DRIVE_FR = 12
    DRIVE_FL = 9
    DRIVE_BL = 6
    DRIVE_BR = 3

    TURN_FR = 10
    TURN_FL = 7
    TURN_BL = 4
    TURN_BR = 1

    # Pigeon2 gyro CAN bus ID
    PIGEON_ID = 13

    # Drivetrain geometry, gearing, etc.
    TRACK_HALF_WIDTH: inches = metersToInches(0.27) # meters 
    WHEELBASE_HALF_LENGTH: inches = metersToInches(0.27)
    TURN_GEAR_RATIO = 468.0/35.0 #10 pinion gear
    DRIVE_GEAR_RATIO = 6.2 #11 pinion gear
    WHEEL_DIA: inches = 4 # 4" diameter

    WHEEL_RADIUS: inches = WHEEL_DIA / 2

    FREE_SPEED = 3.76 # max








    MAX_SPEED_INCHES_PER_SECOND: inches_per_second = (
        145.7 
    )
    MAX_DEGREES_PER_SECOND: degrees_per_second = (
        72.85
    ) # degrees per second






    PIDX_KP: float = 1.0 * 0.9592
    PIDY_KP: float = 1.0 * 0.9592 
    PID_ROT_KP: float = 1.0 / 90.0


    HORIZ_MAX_V: inches_per_second = 39.0
    HORIZ_MAX_A: inches_per_second_squared = (
        78.0 * 1.5
    )
    HORIZ_POS_TOL: inches = (
        4.0
    )
    HORIZ_VEL_TOL: inches_per_second = 0.4


    ROT_MAX_V: degrees_per_second = (
        40.0
    )
    ROT_MAX_A: degrees_per_second_squared = (
        20.0
    )
    ROT_POS_TOL: degrees = 5.0
    ROT_VEL_TOL: degrees_per_second = (
        1.0
    )