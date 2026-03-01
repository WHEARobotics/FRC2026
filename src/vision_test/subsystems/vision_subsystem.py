import commands2
import limelight
import limelightresults
import logging
import wpilib
from ntcore import NetworkTableInstance
from wpilib import SmartDashboard
from wpilib.shuffleboard import Shuffleboard
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.units import seconds, inchesToMeters, degreesToRadians, degrees, metersToInches
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

        # Create a dedicated Shuffleboard Tab
        self.vision_tab = Shuffleboard.getTab("Vision System")

        # This places the widget on the 'Vision System' tab
        self.target_id_entry = (
            self.vision_tab.add("Active Target ID", -1.0)
            .withWidget("Text View")
            .withPosition(4, 1) 
            .getEntry()
        )
        self.target_tx_entry = (
            self.vision_tab.add("Active Target X", 0.0)
            .withWidget("Text View")
            .withPosition(4, 2) 
            .getEntry()
        )
        self.target_ty_entry = (
            self.vision_tab.add("Active Target Y", 0.0)
            .withWidget("Text View")
            .withPosition(5, 2) 
            .getEntry()
        )

        self.target_ta_entry = (
            self.vision_tab.add("Active Target Angle", 0.0)
            .withWidget("Text View")
            .withPosition(6, 2) 
            .getEntry()
        )

        self.trustworthy_entry = (
            self.vision_tab.add("Vision Trustworthy", False)
            .withPosition(5, 1) 
            .getEntry()
        )

        self.vision_x_entry = (
            self.vision_tab.add("Vision X", 0) #metersToInches(pose.X())
            .withWidget("Text View")
            .withPosition(4, 0)
            .getEntry()
        )
        self.vision_y_entry = (
            self.vision_tab.add("Vision Y", 0) #metersToInches(pose.Y())
            .withWidget("Text View")
            .withPosition(5, 0)
            .getEntry()
        )
        self.vision_rotation_entry = (
            self.vision_tab.add("Robot Rotation", 0) #pose.rotation().degrees()
            .withWidget("Text View")
            .withPosition(6, 0)
            .getEntry()
        )

        self.vision_status_entry = (
            self.vision_tab.add("Status", self.debug_status())
            .withPosition(6,1)
            .getEntry()
        )

    def periodic(self):

        # Just read NetworkTables — very fast
        self.target_id_entry.setDouble(self.get_target_id())

        self.target_tx_entry.setDouble(self.get_tx())   

        self.target_ty_entry.setDouble(self.get_ty())  

        self.target_ta_entry.setDouble(self.get_ta())

        self.vision_status_entry.setString(self.debug_status())  
        # etc.

        # Only do botpose / pose estimation when you actually see valid tags
        if self.has_valid_target():
            
            self.trustworthy_entry.setBoolean(self._is_result_trustworthy(self.limelight.get_results()))

            botpose = self.table.getEntry("botpose_wpiblue").getDoubleArray([])
            if len(botpose) >= 6:
                pose = Pose2d(botpose[0], botpose[1], Rotation2d.fromDegrees(botpose[5]))
                timestamp = wpilib.Timer.getFPGATimestamp() - (self.table.getEntry("tl").getDouble(0)/1000.0 + 0.011)  # approx
                self.vision_x_entry.setDouble(metersToInches(pose.X()))
                self.vision_y_entry.setDouble(metersToInches(pose.Y()))
                self.vision_rotation_entry.setDouble(pose.rotation().degrees())
                if self.add_vision_measurement_fn:
                    self.add_vision_measurement_fn(pose, timestamp, (0.6,0.6,9999))
        else:
            self.trustworthy_entry.setBoolean(False)
        

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
        """
        True if Limelight currently reports at least one valid target (tv >= 1).
        This is the most common / reliable check in FRC.
        """
        tv = self.table.getEntry("tv").getDouble(0.0)
        return tv >= 1.0

    def get_tx(self) -> float:
        """Horizontal offset to primary target (degrees, left negative)"""
        # if self.has_valid_target():
        #     return self.last_result.fiducialResults[0].target_x_degrees
        # return 0.0
        return self.table.getEntry("tx").getDouble(0.0)

    def get_ty(self) -> float:
        """Vertical offset to primary target (degrees, up positive)"""
        # if self.has_valid_target():
        #     return self.last_result.fiducialResults[0].target_y_degrees
        # return 0.0
        return self.table.getEntry("ty").getDouble(0.0)
    
    def get_ta(self) -> float:
        return self.table.getEntry("ta").getDouble(0.0)

    def debug_status(self) -> str:
        if self.limelight is None:
            return "No Limelight detected"
        elif not self.has_valid_target():
            return "No valid target"
        else:
            return "Valid target"