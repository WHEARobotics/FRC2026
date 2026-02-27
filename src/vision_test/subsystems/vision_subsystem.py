import commands2
import limelight
import limelightresults
import logging
import wpilib
from wpilib import Shuffleboard, SmartDashboard
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

    def __init__(self, add_vision_measurement_fn: Callable[[Pose2d, float, Tuple[float, float, float]], None]):
        """
        Parameters:
        -----------
        add_vision_measurement_fn : Callable[[Pose2d, float, Tuple[float, float, float]], None]
            Function to call when we have a good pose estimate.
            Usually: drivetrain.odometry.addVisionMeasurement(pose, timestamp, std_devs)
        """
        super().__init__()

        self.add_vision_measurement_fn = add_vision_measurement_fn

        # Limelight connection
        self.limelight: Optional[limelight.Limelight] = None
        discovered = limelight.discover_limelights(debug=True)
        if not discovered:
            logger.warning("No Limelight found! Vision disabled.")
        else:
            self.limelight = limelight.Limelight(discovered[0])
            self.limelight.enable_websocket()
            logger.info(f"Limelight connected at {self.limelight.base_url}")

        # Latest data
        self.last_result: Optional[limelightresults.GeneralResult] = None
        self.last_timestamp: Optional[float] = None

    def periodic(self) -> None:
        if self.limelight is None:
            return

        result = self.limelight.get_results()
        if result is None or result.validity == 0:
            return

        self.last_result = result
        self.last_timestamp = result.timestamp

        # Basic rejection
        if not self._is_result_trustworthy(result):
            return

        # Get MegaTag2 pose (blue alliance origin)
        botpose_blue = result.botpose_wpiblue
        if botpose_blue and len(botpose_blue) >= 6:
            pose = Pose2d(
                botpose_blue[0],                     # x (meters)
                botpose_blue[1],                     # y (meters)
                Rotation2d.fromDegrees(botpose_blue[5])  # yaw (degrees)
            )

            # Feed to odometry with tuned standard deviations
            self.add_vision_measurement_fn(
                pose,
                self.last_timestamp,
                VisionConstants.POSE_STD_DEV_POSITION
            )

            logger.debug(f"Vision pose update: {pose} @ {self.last_timestamp:.3f}s")

    def _is_result_trustworthy(self, result: limelightresults.GeneralResult) -> bool:
        """Apply filters to avoid feeding bad data to odometry."""
        if not result.fiducialResults:
            return False

        # Too few tags
        if len(result.fiducialResults) < VisionConstants.MIN_VALID_TAGS_FOR_POSE:
            return False

        # Primary tag too ambiguous
        primary = result.fiducialResults[0]
        if primary.ambiguity > VisionConstants.MAX_AMBIGUITY_DEGREES:
            return False

        # Result too old
        if (seconds.now() - result.timestamp) > VisionConstants.MAX_LATENCY_SECONDS:
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

    def get_target_id(self) -> int:
        """ID of the primary detected AprilTag"""
        if self.has_valid_target():
            return self.last_result.fiducialResults[0].fiducial_id
        return -1

    def get_tag_count(self) -> int:
        """Number of currently detected AprilTags"""
        if self.last_result and self.last_result.fiducialResults:
            return len(self.last_result.fiducialResults)
        return 0

    def get_botpose_blue(self) -> Optional[list[float]]:
        """Raw botpose_wpiblue array (if available)"""
        if self.last_result:
            return self.last_result.botpose_wpiblue
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