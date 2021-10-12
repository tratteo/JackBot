import talib
print(talib.__ta_version__)

from talib import abstract
stoch =  abstract.Function('stoch')
stoch.set_parameters(fastk_period=14, slowk_period=1, slowd_period=3, slowk_matype=0, slowd_matype=0)
print(stoch.lookback)
