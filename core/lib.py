import os
import sys
from typing import Callable


def get_minutes_from_flag(flag: str):
    if flag == "1m":
        return 1
    if flag == "3m":
        return 3
    if flag == "5m":
        return 5
    if flag == "10m":
        return 10
    if flag == "15m":
        return 15
    if flag == "30m":
        return 30
    if flag == "1h":
        return 60
    if flag == "4h":
        return 240
    if flag == "1d":
        return 1440
    if flag == "1w":
        return 10080
    if flag == "1M":
        return 43200
    else:
        return None


def get_flag_from_minutes(minutes: int):
    if minutes == 1:
        return "1m"
    if minutes == 3:
        return "3m"
    if minutes == 5:
        return "5m"
    if minutes == 10:
        return "10m"
    if minutes == 15:
        return "15m"
    if minutes == 30:
        return "30m"
    if minutes == 60:
        return "1h"
    if minutes == 240:
        return "4h"
    if minutes == 1440:
        return "1d"
    if minutes == 10080:
        return "1w"
    if minutes == 43200:
        return "1M"
    else:
        return None


def create_folders_in_path(path: str, fail_delegate: Callable[[], any] = None):
    try:
        index = path.rindex("/")
        folders = path[0: index]
        if not os.path.exists(folders):
            try:
                os.makedirs(folders)
            except FileExistsError:
                print("Unable to create " + folders + " dirs", flush = True)
                if fail_delegate is not None:
                    fail_delegate()
    except ValueError:
        return


def try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


class ProgressBar:

    def __init__(self, total_steps: int):
        self.current_length = 0
        self.total_steps = total_steps
        self.current_step = 0
        self.width = 25
        self.percentage = 0
        self.style_edges = ("|", "|")
        self.style_fill = "█"
        self.show_percentage = True

    def reset(self):
        self.current_length = 0
        self.current_step = 0
        self.percentage = 0
        self.render()

    def render(self):
        if self.show_percentage:
            sys.stdout.write("{0:}{1:}{2:} {3:.2f}%\r".format(self.style_edges[0], self.style_fill * self.current_length + " " * (self.width - self.current_length), self.style_edges[1], float(self.percentage * 100)))
        else:
            sys.stdout.write("{0:}{1:}{2:}\r".format(self.style_edges[0], self.style_fill * self.current_length + " " * (self.width - self.current_length), self.style_edges[1]))
        sys.stdout.flush()

    def step(self, progress: float):
        self.current_step += progress
        # print(str(progress) + ", " + str(self.current_step))
        if self.current_step > self.total_steps: self.current_step = self.total_steps
        self.percentage = self.current_step / self.total_steps
        self.current_length = int(self.percentage * self.width)
        self.render()

    def dispose(self):
        self.current_length = 0
        self.current_step = 0
        self.percentage = 0
        print("", flush = True)

    @staticmethod
    def create(total_steps: int):
        return ProgressBarBuilder(total_steps)


class ProgressBarBuilder:

    def __init__(self, total_steps: int):
        self.progress_bar = ProgressBar(total_steps)

    def width(self, width: int):
        self.progress_bar.width = width
        return self

    def style(self, edges: tuple[str, str], fill: str):
        self.progress_bar.style_fill = fill
        self.progress_bar.style_edges = edges
        return self

    def no_percentage(self):
        self.progress_bar.show_percentage = False
        return self

    def build(self):
        return self.progress_bar
