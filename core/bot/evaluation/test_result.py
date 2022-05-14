import json

from core.bot.logic.strategy import Strategy


class EvaluationResult:
    def __init__(self, strategy: Strategy, initial_balance: float, minute_candles: int, time_frame_minutes: int):
        self.days = 0
        self.minutes = 0
        self.time_frame_minutes = 0
        self.initial_balance = 0
        self.final_balance = 0
        self.total_profit = 0
        self.win_ratio = 0
        self.estimated_apy = 0
        self.average_result_percentage = 0
        self.result_percentage = 0
        self.opened_positions = 0
        self.closed_positions = 0
        self.populate(strategy, initial_balance, minute_candles, time_frame_minutes)

    def populate(self, strategy: Strategy, initial_balance: float, minute_candles: int, time_frame_minutes: int):
        self.initial_balance = initial_balance
        self.total_profit = 0
        self.minutes = minute_candles
        self.days = float(minute_candles) / 1440
        self.time_frame_minutes = time_frame_minutes
        self.closed_positions = len(strategy.closed_positions)
        won = 0
        self.average_result_percentage = 0
        for c in strategy.closed_positions:
            self.total_profit += c.profit
            self.result_percentage += c.result_percentage
            if c.won:
                won += 1

        self.average_result_percentage = self.result_percentage / len(strategy.closed_positions)
        self.final_balance = self.initial_balance + self.total_profit
        if len(strategy.closed_positions) > 0:
            self.win_ratio = won / len(strategy.closed_positions)

        self.estimated_apy = (((self.final_balance / self.initial_balance) ** (365 / self.days)) - 1) * 100
        self.opened_positions = len(strategy.open_positions) + len(strategy.closed_positions)

    def __str__(self):
        return json.dumps(vars(self), indent = 4)
