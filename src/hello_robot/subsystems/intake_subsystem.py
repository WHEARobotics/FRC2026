import rev
import wpilib
import commands2
from wpilib import SmartDashboard
from wpilib.shuffleboard import Shuffleboard
from constants.intakeconstants import IntakeConstants
from constants.newtypes import inches_per_second, degrees_per_second, percentage


class IntakeSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()

        self.intake_motor = rev.SparkMax(IntakeConstants.MOTOR_ID, rev.SparkFlex.MotorType.kBrushless)

        self.robot_tab = Shuffleboard.getTab("Robot System")

        self.motor_temp_entry = self.robot_tab.add("Intake Temp C", self.get_intake_temp()).withPosition(7, 2).getEntry()

    def intake_action(self, speed: percentage) -> None:
        self.intake_motor.set(speed)

    def intake_stop(self) -> None:
        self.intake_motor.stopMotor()

    def get_intake_temp(self) -> float:
        return self.intake_motor.getMotorTemperature()
    
    def periodic(self):
        self.motor_temp_entry.setFloat(self.get_intake_temp())
        SmartDashboard.putNumber("Intake Temp C", self.get_intake_temp())

    



