from enum import Enum, auto

WorkingDataObjects = []

class WorkingType(Enum):
    HEADER = auto()
    FUNCTION = auto()
    INSTRUCTION = auto()
    CONSTANT = auto()
    LOCAL = auto()
    UPVALUE = auto()

    def __str__(self):
        return self.name.lower()



class WorkingData:
    def __init__(self):
        self.userDefinedTag = None # for user-defined naming of data

        self.type = None
        self.address = None
        self.value = None
        WorkingDataObjects.append(self)

    def from_data(type, address, value):
        data = WorkingData()
        data.type = type
        data.address = address
        data.value = value
        return data