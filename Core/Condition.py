from abc import ABC, abstractmethod


class StrategyCondition(ABC):

    def __init__(self):
        self.satisfied = False


    @abstractmethod
    def tick(self, frame):
        pass


class PerpetualStrategyCondition(StrategyCondition):

    def __init__(self, condition):
        super().__init__()
        self.condition = condition


    def tick(self, frame):
        self.satisfied = self.condition(frame)
        pass


class EventStrategyCondition(StrategyCondition):

    def __init__(self, condition, tolerance_duration: int):
        super().__init__()
        self.condition = condition
        self.tolerance_duration = tolerance_duration
        self.current_tolerance = 0


    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.condition(frame)
            if self.satisfied: self.current_tolerance = 0
        else:
            self.satisfied = self.current_tolerance <= self.tolerance_duration

        if self.satisfied:
            self.current_tolerance += 1


class DoubledStrategyCondition(StrategyCondition):

    def __init__(self, valid_condition, invalid_condition, duration_tolerance: int = 0):
        super().__init__()
        self.valid_condition = valid_condition
        self.invalid_condition = invalid_condition
        self.duration_tolerance = duration_tolerance
        self.current_tolerance = 0


    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.valid_condition(frame)
            if self.satisfied: self.current_tolerance = 0
        else:
            self.satisfied = not self.invalid_condition(frame) and self.current_tolerance < self.duration_tolerance

        if self.satisfied:
            self.current_tolerance += 1
