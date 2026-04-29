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
from wpilib.shuffleboard import Shuffleboard
from util.current_threshold import CurrentThreshold

from constants.newtypes import percentage, inches_per_second

from constants.climbconstants import ClimbConstants


class ClimbSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()
        self.current_threshold = CurrentThreshold("Elevator Motor", ClimbConstants.STOP_CURRENT)
    
        self.climb_motor = TalonFX(ClimbConstants.MOTOR_ID)

        self.climb_motor.configurator.apply(self._configure_climb_motor())
        
        self.panic_stop = False
        self.initialized = False

        self.position_request = PositionVoltage(0).with_slot(0)

        self.robot_tab = Shuffleboard.getTab("Robot System")

        self.at_goal_entry = self.robot_tab.add("At goal", self.is_at_goal()).withPosition(7, 3).getEntry()
        self.current_height_entry = self.robot_tab.add("Current Height inch", self.get_current_height_inches()).withPosition(8, 1).getEntry()

    def periodic(self):
        self.at_goal_entry.setBoolean(self.is_at_goal())
        self.current_height_entry.setFloat(self.get_current_height_inches())

    def climb(self, speed: percentage):
        self.climb_motor.set(speed)

    def stop(self):
        self.climb_motor.stopMotor()

    def set_goal_height_inches(self, height: inches):
        """Set the goal in inches that the elevator drives toward"""
        # Convert because internally, we use rotations.
        self.goal_pos = self._inches_to_motor_rot(height)

    def get_current_goal_pos_inches(self):
        return self._motor_rot_to_inches(self.goal_pos)
        

    def get_current_height_inches(self) -> inches:
        """Get the current height of the elevator in inches"""
        return self._motor_rot_to_inches(self.climb_motor.get_position().value)

    def move_to_goal(self):
        """Move toward the goal position"""
        motor_current = self.climb_motor.get_stator_current().value
        if self.initialized:
            motor_duty = self.climb_motor.get_duty_cycle().value
            

            if (self.current_threshold.is_exceeded(motor_current) and motor_duty < -0.05) or (self.get_current_height_inches() >= ClimbConstants.TOP_HEIGHT_LIMIT and motor_duty > 0.05):
                print("Panick Stop!!")
                self.climb_motor.set(0.0)
                self.panic_stop = True
            else:
                self.climb_motor.set_control(
                    self.position_request.with_position(self.goal_pos)
                )
        else:
            # If not initialized, move downward slowly to find the bottom.
            self.climb_motor.set(-0.1)
            if self.current_threshold.is_exceeded(motor_current):
                self.climb_motor.set(0.0)
                rotations = self._inches_to_motor_rot(ClimbConstants.BASE_HEIGHT)
                self.climb_motor.set_position(rotations, timeout_seconds=10.0)
                self.initialized = True

    def initialized_and_stop(self):
        motor_current = self.climb_motor.get_stator_current().value
        if self.initialized:
            self.stop()
            
        else:
            # If not initialized, move downward slowly to find the bottom.
            self.climb_motor.set(-0.1)
            if self.current_threshold.is_exceeded(motor_current):
                self.climb_motor.set(0.0)
                rotations = self._inches_to_motor_rot(ClimbConstants.BASE_HEIGHT)
                self.climb_motor.set_position(rotations, timeout_seconds=10.0)
                self.initialized = True

    def is_at_goal(self):
        return self.panic_stop


    @staticmethod
    def _motor_rot_to_inches(rot: float) -> inches:
        return (
            rot * ClimbConstants.SCREW_INCHES_PER_ROT / ClimbConstants.GEAR_RATIO
        )
    
    @staticmethod
    def _inches_to_motor_rot(height: inches) -> float:
        return (
            height / ClimbConstants.SCREW_INCHES_PER_ROT
            * ClimbConstants.GEAR_RATIO
        )

    @staticmethod
    def _configure_climb_motor() -> TalonFXConfiguration:
        configuration = TalonFXConfiguration()

        configuration.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
        configuration.motor_output.neutral_mode = NeutralModeValue.BRAKE

        configuration.slot0.k_p = (
            1.6
        )
        configuration.slot0.k_i = 0.0
        configuration.slot0.k_d = 0.0

        return configuration