from io import BytesIO
from enum import Enum
import struct

class LuaConstantType(Enum):
    NONE = 0
    Boolean = 1
    Number = 3
    String = 4

class LuaConstant:
    def __init__(self):
        self.type = None
        self.value = None

    def read(byteorder, sizes, stream: BytesIO):
        sizeTSize, numberSize = sizes[1].value, sizes[3].value
        constant = LuaConstant()

        constant.type = LuaConstantType(int.from_bytes(stream.read(1), byteorder=byteorder))

        if constant.type == LuaConstantType.Boolean:
            constant.value = int.from_bytes(stream.read(1), byteorder=byteorder) == 1
        elif constant.type == LuaConstantType.Number:
            number = stream.read(numberSize)
            constant.value = struct.unpack('d', number)[0]
        elif constant.type == LuaConstantType.String:
            size = int.from_bytes(stream.read(sizeTSize), byteorder=byteorder)
            constant.value = stream.read(size)

        return constant