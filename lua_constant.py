from io import BytesIO
from enum import Enum

class LuaConstantType(Enum):
    NONE = 0
    Boolean = 1
    Number = 3
    String = 4

class LuaConstant:
    def __init__(self):
        self.type = None
        self.value = None

    def read(sizes, stream: BytesIO):
        sizeTSize, numberSize = sizes[1].value, sizes[3].value
        constant = LuaConstant()

        constant.type = LuaConstantType(int.from_bytes(stream.read(1)))

        if constant.type == LuaConstantType.Boolean:
            constant.value = int.from_bytes(stream.read(1))
        elif constant.type == LuaConstantType.Number:
            constant.value = float.from_bytes(stream.read(numberSize), byteorder='little')
        elif constant.type == LuaConstantType.String:
            size = int.from_bytes(stream.read(sizeTSize), byteorder='little')
            constant.value = stream.read(size).decode('utf-8')

        return constant