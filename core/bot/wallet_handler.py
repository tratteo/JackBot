from abc import abstractmethod, ABC


class WalletHandler(ABC):

    @abstractmethod
    def get_balance(self) -> float:
        pass


class TestWallet(WalletHandler):

    @classmethod
    def factory(cls, initial_balance: float):
        return TestWallet(initial_balance)

    def __init__(self, initial_balance: float):
        super().__init__()
        self.__balance = initial_balance
        self.balance_trend = [initial_balance]

    @property
    def balance(self):
        return self.__balance

    def get_balance(self) -> float:
        return self.balance

    @balance.setter
    def balance(self, value: float):
        self.__balance = value
