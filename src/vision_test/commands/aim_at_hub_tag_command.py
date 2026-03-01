import commands2

from subsystems.vision_subsystem import VisionSubsystem
from constants.visionconstant import VisionConstants
# from subsystems.drive_subsystem import DriveSubsystem

# Simple PID-like turn to face a HUB AprilTag (e.g., IDs 2-11)
class AimAtHubTagCommand(commands2.Command):
    def __init__(self, vision: VisionSubsystem):
        super().__init__()
        self.vision = vision
        self.addRequirements(vision)

    def execute(self):
        if self.vision.has_valid_target():
            tag_id = self.vision.get_target_id() 
            if tag_id in VisionConstants.HUB_TAG_IDS: # e.g., [2,3,4,5,8,9,10,11,...]
                # self.drivetrain.drive(0, 0, 0)     # stop
                print("ready")
                return
            else:
                print("aiming")

    def isFinished(self) -> bool:
            return (
                self.vision.has_valid_target() and
                self.vision.get_target_id() in VisionConstants.HUB_TAG_IDS
            )

    def end(self, interrupted: bool):
        # self.drivetrain.drive(0, 0, 0)
        pass