from abc import abstractmethod, ABC

from typing import Callable


class StrategyCondition(ABC):

    def __init__(self):
        self.satisfied = False

    @abstractmethod
    def tick(self, frame):
        pass

    @abstractmethod
    def reset(self):
        self.satisfied = False
        pass


class PerpetualStrategyCondition(StrategyCondition):

    def __init__(self, condition_delegate: Callable[[dict], bool]):
        super().__init__()
        self.__condition_delegate = condition_delegate

    def tick(self, frame):
        self.satisfied = self.__condition_delegate(frame)
        pass

    def reset(self):
        super().reset()
        pass


class EventStrategyCondition(StrategyCondition):

    def __init__(self, condition_delegate: Callable[[dict], bool], tolerance_duration: int):
        super().__init__()
        self.__condition_delegate = condition_delegate
        self.__tolerance_duration = tolerance_duration
        self.__current_tolerance = 0

    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.__condition_delegate(frame)
            if self.satisfied: self.__current_tolerance = 0
        else:
            self.satisfied = self.__current_tolerance <= self.__tolerance_duration

        if self.satisfied:
            self.__current_tolerance += 1

    def reset(self):
        super().reset()
        self.__current_tolerance = 0
        pass


class BoundedStrategyCondition(StrategyCondition):

    def __init__(self, valid_condition_delegate: Callable[[dict], bool], invalid_condition_delegate: Callable[[dict], bool], duration_tolerance: int = 0):
        super().__init__()
        self.__valid_condition_delegate = valid_condition_delegate
        self.__invalid_condition_delegate = invalid_condition_delegate
        self.__duration_tolerance = duration_tolerance
        self.__current_tolerance = 0

    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.__valid_condition_delegate(frame)
            if self.satisfied: self.__current_tolerance = 0
        else:
            self.satisfied = not self.__invalid_condition_delegate(frame) and self.__current_tolerance < self.__duration_tolerance

        if self.satisfied:
            self.__current_tolerance += 1

    def reset(self):
        super().reset()
        self.__current_tolerance = 0
        pass
