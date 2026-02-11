import wpimath
from phoenix6.controls import PositionVoltage, NeutralOut
from phoenix6.hardware import CANcoder
from phoenix6.hardware.talon_fx import TalonFX
from phoenix6.configs import TalonFXConfiguration
from phoenix6.signals import InvertedValue, NeutralModeValue
from wpimath.geometry import Rotation2d
from wpimath.kinematics import SwerveModulePosition, SwerveModuleState
from wpimath.units import degrees, meters, inches, meters_per_second
from wpimath.units import (
    metersToInches,
    inchesToMeters,
    degreesToRotations,
    rotationsToDegrees,
)

import wpilib 

from constants.driveconstants import DriveConstants
from constants.new_types import percentage, inches_per_second


def _calc_drive_effort(speed: inches_per_second) -> percentage:
    drive_effort = speed / DriveConstants.MAX_SPEED_INCHES_PER_SECOND
    drive_effort_clamped = max(min(drive_effort, 1.0), -1.0)
    return percentage(drive_effort_clamped)


class SwerveModule: 
    def __init__(
        self,
        name: str,
        drive_motor_bus_id: int,
        turn_motor_bus_id: int,
        cancoder_bus_id: int,
        offset_rotations: float,
    ):
        """
        
        :param name:
        :param drive_motor_bus_id:
        :param turn_motor_bus_id:
        :param cancoder_bus_id:
        :param offset_rotations: Range is [-1,1] and is in rotations, not degrees
        """

        # Needed for outputting to NetworkTables in periodic() fn (whassat mean)
        self.name = name
        self.drive_motor = TalonFX(drive_motor_bus_id)
        self.turn_motor = TalonFX(turn_motor_bus_id)
        self.can_coder = CANcoder(cancoder_bus_id) # ID number

        self.turn_motor.configurator.apply(self._configure_turn_motor())
        self.drive_motor.configurator.apply(self._configure_drive_motor())

        


        self.brake_request = NeutralOut()


        self.position_request = PositionVoltage(0).with_slot(0)



        self.drive_motor.set_position(0.0)




        self.rotation_offset_degrees = rotationsToDegrees(offset_rotations)





        steering_position_rotations = self._get_can_coder_pos_normalized()
        self.turn_motor.set_position(
            steering_position_rotations * DriveConstants.TURN_GEAR_RATIO
        )

        # ----------------------
        # public methods
        # ----------------------


    def set_drive_effort(self, speed_pct: percentage):
        self.drive_motor.set(speed_pct)
        



    def set_turn_effort(self, speed_pct: percentage):
        self.turn_motor.set(speed_pct)

        





    def set_turn_angle(self, angle_degrees: degrees):
        steering_rotation = degreesToRotations(
            angle_degrees
        )  # translate from degrees to rotation for motor


        self.turn_motor.set_control(
            self.position_request.with_position(
                steering_rotation * DriveConstants.TURN_GEAR_RATIO
            )
        )  # ??? yeah me too???

    def get_turn_angle_degrees(self) -> degrees:
        """
            returns the current turn angle of the module in degrees.
            retuns:
                Turn angle normalized to the range [-180, 180]
        """
        normalized_rotations = self._get_can_coder_pos_normalized() # Range form 0 to 1
        _degrees = normalized_rotations * 360
            # convert to [-180, 180] range
        if _degrees > 180:  
            _degrees = _degrees - 360
        return _degrees
    
    def get_state(self) -> SwerveModuleState:
        """
        Get the current state of the module
        Returns:
            Current state (speed and angle)
        """



        wheel_rps = (
            self.drive_motor.get_velocity().value / DriveConstants.DRIVE_GEAR_RATIO
        ) # wheel rotations per second
        speed_mps: meters_per_second = inchesToMeters(
            self._inches_per_rotation() * wheel_rps
        )


        angle = wpimath.geometry.Rotation2d().fromDegrees(self.get_turn_angle_degrees())
        return wpimath.kinematics.SwerveModuleState(speed_mps, angle)
    

    def get_position(self) -> SwerveModulePosition:
        """   
        Get the "position" of the swerve module
        Returns:
            Current positions (total wheel distance traveled and module angle)
        """




        wheel_rotations = (
            self.drive_motor.get_position().value / DriveConstants.DRIVE_GEAR_RATIO
        )
        wheel_distance: meters = inchesToMeters(
            self._inches_per_rotation() * wheel_rotations
        )
        angle: Rotation2d = Rotation2d.fromDegrees(self.get_turn_angle_degrees())

        return SwerveModulePosition(wheel_distance, angle)
    
    def periodic(self):
        """  
        Reports module data to dashboards
        """








        # wpilib.SmartDashboard.potString(
        #     f"{self.name}_drive_motor_rotations",
        #     "rotations: {:5.3f}".format(self.drive_motor.get_position().value),
        # )

    def set_desired_state(self, desired_state: SwerveModuleState) -> None:
        """  
        Sets the module's desired "state" (wheel rim speed and turning/steering angle).
        :param desired_state: the state command to the module.
        """
            # Get the full angle the steering shaft has rotated.
        current_degrees = self._get_full_turn_angle_from_motor()
        current_rotation = Rotation2d.fromDegrees(current_degrees)
            # 
        optimized_state = self._optimize(desired_state, current_rotation)

        drive_effort = _calc_drive_effort(
            inches_per_second(metersToInches(optimized_state.speed))
        ) # 



        geared_rotations = self._degrees_to_turn_count(optimized_state.angle.degrees())
        request = self.position_request.with_position(geared_rotations)

        self.set_drive_effort(drive_effort)
        self.turn_motor.set_control(request)

            # --------------------
            # Private methods for configuration
            # --------------------

    @staticmethod
    def _inches_per_rotation() -> inches:
        return DriveConstants.WHEEL_RADIUS * 2 * 3.14159
            
    @staticmethod
    def _configure_turn_motor() -> TalonFXConfiguration:
        configuration = TalonFXConfiguration()

        configuration.motor_output.inverted = InvertedValue.COUNTER_CLOCKWISE_POSITIVE
        configuration.motor_output.neutral_mode = NeutralModeValue.COAST


        configuration.slot0.k_p = (
            1.0 # An error of one rotation results in 1.0v to the motor
        )
        configuration.slot0.k_i = 0.0 # no integral control
        configuration.slot0.k_d = 0.0 # no differential component

        return configuration
            
    @staticmethod
    def _configure_drive_motor() -> TalonFXConfiguration:
        configuration = TalonFXConfiguration()

        configuration.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
        configuration.motor_output.neutral_mode = NeutralModeValue.BRAKE

        return configuration
            
            #------------------------
            # private methods to help calulate desired state
            # --------------------------

    @staticmethod
    def _place_in_appropriate_0to360_scope(
        scope_reference_degrees: degrees, new_angle_degrees: degrees
    ) -> degrees:
        """  
                Place the new_angle_degrees in the range that is a multiple of [0, 360] that is closest 
                to the scope_reference
        """
        lower_offset = (
            scope_reference_degrees % 360
        )
        lower_bound = scope_reference_degrees - lower_offset
        upper_bound = lower_bound + 360


        while new_angle_degrees < lower_bound:
            new_angle_degrees += 360
        while new_angle_degrees > upper_bound:
            new_angle_degrees -= 360


        if new_angle_degrees - scope_reference_degrees > 180:
            new_angle_degrees -= 360
        elif new_angle_degrees - scope_reference_degrees < -180:
            new_angle_degrees += 360 

        return new_angle_degrees
            
    def _optimize(
        self, desired_state: SwerveModuleState, current_rotation: Rotation2d
    ) -> SwerveModuleState:
        """ 
        There are two ways hausuhudhe
        hdihd
                iddih
                dihdi
        """
        target_angle = self._place_in_appropriate_0to360_scope(
            current_rotation.degrees(), desired_state.angle.degrees()
        )
        target_speed = desired_state.speed
        delta_degrees = target_angle - current_rotation.degrees()

        if abs(delta_degrees) > 90:
            optimized_target_speed = -target_speed
            if delta_degrees > 90:
                        # Delta is positive
                optimized_target_angle = target_angle - 180
            else:
                        # Delta is negative
                optimized_target_angle = target_angle + 180
        else:
            optimized_target_speed = target_speed
            optimized_target_angle = target_angle

        return SwerveModuleState(
            optimized_target_speed, Rotation2d.fromDegrees(optimized_target_angle)
        )
            
            # -------------------------------------
            # Private methods for turn (steering) angle
            # -------------------------------------

    @staticmethod
    def _degrees_to_turn_count(_degrees: degrees) -> float:
        """  
                Converts between steering shaft angle in degrees and motor rotations.
                :param_degrees: turning angle in degrees
                Returns:
                    Turn motor rotations
                """
        rotations = degreesToRotations(_degrees)
        return rotations * DriveConstants.TURN_GEAR_RATIO
            
            # Returns the CANcoder's current position as a percentage of full rotation (range [0, 1]).
    def _get_can_coder_pos_normalized(
        self,
    ) -> (
        percentage
    ): 
        can_coder_abs_pos = self.can_coder.get_absolute_position().value
        can_coder_offset = can_coder_abs_pos - degreesToRotations(
            self.rotation_offset_degrees
        )
        normalized = percentage(can_coder_offset % 1.0)
        return normalized
            
    def _get_turn_angle_from_motor(self) -> degrees:
        """
                Get the turn angle from the motor's encoder, normalized to the 
                range [0.0, 360.0). CCW looking from above is positive.
                Returns:
                    Steering shaft angle in normalized degrees.
        """
                #TalonFX.get_position() returns a value in full rotations.
        motor_abs_rotations = self.turn_motor.get_position().value
                # Convert by gear ratio
        ratioed_rotations = motor_abs_rotations / DriveConstants.TURN_GEAR_RATIO
                # We're only interested in the fractional part
        steering_pct_rotated = ratioed_rotations % 1.0
        return rotationsToDegrees(steering_pct_rotated)
            
    def _get_full_turn_angle_from_motor(self) -> degrees:
        """
                Get the turn angle from the motor's encoder, without wrapping.
                In other words, if the steering has made two complete rotations
                CCW, the returned value will be 720.0 degrees.
                CCW looking from above is positive.
                Returns
                    steering shaft angle in degrees.
        """
                # TalonFX.get_position() returns a value in full rotations
        motor_abs_rotations = self.turn_motor.get_position().value
                # Convert by gear ratio
        ratioed_rotations = motor_abs_rotations / DriveConstants.TURN_GEAR_RATIO
        return rotationsToDegrees(ratioed_rotations)
            
    def stop(self):
        self.drive_motor.stopMotor()
        self.turn_motor.stopMotor()