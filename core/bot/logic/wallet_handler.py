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
        self.balance = initial_balance
        self.total_balance = initial_balance

    def get_balance(self) -> float:
        return self.balance
