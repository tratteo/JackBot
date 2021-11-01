from typing import Callable


class CommandHandler:
    '''
    


    '''

    @classmethod
    def create(cls):
        """Create a builder instance"""
        builder = CommandHandlerBuilder()
        builder.command_handler = cls()
        return builder

    def __init__(self):
        self.p_args = []
        self.k_args = dict()
        self.f_args = []
        self.p_number = 0
        self.keys = []
        self.fail_delegate = None
        self.helper_string = ''
        self.help_delegate = None
        self.flags = []

    def get_k(self, key: str) -> str:
        return self.k_args.get(key)

    def get_p(self, index: int) -> str:
        return self.p_args[index]

    def has_flag(self, key: str) -> bool:
        return key in self.f_args

    def verify(self) -> bool:
        if not len(self.p_args) == self.p_number:
            return False
        return True


class CommandHandlerBuilder:

    def __init__(self):
        self.command_handler = None

    def positional(self, helper: str):
        self.command_handler.p_number += 1
        self.command_handler.helper_string += 'P' + str(self.command_handler.p_number) + ': ' + helper + '\n'
        return self

    def flag(self, key):
        self.command_handler.flags.append(key)
        return self

    def keyed(self, key, helper: str):
        if key not in self.command_handler.keys:
            self.command_handler.keys.append(key)
            self.command_handler.helper_string += key + ': ' + helper + '\n'
        return self

    def on_fail(self, fail_delegate: Callable[[str], None]):
        self.command_handler.fail_delegate = fail_delegate
        return self

    def on_help(self, help_delegate: Callable[[str], None]):
        self.command_handler.help_delegate = help_delegate
        return self

    def build(self, args: list[str]) -> CommandHandler:
        args = args.copy()
        args.pop(0)
        if len(args) <= 0 or args[0] == 'help' and self.command_handler.help_delegate is not None:
            self.command_handler.help_delegate(self.command_handler.helper_string)
            return self.command_handler
        for k in self.command_handler.keys:
            if k in args:
                index = args.index(k)
                if index <= len(args) - 2:
                    self.command_handler.k_args[k] = args[index + 1]
                    args.remove(args[index + 1])
                args.remove(k)
        for f in self.command_handler.flags:
            if f in args:
                args.remove(f)
                self.command_handler.f_args.append(f)
        self.command_handler.p_args = args
        if not self.command_handler.verify() and self.command_handler.fail_delegate is not None:
            self.command_handler.fail_delegate(self.command_handler.helper_string)
        return self.command_handler
