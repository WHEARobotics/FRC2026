# import rev
# import wpilib
# import commands2

# from constants.shooterconstants import ShooterConstants
# from constants.new_types import inches_per_second, degrees_per_second, percentage


# class ShooterSubsystem(commands2.subsystem):
#     def __init__(self):
#         super().__init__()

#         self.shooter_motor = rev.SparkMax(ShooterConstants.MOTOR, rev.SparkMax.MotorType.kBrushless)

#     def shooter_action(self, speed: percentage) -> None:
#         self.shooter_motor.set(speed)

#     def shooter_stop(self) -> None:
#         self.shooter_motor.set(0.0)




