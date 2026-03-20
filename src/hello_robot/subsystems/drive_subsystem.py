from typing import Optional, Tuple

import commands2
import limelight
import wpimath
import wpilib
import logging
from wpilib import SmartDashboard, Field2d
from ntcore import NetworkTableInstance
from wpilib.shuffleboard import Shuffleboard
from wpimath.geometry import Pose2d, Rotation2d, Translation2d
from wpimath.units import inchesToMeters, degreesToRadians, degrees, metersToInches

from phoenix6.hardware.pigeon2 import Pigeon2
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
from constants.newtypes import inches_per_second, degrees_per_second, percentage
from subsystems.swerve_module_subsystem import SwerveModule # swerve_module in original code, but file is named different - doublecheck

logger = logging.getLogger(__name__)

class DriveSubsystem(commands2.Subsystem):
    def __init__(self):
        super().__init__()
        # ────────────────────────────────────────────────
        #          VISION (Limelight) INTEGRATION
        # ────────────────────────────────────────────────

        self.limelight_ip = "10.38.81.11"

        try:
            self.limelight = limelight.Limelight(self.limelight_ip)
            self.limelight.enable_websocket()
            logger.info(f"Limelight connected at {self.limelight.base_url}")
        except Exception as e:
            logger.error(f"Could not connect to Limelight: {e}")
            self.limelight = None

        self.nt_table = NetworkTableInstance.getDefault().getTable("limelight")

        # Shuffleboard Tab
        self.robot_tab = Shuffleboard.getTab("Robot System")

        self.slow_mode_entry = self.robot_tab.add("Slow mode", self.slow_mode).withPosition(7, 1).getEntry()

        self.target_id_entry = self.robot_tab.add("Active Target ID", -1.0).withPosition(4, 1).getEntry()
        self.target_tx_entry = self.robot_tab.add("Active Target X", 0.0).withPosition(4, 2).getEntry()
        self.target_ty_entry = self.robot_tab.add("Active Target Y", 0.0).withPosition(5, 2).getEntry()
        self.target_ta_entry = self.robot_tab.add("Active Target Area", 0.0).withPosition(6, 2).getEntry()

        self.trustworthy_entry = self.robot_tab.add("Vision Trustworthy", False).withPosition(5, 1).getEntry()

        self.vision_x_entry = self.robot_tab.add("Vision X (in)", 0).withPosition(4, 0).getEntry()
        self.vision_y_entry = self.robot_tab.add("Vision Y (in)", 0).withPosition(5, 0).getEntry()
        self.vision_rotation_entry = self.robot_tab.add("Vision Rotation (°)", 0).withPosition(6, 0).getEntry()

        self.vision_status_entry = self.robot_tab.add("Vision Status", "Initializing...").withPosition(6, 1).getEntry()

        # ────────────────────────────────────────────────
        #          SWERVE HARDWARE & ODOMETRY
        # ────────────────────────────────────────────────

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
        self.pose_estimator = self._initialize_pose_estimator()

        self.slow_mode = False

        self.speed_divisor = 2
        self.rotation_divisor = 4


        self.field_sim = Field2d()
        SmartDashboard.putData("Field", self.field_sim)


        self.x_controller, self.y_controller, self.rot_controller = (
            self._initialize_pid_controllers()
        )

        self.pose = self.pose_estimator.getEstimatedPosition()

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
        
        SmartDashboard.putBoolean("Slow mode", self.slow_mode)

        self.slow_mode_entry.setBoolean(self.slow_mode)

        positions = [module.get_position() for module in self.modules]
        self.pose_estimator.update(self.get_gyro_heading_rotation2d(), *positions)

        self.pose = self.pose_estimator.getEstimatedPosition()

        # ─── Vision processing ───
        self._update_vision_dashboard()

        if self.has_valid_target():
            # Optional: get raw botpose from NT (faster than websocket in many cases)
            botpose = self.nt_table.getEntry("botpose_wpiblue").getDoubleArray([])
            if len(botpose) >= 6:
                vision_pose = Pose2d(botpose[0], botpose[1], Rotation2d.fromDegrees(botpose[5]))
                latency = self.nt_table.getEntry("tl").getDouble(0) / 1000.0 + 0.011  # approx pipeline delay
                timestamp = wpilib.Timer.getFPGATimestamp() - latency

                # Add to estimator (with vision std devs)
                self.pose_estimator.addVisionMeasurement(
                    vision_pose,
                    timestamp,
                    (0.6, 0.6, 999999.0)  # trust x/y, almost ignore vision yaw
                )

                # Dashboard feedback
                self.vision_x_entry.setDouble(metersToInches(vision_pose.X()))
                self.vision_y_entry.setDouble(metersToInches(vision_pose.Y()))
                self.vision_rotation_entry.setDouble(vision_pose.rotation().degrees())

                # Trustworthy check (websocket-based for ambiguity/latency)
                if self.limelight:
                    result = self.limelight.get_results()
                    self.trustworthy_entry.setBoolean(self._is_result_trustworthy(result))
                else:
                    self.trustworthy_entry.setBoolean(False)
        else:
            self.trustworthy_entry.setBoolean(False)

        # Common dashboard updates
        SmartDashboard.putNumber("Robot X", metersToInches(self.pose.X()))
        SmartDashboard.putNumber("Robot Y", metersToInches(self.pose.Y()))
        SmartDashboard.putNumber("Gyro Degree", self.get_gyro_heading_degrees())
        SmartDashboard.putNumber("Robot Heading", self.pose.rotation().degrees())

        for i, name in enumerate(["Front Left", "Front Right", "Back Left", "Back Right"]):
            SmartDashboard.putNumber(f"{name} Pos", self.modules[i].get_position().angle.degrees())

        self.field_sim.setRobotPose(self.pose)

    def has_valid_target(self) -> bool:
        return self.nt_table.getEntry("tv").getDouble(0.0) >= 1.0

    def get_target_id(self) -> float:
        return self.nt_table.getEntry("tid").getDouble(-1.0)

    def get_tx(self) -> float:
        return self.nt_table.getEntry("tx").getDouble(0.0)

    def get_ty(self) -> float:
        return self.nt_table.getEntry("ty").getDouble(0.0)

    def get_ta(self) -> float:
        return self.nt_table.getEntry("ta").getDouble(0.0)

    def _is_result_trustworthy(self, result: dict) -> bool:
        if not result:
            return False

        fiducials = result.get("Fiducial", [])
        if not fiducials:
            return False

        if len(fiducials) < DriveConstants.MIN_VALID_TAGS_FOR_POSE:
            return False

        primary = fiducials[0]
        if primary.get("ambiguity", 1.0) > DriveConstants.MAX_AMBIGUITY_DEGREES:
            return False

        current_time = wpilib.Timer.getFPGATimestamp()
        limelight_ts = result.get("ts", 0) / 1000.0
        if (current_time - limelight_ts) > DriveConstants.MAX_LATENCY_SECONDS:
            return False

        return True

    def _update_vision_dashboard(self):
        self.target_id_entry.setDouble(self.get_target_id())
        self.target_tx_entry.setDouble(self.get_tx())
        self.target_ty_entry.setDouble(self.get_ty())
        self.target_ta_entry.setDouble(self.get_ta())

        if self.limelight is None:
            status = "No Limelight detected"
        elif not self.has_valid_target():
            status = "No valid target"
        else:
            status = f"Valid target (ID {int(self.get_target_id())})"

        self.vision_status_entry.setString(status)

    # ────────────────────────────────────────────────
    #          SWERVE / ODOMETRY HELPERS (unchanged or lightly adapted)
    # ────────────────────────────────────────────────

    def _initialize_pose_estimator(self) -> SwerveDrive4PoseEstimator:
        initial_pose = Pose2d(0, 0, Rotation2d(0))
        initial_positions = [module.get_position() for module in self.modules]

        return SwerveDrive4PoseEstimator(
            self.kinematics,
            self.get_gyro_heading_rotation2d(),
            tuple(initial_positions),
            initial_pose,
            stateStdDevs=(0.1, 0.1, degreesToRadians(5)),     # wheel odometry noise
            visionMeasurementStdDevs=(0.6, 0.6, 999999.0)     # vision noise (trust gyro for rotation)
        )

    def _get_module_translations(self) -> list[Translation2d]:
        return [
            Translation2d(DriveConstants.WHEELBASE_HALF_LENGTH, -DriveConstants.TRACK_HALF_WIDTH),   # FR
            Translation2d(DriveConstants.WHEELBASE_HALF_LENGTH,  DriveConstants.TRACK_HALF_WIDTH),   # FL
            Translation2d(-DriveConstants.WHEELBASE_HALF_LENGTH, DriveConstants.TRACK_HALF_WIDTH),   # BL
            Translation2d(-DriveConstants.WHEELBASE_HALF_LENGTH, -DriveConstants.TRACK_HALF_WIDTH),  # BR
        ]

    def get_gyro_heading_degrees(self) -> float:
        return self.gyro.get_yaw().value

    def get_gyro_heading_rotation2d(self) -> Rotation2d:
        return Rotation2d.fromDegrees(self.get_gyro_heading_degrees())

    def get_estimated_pose(self) -> Pose2d:
        return self.pose_estimator.getEstimatedPosition()

    def drive(
        self,
        x_speed: inches_per_second,
        y_speed: inches_per_second,
        rot_speed: degrees_per_second,
    ) -> None:
        states = self.kinematics.toSwerveModuleStates(
            ChassisSpeeds.fromFieldRelativeSpeeds(
                x_speed / 39.3701,  # inches → meters
                y_speed / 39.3701,
                rot_speed * (3.14159 / 180),  # deg/s → rad/s
                self.get_gyro_heading_rotation2d()
            )
        )
        SwerveDrive4Kinematics.desaturateWheelSpeeds(states, DriveConstants.MAX_SPEED_INCHES_PER_SECOND / 39.3701)
        for module, state in zip(self.modules, states):
            module.set_desired_state(state)

    # ... (keep the rest of your methods: drive_to_goal, set_goal_pose, reset_pids, clamp, stop, check_and_set_slow_mode, etc.)


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