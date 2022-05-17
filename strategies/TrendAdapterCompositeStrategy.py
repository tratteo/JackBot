from typing import List

import numpy as np

from core.bot.logic.condition import StrategyCondition
from core.bot.logic.position import PositionType
from core.bot.logic.strategy import Strategy
from core.bot.logic.wallet_handler import WalletHandler
from core.bot.middleware.data_frame import DataFrame
from core.utils import lib
from indicators.EMA import EMA
from indicators.RSI import RSI


class TrendAdapterCompositeStrategy(Strategy):

    def __init__(self, wallet_handler: WalletHandler, genome: dict, **strategy_params):

        # Create bear strategy
        strat_class = lib.load_strategy_module(strategy_params.get("bear_strategy")["module"])
        strat_args = strategy_params.get("bear_strategy")["genome"]
        self.bear_strat: Strategy = strat_class(wallet_handler, strat_args, **strategy_params.get("bull_strategy")["parameters"])

        # Create bull strategy
        strat_class = lib.load_strategy_module(strategy_params.get("bull_strategy")["module"])
        strat_args = strategy_params.get("bull_strategy")["genome"]
        self.bull_strat: Strategy = strat_class(wallet_handler, strat_args, **strategy_params.get("bull_strategy")["parameters"])

        self.factor = int(strategy_params.get("switch_timeframe_factor"))

        self.active_strategy: Strategy = self.bull_strat
        self.rsi_up_threshold = float(genome.get("rsi_up_threshold"))
        self.rsi_down_threshold = float(genome.get("rsi_down_threshold"))
        self.ema = EMA(int(genome.get("ema_period")))
        self.ema_val = np.nan
        self.rsi = RSI(int(genome.get("rsi_period")))
        self.rsi_val = np.nan
        self.curr_factor = 0
        self.switch_counter = 0
        self.tolerance_candles = int(genome.get("tolerance_candles"))
        self.cumulative_tolerance = 0
        self.above_ema: bool = True
        self.modular_close_counter = 0
        super().__init__(wallet_handler, int(strategy_params.get("max_open_positions")))

    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        return self.active_strategy.get_stop_loss(open_price, position_type)

    def compute_indicators_step(self, frame: DataFrame):
        self.bear_strat.compute_indicators_step(frame)
        self.bull_strat.compute_indicators_step(frame)
        close = frame.close_price
        self.curr_factor += 1
        if self.curr_factor >= self.factor:
            self.ema_val = self.ema.compute_next(close)
            self.rsi_val = self.rsi.compute_next(close)
            self.curr_factor = 0

    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        return self.active_strategy.get_take_profit(open_price, position_type)

    def get_margin_investment(self) -> float:
        return self.active_strategy.get_margin_investment()

    def build_long_conditions(self) -> List[StrategyCondition]:
        return self.active_strategy.build_long_conditions()

    def build_short_conditions(self) -> List[StrategyCondition]:
        return self.active_strategy.build_short_conditions()

    def update_state(self, frame: DataFrame, verbose: bool = False):

        if frame.is_closed:
            self.modular_close_counter += 1
            if self.modular_close_counter % self.factor == 0:
                self.modular_close_counter = 0
                current_above: bool = frame.close_price > self.ema_val
                if self.ema_val is np.nan:
                    current_above = self.above_ema
                else:
                    pass
                if self.above_ema != current_above:
                    self.cumulative_tolerance += 1
                else:
                    self.cumulative_tolerance = 0

                if self.cumulative_tolerance >= self.tolerance_candles * self.factor:
                    switched: bool = False
                    if current_above and self.rsi_val is not np.nan and self.rsi_val > self.rsi_up_threshold and self.active_strategy is not self.bull_strat:
                        self.switch_strategy(self.bull_strat)
                        switched = True

                    if not current_above and self.rsi_val is not np.nan and self.rsi_val < self.rsi_down_threshold and self.active_strategy is not self.bear_strat:
                        self.switch_strategy(self.bear_strat)
                        switched = True

                    if switched:
                        self.above_ema = current_above
                        self.cumulative_tolerance = 0

        super().update_state(frame, verbose)

    def switch_strategy(self, new_strat: Strategy):
        self.reset_conditions(self.active_strategy.long_conditions)
        self.reset_conditions(self.active_strategy.short_conditions)
        new_strat.reset_conditions(new_strat.long_conditions)
        new_strat.reset_conditions(new_strat.short_conditions)
        self.active_strategy = new_strat
        self.long_conditions = self.active_strategy.long_conditions
        self.short_conditions = self.active_strategy.short_conditions
        self.switch_counter += 1
