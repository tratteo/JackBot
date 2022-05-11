import json

from core import lib
from core.bot.position import Position
from core.bot.strategy import Strategy


class TestResult:
    def __init__(self, strategy: Strategy, initial_balance: float, minute_candles: int, time_frame_minutes: int):
        self.total_profit = 0
        self.days = 0
        self.win_ratio = 0
        self.estimated_apy = 0
        self.minutes = 0
        self.initial_balance = 0
        self.opened_positions = 0
        self.final_balance = 0
        self.time_frame_minutes = 0
        self.average_result_percentage = 0
        self.closed_positions = []
        self.populate(strategy, initial_balance, minute_candles, time_frame_minutes)

    def populate(self, strategy: Strategy, initial_balance: float, minute_candles: int, time_frame_minutes: int):
        self.initial_balance = initial_balance
        self.total_profit = 0
        self.minutes = minute_candles
        self.days = float(minute_candles) / 1440
        self.time_frame_minutes = time_frame_minutes
        self.closed_positions: list[Position] = strategy.closed_positions
        won = 0
        self.average_result_percentage = 0
        for c in self.closed_positions:
            self.total_profit += c.profit
            self.average_result_percentage += c.result_percentage
            if c.won:
                won += 1

        self.average_result_percentage /= len(strategy.closed_positions)
        self.final_balance = self.initial_balance + self.total_profit
        if len(strategy.closed_positions) > 0:
            self.win_ratio = won / len(strategy.closed_positions)

        self.estimated_apy = (((self.final_balance / self.initial_balance) ** (365 / self.days)) - 1) * 100
        self.opened_positions = len(strategy.open_positions) + len(strategy.closed_positions)

    def to_json(self):
        dic = vars(self)
        dic["closed_positions"] = len(self.closed_positions)
        return json.dumps(dic, default = lambda x: None, indent = 4)

    def __str__(self):
        return "{:<25s}{:^4.2f}".format("Time span (d): ", self.days) + \
               "\n{:<25s}{:^4s}".format("Time frame: ", lib.get_flag_from_minutes(self.time_frame_minutes)) + \
               "\n{:<25s}{:^4.3f}".format("Initial balance: ", self.initial_balance) + \
               "\n{:<25s}{:^4.3f}".format("Final balance: ", self.final_balance) + \
               "\n{:<25s}{:^4.3f}".format("Total profit: ", self.total_profit) + \
               "\n{:<25s}{:^4}".format("Opened positions: ", self.opened_positions) + \
               "\n{:<25s}{:^4.3f}".format("Win rate: ", self.win_ratio * 100) + "%" + \
               "\n{:<25s}{:^4.3f}".format("Estimated apy: ", self.estimated_apy) + "%"
