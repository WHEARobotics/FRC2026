"""
Vision-related constants for 2026 REBUILT game.
- AprilTag IDs grouped by field element (from official Game Manual TU11).
- Heights are approximate centers from floor (for pipeline tuning or 3D solve).
- Use botpose_wpiblue for all field-relative calculations (blue alliance origin).
"""

from dataclasses import dataclass
from typing import List, Tuple

# ────────────────────────────────────────────────
# AprilTag IDs by Field Element (36h11 family, IDs 1-32)
# ────────────────────────────────────────────────
@dataclass(frozen=True)
class VisionConstants:

    HUB_TAG_IDS: List[int] = [2, 3, 4, 5, 8, 9, 10, 11, 18, 19, 20, 21, 24, 25, 26, 27]
    """
    HUB AprilTags: Located on all four faces of the HUB.
    - Each face has 2 tags (one centered, one offset horizontally).
    - Center height: ~44.25 inches (1.124 m) from floor.
    - Primary for scoring FUEL into the HUB.
    """

    TOWER_WALL_TAG_IDS: List[int] = [15, 16, 31, 32]
    """
    TOWER WALL AprilTags: 2 per TOWER WALL (centered + offset).
    - Center height: ~21.75 inches (0.553 m) from floor.
    - Useful for climb alignment or tower approach.
    """

    OUTPOST_TAG_IDS: List[int] = [13, 14, 29, 30]
    """
    OUTPOST AprilTags: 2 per OUTPOST (centered on CHUTE/CORRAL + offset).
    - Center height: ~21.75 inches (0.553 m) from floor.
    - Good for HP interaction, loading FUEL, or Outpost targeting.
    """

    TRENCH_TAG_IDS: List[int] = [1, 6, 7, 12, 17, 22, 23, 28]
    """
    TRENCH AprilTags: Attached to mounting brackets on horizontal arm of TRENCH.
    - Useful for field orientation, crossing under trenches, or neutral zone nav.
    """

    ALL_RELEVANT_TAG_IDS: List[int] = (
        HUB_TAG_IDS + TOWER_WALL_TAG_IDS + OUTPOST_TAG_IDS + TRENCH_TAG_IDS
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
    PRIORITY_TARGET_TAGS: List[int] = HUB_TAG_IDS  # Default: aim at HUB for scoring