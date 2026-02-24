import rev
import wpilib
import commands2

from constants.intakeconstants import IntakeConstants
from constants.new_types import inches_per_second, degrees_per_second, percentage


class IntakeSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()

        self.intake_motor = rev.SparkMax(IntakeConstants.MOTOR_ID, rev.SparkFlex.MotorType.kBrushless)

    def intake_action(self, speed: percentage) -> None:
        self.intake_motor.set(speed)

    def intake_stop(self) -> None:
        self.intake_motor.stopMotor()



