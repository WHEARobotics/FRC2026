from dataclasses import dataclass

@dataclass(frozen=True)
class ShooterConstants:
    """ for the shooter """

    MOTOR_ID = 14
    KICKER_ID = 15

    SHOOTER_VELOCITY_MAX = -4590
    SHOOTER_VELOCITY_MIN = -4610