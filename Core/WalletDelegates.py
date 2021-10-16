class WalletDelegates:

    def __init__(self, change_balance_delegate, get_balance_delegate):
        self.change_balance_delegate = change_balance_delegate
        self.get_balance_delegate = get_balance_delegate


    def change_balance(self, amount):
        self.change_balance_delegate(amount)


    def get_balance(self):
        return self.get_balance_delegate()
