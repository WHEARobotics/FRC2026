from wpilib import SmartDashboard

""" Utility class to check if a value exceeds a threshold (for instance, motor current).
    Puts on SmartDashboard `name` and `{name}_current` 
"""
class CurrentThreshold():
    def __init__(self, name: str, stop_threshold_amps : float):
        self.name = name
        self.stop_threshold_amps = stop_threshold_amps
        SmartDashboard.putNumber(f"{self.name}_threshold", stop_threshold_amps)

    def is_exceeded(self, amps : float) -> bool:
        SmartDashboard.putNumber(f"{self.name}_current", amps)
        return amps >= self.stop_threshold_amps