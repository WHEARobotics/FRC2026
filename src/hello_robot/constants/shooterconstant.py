from dataclasses import dataclass

@dataclass(frozen=True)
class ShooterConstants:
    """ for the shooter """

    MOTOR_ID = 14
    KICKER_ID = 15

    #-3960
    SHOOTER_VELOCITY_MAX = -430
    0
    SHOOTER_VELOCITY_MIN = -4350