import rev
import wpilib
import commands2

from wpilib import SmartDashboard
from constants.shooterconstant import ShooterConstants
from constants.new_types import inches_per_second, degrees_per_second, percentage


class ShooterSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()

        self.shooter_motor = rev.SparkFlex(ShooterConstants.MOTOR_ID, rev.SparkFlex.MotorType.kBrushless)
        self.kicker_motor = rev.SparkMax(ShooterConstants.KICKER_ID, rev.SparkMax.MotorType.kBrushless)

        self.shooter_motor_encoder = self.shooter_motor.getEncoder()

    def shooter_action(self, speed: percentage) -> None:
        self.shooter_motor.set(speed)

    def shooter_stop(self) -> None:
        self.shooter_motor.stopMotor()

    def get_shooter_velocity(self):
        return self.shooter_motor_encoder.getVelocity()

    def check_shooter_velocity(self) -> bool:
        if self.get_shooter_velocity() > ShooterConstants.SHOOTER_VELOCITY_MIN and self.get_shooter_velocity() < ShooterConstants.SHOOTER_VELOCITY_MAX:
            return True
        else:
            return False
    
    def kick(self) -> None:
        self.kicker_motor.set(0.1)
    
    def stop_kicking(self) -> None:
        self.kicker_motor.stopMotor()

    def periodic(self):
        SmartDashboard.putNumber("Shooter Velocity", self.get_shooter_velocity())
        SmartDashboard.putBoolean("Velocity", self.check_shooter_velocity())
