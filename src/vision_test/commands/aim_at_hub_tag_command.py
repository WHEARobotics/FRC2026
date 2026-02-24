import commands2

from subsystems.vision_subsystem import VisionSubsystem
from constants.visionconstants import VisionConstants

# Simple PID-like turn to face a HUB AprilTag (e.g., IDs 2-11)
class AimAtHubTagCommand(commands2.Command):
    def __init__(self, vision: VisionSubsystem, drivetrain):
        super().__init__()
        self.vision = vision
        self.drivetrain = drivetrain
        self.addRequirements(drivetrain)

    def execute(self):
        print("aiming")
        if not self.vision.has_valid_target():
            self.drivetrain.stop()  # or drive(0,0,0)
            return

        tag_id = self.vision.get_target_id()
        if tag_id not in VisionConstants.HUB_TAG_IDS:  # e.g., [2,3,4,5,8,9,10,11,...]
            return

        tx = self.vision.get_tx()  # degrees off-center
        rot_speed = -0.025 * tx  # simple P gain (tune this!)
        rot_speed = max(min(rot_speed, 1.0), -1.0)  # clamp

        self.drivetrain.drive(0, 0, rot_speed)  # Only rotate in place

    def isFinished(self) -> bool:
        print("done")
        return abs(self.vision.get_tx()) < 2.0  # within 2 degrees