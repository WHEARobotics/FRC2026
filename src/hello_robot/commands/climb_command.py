import commands2

from constants.newtypes import inches
from subsystems.climb_subsystem import ClimbSubsystem

class ClimbToGoalCommand(commands2.Command):

    def __init__(self, goal: inches, climb: ClimbSubsystem):
        super().__init__()
        self.climb = climb
        self.goal = goal
        self.addRequirements(climb)

    def initialize(self):
        self.climb.set_goal_height_inches(self.goal)

    def execute(self):
        self.climb.move_to_goal()

    def isFinished(self):
        return self.climb.is_at_goal()

    def end(self, interrupted):
        self.climb.stop()