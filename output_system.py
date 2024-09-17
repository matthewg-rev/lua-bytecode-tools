from enum import Enum, auto
from termcolor import colored

class OutputType(Enum):
    ADDRESS = auto()
    KEYWORD = auto()
    INSTRUCTION = auto()
    REGISTER = auto()
    CONSTANTTYPE = auto()
    CONSTANT = auto()

    NUMBER = auto()
    TAG = auto()

    ERROR = auto()
    WARNING = auto()

    DEFAULT = auto()

    END_OF_LINE = auto()

class OutputSystem:
    def __init__(self):
        self.prepared_data = []
        self.loaded_format = None

    def add_data(self, data, type = OutputType.DEFAULT):
        self.prepared_data.append((data, type))

    def clear_format(self):
        self.loaded_format = None

    def load_format(self, format):
        self.loaded_format = format

    def color_from_type(self, data, type):
        if type == OutputType.ADDRESS:
            return colored(data, 'light_magenta')
        elif type == OutputType.KEYWORD:
            return colored(data, 'green')
        elif type == OutputType.INSTRUCTION:
            return colored(data, 'light_grey')
        elif type == OutputType.REGISTER:
            return colored(data, 'light_cyan')
        elif type == OutputType.CONSTANTTYPE:
            return colored(data, 'light_red')
        elif type == OutputType.CONSTANT:
            return colored(data, 'light_green')
        elif type == OutputType.NUMBER:
            return colored(data, 'light_blue')
        elif type == OutputType.TAG:
            return colored(data, 'yellow')
        elif type == OutputType.ERROR:
            return colored(data, 'light_red')
        elif type == OutputType.WARNING:
            return colored(data, 'light_yellow')
        elif type == OutputType.DEFAULT:
            return colored(data, 'white')
        
    def end_of_line(self):
        self.prepared_data.append((None, OutputType.END_OF_LINE))

    def print_data(self):
        printing_data = []
        line = self.loaded_format if self.loaded_format is not None else ''
        for data, type in self.prepared_data:
            if type == OutputType.END_OF_LINE:
                if self.loaded_format is not None:
                    print(line.format(*printing_data))
                    printing_data = []
                else:
                    print(*printing_data)
                    printing_data = []
            else:
                printing_data.append(self.color_from_type(data, type))
        self.prepared_data = []