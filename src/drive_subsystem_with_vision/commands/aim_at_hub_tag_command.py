import commands2

from subsystems.drive_subsystem import DriveSubsystem
from constants.driveconstants import DriveConstants


class AimAtHubTagCommand(commands2.Command):
    """
    Slowly rotate until any HUB AprilTag is detected,
    then stop rotating immediately.
    """

    def __init__(self, drivetrain: DriveSubsystem):
        super().__init__()
        self.drivetrain = drivetrain
        self.addRequirements(drivetrain)

        self.search_rot_speed = 0.20      # adjust 0.12–0.25

    def execute(self):
        if not self.drivetrain.has_valid_target():
            self.drivetrain.drive(0, 0, self.search_rot_speed)
            return

        tag_id = self.drivetrain.get_target_id()

        if tag_id not in DriveConstants.HUB_TAG_IDS:
            self.drivetrain.drive(0, 0, self.search_rot_speed)
            return

        # HUB tag found → stop
        self.drivetrain.drive(0, 0, 0)

    def isFinished(self) -> bool:
        return (
            self.drivetrain.has_valid_target() and
            self.drivetrain.get_target_id() in DriveConstants.HUB_TAG_IDS
        )

    def end(self, interrupted: bool) -> None:
        self.drivetrain.drive(0, 0, 0)