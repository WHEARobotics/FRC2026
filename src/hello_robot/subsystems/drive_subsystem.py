from typing import Optional

import commands2
import wpimath
import logging
from wpilib import SmartDashboard, Field2d
from wpimath.controller import ProfiledPIDController
from wpimath.trajectory import TrapezoidProfile
from wpimath.geometry import Rotation2d, Pose2d
from wpimath.kinematics import (
    SwerveDrive4Kinematics,
    # SwerveDrive4Odometry,
    ChassisSpeeds,
    SwerveModuleState, SwerveModulePosition,
)
from wpimath.estimator import SwerveDrive4PoseEstimator

from wpimath.units import inchesToMeters, degreesToRadians, degrees, metersToInches
from phoenix6.hardware.pigeon2 import Pigeon2

from constants.driveconstants import DriveConstants
from constants.new_types import inches_per_second, degrees_per_second, percentage
from subsystems.swerve_module_subsystem import SwerveModule # swerve_module in original code, but file is named different - doublecheck

logger = logging.getLogger(__name__)







class DriveSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()


        self.modules = [
            SwerveModule(
                "FrontRight",
                DriveConstants.DRIVE_FR,
                DriveConstants.TURN_FR,
                DriveConstants.CAN_FR,
                DriveConstants.FR_OFFSET,
            ),
            SwerveModule(
                "FrontLeft",
                DriveConstants.DRIVE_FL,
                DriveConstants.TURN_FL,
                DriveConstants.CAN_FL,
                DriveConstants.FL_OFFSET,
            ),
            SwerveModule(
                "BackLeft",
                DriveConstants.DRIVE_BL,
                DriveConstants.TURN_BL,
                DriveConstants.CAN_BL,
                DriveConstants.BL_OFFSET,
            ),
            SwerveModule(
                "BackRight",
                DriveConstants.DRIVE_BR,
                DriveConstants.TURN_BR,
                DriveConstants.CAN_BR,
                DriveConstants.BR_OFFSET,
            ),
        ]
        self.FrontRightModule = self.modules[0]
        self.FrontLeftModule = self.modules[1]
        self.BackLeftModule = self.modules[2]
        self.BackRightModule = self.modules[3]


        self.gyro = Pigeon2(DriveConstants.PIGEON_ID)
        self.gyro.set_yaw(
            0.0
        ) # assumes robot s facing same direction as driver


        self.kinematics = SwerveDrive4Kinematics(*self._get_module_translations())
        self.odometry = self._initialize_odometry(kinematics=self.kinematics)

        self.slow_mode = False

        self.speed_divisor = 2
        self.rotation_divisor = 4


        self.field_sim = Field2d()
        SmartDashboard.putData("Field", self.field_sim)


        self.x_controller, self.y_controller, self.rot_controller = (
            self._initialize_pid_controllers()
        )

        








        self.pose = self.odometry.getEstimatedPosition()










    def drive_by_effort(
        self, drive_effort: percentage, turn_effort: percentage
    ) -> None:
        for module in self.modules:
            module.set_drive_effort(drive_effort)
            module.set_turn_effort(turn_effort)

    def set_drive_angle(self, desired_angle_degrees: degrees) -> None:
        # Probably: (probably??? what???)
        for module in self.modules:
            module.set_turn_angle(desired_angle_degrees)





    def get_gyro_heading_degrees(self) -> degrees:
        """  
        Gets the heading of the robot (direction it is pointing) in degrees.
        CCW is positive.
        """
        heading = self.gyro.get_yaw().value

        return heading

    def get_gyro_heading_rotation2d(self) -> Rotation2d:
        """
        Gets the heading of the robot (direction it is pointing) as a Rotation2D.
        CCW is positive.
        """
        return Rotation2d.fromDegrees(self.get_gyro_heading_degrees())

    def get_estimated_pose(self) -> wpimath.geometry.Pose2d:
        return self.odometry.getEstimatedPosition()
        
    def get_controllers_goals(self) -> tuple[float, float, float]:
        return (
            self.x_controller.getGoal().position,
            self.y_controller.getGoal().position,
            self.rot_controller.getGoal().position,
        ) 







    def periodic(self):
        for module in self.modules:
            module.periodic()

        self.check_and_set_slow_mode()

        # self.get_speed_mode()

        SmartDashboard.putBoolean("Slow mode", self.slow_mode)


        positions = [module.get_position() for module in self.modules]
        self.odometry.update(self.get_gyro_heading_rotation2d(), tuple(positions))



        self.pose = self.odometry.getEstimatedPosition()
        SmartDashboard.putNumber("Robot X", metersToInches(self.pose.X()))
        SmartDashboard.putNumber("Robot Y", metersToInches(self.pose.Y()))
        SmartDashboard.putNumber("Gyro Degree", self.get_gyro_heading_degrees())
        SmartDashboard.putNumber("Robot Heading", self.pose.rotation().degrees())

        SmartDashboard.putNumber("Front Left Pos", self.FrontLeftModule.get_position().angle.degrees())
        SmartDashboard.putNumber("Front Right Pos", self.FrontRightModule.get_position().angle.degrees())
        SmartDashboard.putNumber("Back Left Pos", self.BackLeftModule.get_position().angle.degrees())
        SmartDashboard.putNumber("Back Right Pos", self.BackRightModule.get_position().angle.degrees())
        





















        self.field_sim.setRobotPose(self.pose)

    def drive(
        self,
        x_speed_inches_per_second: inches_per_second,
        y_speed_inches_per_second: inches_per_second,
        rot_speed_degrees_per_second: degrees_per_second,
    ) -> None:
        """
    
        




        """
        desaturated_module_states = self._speeds_to_states(
            x_speed_inches_per_second,
            y_speed_inches_per_second,
            rot_speed_degrees_per_second,
        )
        for module, state in zip(self.modules, desaturated_module_states):
            module.set_desired_state(state)






    def get_speed_mode(self) -> bool:
        return self.slow_mode


    def _speeds_to_states(
        self,
        x_speed: inches_per_second,
        y_speed: inches_per_second,
        rot_speed: degrees_per_second,
    ) -> list[SwerveModuleState]:
        chassis_speeds = self._get_chassis_speeds(
            x_speed_inches_per_second=x_speed,
            y_speed_inches_per_second=y_speed,
            rot_speed_degrees_per_second=rot_speed,
        )
        swerve_module_states = self.kinematics.toSwerveModuleStates(chassis_speeds)
        desaturated_module_states = SwerveDrive4Kinematics.desaturateWheelSpeeds(
            swerve_module_states,
            inchesToMeters(DriveConstants.MAX_SPEED_INCHES_PER_SECOND),
        )
        return desaturated_module_states

    def _get_chassis_speeds(
        self,
        x_speed_inches_per_second: inches_per_second,
        y_speed_inches_per_second: inches_per_second,
        rot_speed_degrees_per_second: degrees_per_second,
    ) -> ChassisSpeeds:
        
        x_speed_meters_per_second = inchesToMeters(x_speed_inches_per_second)
        y_speed_meters_per_second = inchesToMeters(y_speed_inches_per_second)
        rot_speed_radians = degreesToRadians(rot_speed_degrees_per_second)
        cs = ChassisSpeeds.fromRobotRelativeSpeeds(
            x_speed_meters_per_second,
            y_speed_meters_per_second,
            rot_speed_radians,
            -self.get_gyro_heading_rotation2d(),
        )
        return cs





    def _initialize_odometry(
        self, kinematics: SwerveDrive4Kinematics
    ) -> SwerveDrive4PoseEstimator:
        estimator = SwerveDrive4PoseEstimator(
            kinematics = kinematics,
            gyroAngle = self.get_gyro_heading_rotation2d(),
            modulePositions = [module.get_position() for module in self.modules],
            initialPose=Pose2d(x = 0.0, y = 0.0, rotation = self.get_gyro_heading_rotation2d())
        )

        estimator.setVisionMeasurementStdDevs((0.7, 0.7, 9999999))

        return estimator


    @staticmethod
    def _get_module_translations() -> list[wpimath.geometry.Translation2d]:
        """
        Returns the physical positions of each swerve module relative to the center of the robot.
        The order should match the order of modules in self.modules:
        [FrontRight, FrontLeft, BackLeft, BackRight]

        Returns:
            list[Translation2d]: List of module positions in inches
        """

        # Create Translation2d objects for each module position
        # The coordinate system is:
        # - Positive x is forward
        # - Positive y is left
        # - Origin (0,0) is at robot center
        translations = [
            wpimath.geometry.Translation2d(
                DriveConstants.WHEELBASE_HALF_LENGTH, -DriveConstants.TRACK_HALF_WIDTH
            ),  # Front Right
            wpimath.geometry.Translation2d(
                DriveConstants.WHEELBASE_HALF_LENGTH, DriveConstants.TRACK_HALF_WIDTH
            ),  # Front Left
            wpimath.geometry.Translation2d(
                -DriveConstants.WHEELBASE_HALF_LENGTH, DriveConstants.TRACK_HALF_WIDTH
            ),  # Back Left
            wpimath.geometry.Translation2d(
                -DriveConstants.WHEELBASE_HALF_LENGTH, -DriveConstants.TRACK_HALF_WIDTH
            ),  # Back Right
        ]

        return translations

    def set_goal_pose(self, goal_pose: Pose2d) -> None:
        """
        Set the goal for upcoming use of PID controllers.
        Call this before using drive_to_goal().
        :param: goal_pose The desired pose to drive to.
        """
        # Reset the PID loops, because we're starting a new trajectory.
        self.reset_pids()
        # Extract each axis to set the goal for the corresponding controller.
        goal_x = goal_pose.X()
        self.x_controller.setGoal(goal_x)

        goal_y = goal_pose.Y()
        self.y_controller.setGoal(goal_y)
        goal_rot = goal_pose.rotation().degrees()
        goal_rot = wpimath.inputModulus(goal_rot, -180, 180)
        self.rot_controller.setGoal(goal_rot)

    def drive_to_goal(self):
        """
        Drive from present pose toward another pose on the field.
        Uses the goal set by set_goal_pose().  Call that method once first.
        """
        # Calculate the "gas pedal" values for each axis.
        present_x = self.pose.X()
        pid_output_x = metersToInches(self.x_controller.calculate(present_x))
        clamped_x = clamp(
            val = pid_output_x,
            min_val = -DriveConstants.MAX_SPEED_INCHES_PER_SECOND,
            max_val = DriveConstants.MAX_SPEED_INCHES_PER_SECOND,
        )  # Drive expects inches per second.

        present_y = self.pose.Y()
        pid_output_y = metersToInches(self.y_controller.calculate(present_y))
        clamped_y = clamp(
            val = pid_output_y,
            min_val = -DriveConstants.MAX_SPEED_INCHES_PER_SECOND,
            max_val = DriveConstants.MAX_SPEED_INCHES_PER_SECOND,
        )

        present_rot = self.pose.rotation().degrees()
        present_rot = wpimath.inputModulus(present_rot, -180, 180)
        pid_output_rot = self.rot_controller.calculate(present_rot)
        clamped_rot = clamp(
            val = pid_output_rot,
            min_val = -DriveConstants.MAX_DEGREES_PER_SECOND,
            max_val = DriveConstants.MAX_DEGREES_PER_SECOND,
        )

        # Send the values to the drive train.
        self.drive(x_speed_inches_per_second=clamped_x, y_speed_inches_per_second=clamped_y, rot_speed_degrees_per_second=clamped_rot)

    def is_at_goal(self):
        """
        Used with PID loops to determine if the robot is at the target/goal
        position.
        :returns: True if all three axes (X, Y, rotation) are at the goal.
        """
        all_controllers_at_goal = (
            self.x_controller.atGoal()
            and self.y_controller.atGoal()
            and self.rot_controller.atGoal()
        )
        return all_controllers_at_goal

    def reset_pids(self):
        """
        
        """
        self.x_controller.reset(self.pose.X())
        self.y_controller.reset(self.pose.Y())
        self.rot_controller.reset(self.pose.rotation().degrees())

    @staticmethod
    def _initialize_pid_controllers() -> (
        tuple[ProfiledPIDController, ProfiledPIDController, ProfiledPIDController]
    ):
        
        x_controller = ProfiledPIDController(
            DriveConstants.PIDX_KP,
            0,
            0,
            TrapezoidProfile.Constraints(
                inchesToMeters(DriveConstants.HORIZ_MAX_V), inchesToMeters(DriveConstants.HORIZ_MAX_A)
            ),
        )
        x_controller.setTolerance(
            inchesToMeters(DriveConstants.HORIZ_POS_TOL), inchesToMeters(DriveConstants.HORIZ_VEL_TOL)
        )

        y_controller = ProfiledPIDController(
            DriveConstants.PIDY_KP,
            0,
            0,
            TrapezoidProfile.Constraints(
                inchesToMeters(DriveConstants.HORIZ_MAX_V), inchesToMeters(DriveConstants.HORIZ_MAX_A)
            ),
        )
        y_controller.setTolerance(
            inchesToMeters(DriveConstants.HORIZ_POS_TOL), inchesToMeters(DriveConstants.HORIZ_VEL_TOL)
        )


        rot_controller = ProfiledPIDController(
            DriveConstants.PID_ROT_KP,
            0,
            0,
            TrapezoidProfile.Constraints(
                DriveConstants.ROT_MAX_V, DriveConstants.ROT_MAX_A
            ),
        )
        rot_controller.setTolerance(
            DriveConstants.ROT_POS_TOL, DriveConstants.ROT_VEL_TOL
        )
        rot_controller.enableContinuousInput(-180, 180)

        return x_controller, y_controller, rot_controller

    def stop(self):
        for module in self.modules:
            module.stop()






    def check_and_set_slow_mode(self):
        if self.slow_mode == True:
            self.speed_divisor = 8
            self.rotation_divisor = 16
        else:
            self.speed_divisor = 2
            self.rotation_divisor = 4

        return self.speed_divisor, self.rotation_divisor


    def clamp(val, min_val, max_val):
        """Returns a number clamped to minval and maxval."""
        return max(min(val, max_val), min_val)