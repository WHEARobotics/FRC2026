import commands2
import limelight
import limelightresults
import logging
import wpilib
from ntcore import NetworkTableInstance
from wpilib import SmartDashboard
from wpilib.shuffleboard import Shuffleboard
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.units import seconds
from typing import Optional, Callable, Tuple
from constants.visionconstant import VisionConstants

logger = logging.getLogger(__name__)


class VisionSubsystem(commands2.Subsystem):
    """
    Limelight 3 vision processing for 2026 REBUILT game.
    
    Responsibilities:
    - Detect AprilTags using MegaTag2 localization
    - Provide botpose_wpiblue (field-relative, blue alliance origin)
    - Feed reliable vision measurements to drivetrain odometry
    - Offer getters for targeting commands (tx/ty, tag ID)
    - Include basic rejection to avoid bad data
    
    Usage:
    - Pass a callback to add vision measurements to your SwerveDrive4PoseEstimator
    - Call has_valid_target(), get_tx(), get_target_id() from commands
    """

    # def __init__(self, add_vision_measurement_fn: Callable[[Pose2d, float, Tuple[float, float, float]], None]):
    #     """
    #     Parameters:
    #     -----------
    #     add_vision_measurement_fn : Callable[[Pose2d, float, Tuple[float, float, float]], None]
    #         Function to call when we have a good pose estimate.
    #         Usually: drivetrain.odometry.addVisionMeasurement(pose, timestamp, std_devs)
    #     """
    #     super().__init__()
    #     self.add_vision_measurement_fn = add_vision_measurement_fn

    def __init__(self, add_vision_measurement_fn: Optional[Callable] = None): #Used for not connected to the drivetrain

        super().__init__()
        self.add_vision_measurement_fn = add_vision_measurement_fn

        # Limelight connection
        self.limelight_ip = "10.38.81.11" 
    
        try:
            self.limelight = limelight.Limelight(self.limelight_ip)
            self.limelight.enable_websocket()
            logger.info(f"Limelight connected at {self.limelight.base_url}")
        except Exception as e:
            logger.error(f"Could not connect: {e}")
            self.limelight = None

        self.table = NetworkTableInstance.getDefault().getTable("limelight")
        
        # Latest data
        self.last_result: Optional[limelightresults.GeneralResult] = None
        self.last_timestamp: Optional[float] = None

        # Create a dedicated Shuffleboard Tab
        self.vision_tab = Shuffleboard.getTab("Vision System")

        # This places the widget on the 'Vision System' tab
        self.target_id_entry = (
            self.vision_tab.add("Active Target ID", -1.0)
            .withWidget("Text View")
            .withPosition(4, 1) 
            .getEntry()
        )
    
        self.trustworthy_entry = (
            self.vision_tab.add("Vision Trustworthy", False)
            .withPosition(5, 1) 
            .getEntry()
        )

    def periodic(self):
        # Update our specific Shuffleboard Tab entries
        current_id = self.get_target_id()
        self.target_id_entry.setDouble(current_id)   

        if self.limelight is None:
            return
        
        result = self.limelight.get_results()

        # Update Trustworthy status on the tab
        is_trustworthy = False
        if result and result.get("v", 0) != 0:
            is_trustworthy = self._is_result_trustworthy(result)
        
        self.trustworthy_entry.setBoolean(is_trustworthy)

        # Get MegaTag2 pose (blue alliance origin)
        botpose_blue = result.get("botpose_wpiblue")

        if botpose_blue and len(botpose_blue) >= 6:
            # Create the Pose object using specific list indexes
            pose = Pose2d(
                botpose_blue[0],                     # x (meters)
                botpose_blue[1],                     # y (meters)
                Rotation2d.fromDegrees(botpose_blue[5])  # yaw (degrees)
            )

            # # Update SmartDashboard with the raw numbers
            # SmartDashboard.putNumber("Robot Pose X", pose.X())
            # SmartDashboard.putNumber("Robot Pose Y", pose.Y())
            # SmartDashboard.putNumber("Robot Rotation", pose.rotation().degrees())

            # # Feed to odometry (using the converted timestamp from earlier)
            # timestamp = result.get("ts", 0) / 1000.0
            # self.add_vision_measurement_fn(
            #     pose,
            #     timestamp,
            #     VisionConstants.POSE_STD_DEV_POSITION
            # )

            # logger.debug(f"Vision pose update: {pose} @ {timestamp:.3f}s")

            # Always update SmartDashboard (even without a drivetrain)
            self.vision_tab.add("Vision X", pose.X()).withPosition(4, 0) 
            self.vision_tab.add("Vision Y", pose.Y()).withPosition(5, 0) 
            self.vision_tab.add("Robot Rotation", pose.rotation().degrees()).withPosition(6, 0) 

            # ONLY call the drivetrain function if it actually exists
            timestamp = result.get("ts", 0) / 1000.0
            if self.add_vision_measurement_fn is not None:
                self.add_vision_measurement_fn(
                    pose,
                    timestamp,
                    VisionConstants.POSE_STD_DEV_POSITION
                )
            else:
                # Optional: print a reminder once in a while
                pass 

            logger.debug(f"Vision pose update: {pose} @ {timestamp:.3f}s")

    def get_target_id(self) -> float:
        """Returns the current AprilTag ID or -1.0 if none seen."""
        return self.table.getEntry("tid").getDouble(-1.0)


    def _is_result_trustworthy(self, result: dict) -> bool:
        """Apply filters using dictionary access to avoid bad data."""
        # 1. Access the 'Fiducial' list (returns empty list if missing)
        fiducials = result.get("Fiducial", [])
        
        if not fiducials:
            return False

        # 2. Check tag count
        if len(fiducials) < VisionConstants.MIN_VALID_TAGS_FOR_POSE:
            return False

        # 3. Check ambiguity of the primary (first) tag
        primary = fiducials[0]
        # In the JSON dict, ambiguity is usually 'ambiguity' or 'a'
        if primary.get("ambiguity", 1.0) > VisionConstants.MAX_AMBIGUITY_DEGREES:
            return False
        
        # 4. Get current FPGA time in seconds
        current_time = wpilib.Timer.getFPGATimestamp()

        # 5. Check latency (timestamp is 'ts' in the JSON dict)
        limelight_ts = result.get("ts", 0) / 1000.0 # Convert ms to seconds if needed
        if (current_time - limelight_ts) > VisionConstants.MAX_LATENCY_SECONDS:
            return False

        return True

    # ────────────────────────────────────────────────
    # Public getters for commands / dashboard
    # ────────────────────────────────────────────────

    def has_valid_target(self) -> bool:
        return (
            self.last_result is not None
            and self.last_result.validity > 0
            and self.last_result.fiducialResults
        )

    def get_tx(self) -> float:
        """Horizontal offset to primary target (degrees, left negative)"""
        if self.has_valid_target():
            return self.last_result.fiducialResults[0].target_x_degrees
        return 0.0

    def get_ty(self) -> float:
        """Vertical offset to primary target (degrees, up positive)"""
        if self.has_valid_target():
            return self.last_result.fiducialResults[0].target_y_degrees
        return 0.0

    def get_tag_count(self) -> int:
        """Number of currently detected AprilTags"""
        if self.last_result and self.last_result.fiducialResults:
            return len(self.last_result.fiducialResults)
        return 0

    def get_botpose_blue(self) -> Optional[Pose2d]:
        """Returns the Robot's 2D Pose (X, Y, Rotation) relative to the blue alliance origin."""
        # Get the latest result dict
        result = self.limelight.get_results()
        
        # Check validity (v=1 means it sees tags)
        if result is None or result.get("v", 0) == 0:
            return None

        # Get the blue alliance array
        botpose = result.get("botpose_wpiblue")

        # Convert to WPILib Pose2d [x, y, z, roll, pitch, yaw]
        if botpose and len(botpose) >= 6:
            return Pose2d(
                botpose[0], # X in meters
                botpose[1], # Y in meters
                Rotation2d.fromDegrees(botpose[5]) # Yaw in degrees
            )
        return None

    def debug_status(self) -> str:
        """For SmartDashboard or troubleshooting."""
        if self.limelight is None:
            return "No Limelight detected"
        if not self.has_valid_target():
            return "No valid target"
        tag_id = self.get_target_id()
        tx, ty = self.get_tx(), self.get_ty()
        return f"Tag {tag_id} | tx={tx:.1f}° ty={ty:.1f}° | {self.get_tag_count()} tags"