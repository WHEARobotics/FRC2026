from dataclasses import dataclass, field
from typing import List, Tuple
from wpimath.units import metersToInches

from constants.new_types import (
    inches_per_second,
    inches,
    degrees_per_second,
    degrees,
    inches_per_second_squared,
    degrees_per_second_squared,
)


@dataclass(frozen=True)
class DriveConstants:
    """Drivetrain related constants"""

    # CANcoder CAN bus IDs
    CAN_FR = 11 
    CAN_FL = 8
    CAN_BL = 5
    CAN_BR = 2
    # Gears to the LEFT fo the Robot
    # CANcoder (magnet) offsets in rotations that we got from the CANcoder using Phoenix Tuner X 
    # Not really needed
    BR_OFFSET = -0.253906  # -0.242
    BL_OFFSET = -0.319580 # -0.175
    FR_OFFSET = 0.464844 # 0.033
    FL_OFFSET = -0.414307  # -0.081

    # Kraken IDs
    DRIVE_FR = 12
    DRIVE_FL = 9
    DRIVE_BL = 6
    DRIVE_BR = 3

    TURN_FR = 10
    TURN_FL = 7
    TURN_BL = 4
    TURN_BR = 1

    # Pigeon2 gyro CAN bus ID
    PIGEON_ID = 13

    # Drivetrain geometry, gearing, etc.
    TRACK_HALF_WIDTH: inches = metersToInches(0.27) # meters 
    WHEELBASE_HALF_LENGTH: inches = metersToInches(0.27)
    TURN_GEAR_RATIO = 468.0/35.0 #10 pinion gear
    DRIVE_GEAR_RATIO = 6.2 #11 pinion gear
    WHEEL_DIA: inches = 4 # 4" diameter

    WHEEL_RADIUS: inches = WHEEL_DIA / 2

    FREE_SPEED = 3.76 # max








    MAX_SPEED_INCHES_PER_SECOND: inches_per_second = (
        145.7 
    )
    MAX_DEGREES_PER_SECOND: degrees_per_second = (
        72.85
    ) # degrees per second






    PIDX_KP: float = 1.0 * 0.9592
    PIDY_KP: float = 1.0 * 0.9592 
    PID_ROT_KP: float = 1.0 / 90.0


    HORIZ_MAX_V: inches_per_second = 39.0
    HORIZ_MAX_A: inches_per_second_squared = (
        78.0 * 1.5
    )
    HORIZ_POS_TOL: inches = (
        4.0
    )
    HORIZ_VEL_TOL: inches_per_second = 0.4


    ROT_MAX_V: degrees_per_second = (
        40.0
    )
    ROT_MAX_A: degrees_per_second_squared = (
        20.0
    )
    ROT_POS_TOL: degrees = 5.0
    ROT_VEL_TOL: degrees_per_second = (
        1.0
    )

    HUB_TAG_IDS = [2, 3, 4, 5, 8, 9, 10, 11, 18, 19, 20, 21, 24, 25, 26, 27] 
    """
    HUB AprilTags: Located on all four faces of the HUB.
    - Each face has 2 tags (one centered, one offset horizontally).
    - Center height: ~44.25 inches (1.124 m) from floor.
    - Primary for scoring FUEL into the HUB.
    """

    TOWER_WALL_TAG_IDS = [15, 16, 31, 32] 
    """
    TOWER WALL AprilTags: 2 per TOWER WALL (centered + offset).
    - Center height: ~21.75 inches (0.553 m) from floor.
    - Useful for climb alignment or tower approach.
    """

    OUTPOST_TAG_IDS = [13, 14, 29, 30] 
    """
    OUTPOST AprilTags: 2 per OUTPOST (centered on CHUTE/CORRAL + offset).
    - Center height: ~21.75 inches (0.553 m) from floor.
    - Good for HP interaction, loading FUEL, or Outpost targeting.
    """

    TRENCH_TAG_IDS = [1, 6, 7, 12, 17, 22, 23, 28]
    """
    TRENCH AprilTags: Attached to mounting brackets on horizontal arm of TRENCH.
    - Useful for field orientation, crossing under trenches, or neutral zone nav.
    """

    ALL_RELEVANT_TAG_IDS: List[int] = field(
        default_factory=lambda: DriveConstants.HUB_TAG_IDS + DriveConstants.TOWER_WALL_TAG_IDS + DriveConstants.OUTPOST_TAG_IDS + DriveConstants.TRENCH_TAG_IDS
        )
    """All 32 tags combined for broad detection."""

    # ────────────────────────────────────────────────
    # Heights (centers from floor) – for pipeline 3D solve or manual offset tuning
    # ────────────────────────────────────────────────

    HUB_TAG_HEIGHT_INCHES: float = 44.25
    TOWER_OUTPOST_TAG_HEIGHT_INCHES: float = 21.75
    # Trench tags vary (top surface mounting) – use ~30-40 inches as estimate if needed

    # Limelight pipeline recommendations (set in Limelight web UI)
    RECOMMENDED_PIPELINE_INDEX: int = 0  # Pipeline 0 = AprilTag + MegaTag2 enabled
    MIN_VALID_TAGS_FOR_POSE: int = 1     # Minimum tags to trust pose (prefer 2+)
    MAX_AMBIGUITY_DEGREES: float = 5.0   # Reject if primary tag ambiguity > this
    MAX_LATENCY_SECONDS: float = 0.150   # Reject old results (>150ms)

    # Vision tuning / rejection
    POSE_STD_DEV_POSITION: Tuple[float, float, float] = (0.6, 0.6, 999999.0)  # Trust vision X/Y more than rotation (gyro better)
    POSE_STD_DEV_ROTATION: float = 999999.0  # High value = low trust in vision yaw

    # Example target priorities (for commands)
    PRIORITY_TARGET_TAGS: List[int] = field(default_factory=lambda: DriveConstants.HUB_TAG_IDS)  # Default: aim at HUB for scoring