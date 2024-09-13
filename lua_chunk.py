from io import BytesIO

from lua_instruction import LuaInstruction
from lua_constant import LuaConstant
from lua_local import LuaLocal
from lua_upvalue import LuaUpvalue
from working_data import WorkingData, WorkingType

def read_int(stream: BytesIO, size: int) -> int:
    if size == 4:
        return int.from_bytes(stream.read(4), byteorder='little')
    elif size == 8:
        return int.from_bytes(stream.read(8), byteorder='little')

class LuaChunk:
    def __init__(self):
        self.__startAddress__ = None
        self.source = None
        self.lineDefined = None
        self.lastLineDefined = None
        self.numUpvalues = None
        self.numParameters = None
        self.isVararg = None
        self.maxStackSize = None

        self.instructions = []
        self.constants = []
        self.chunks = []

        self.debug = {
            'lines': [],
            'locals': [],
            'upvalues': []
        }
        
    def read(sizes, stream: BytesIO):
        intSize, sizeTSize = sizes[0].value, sizes[1].value

        chunk = LuaChunk()
        chunk.__startAddress__ = stream.tell()

        # read the size of the source string
        size = read_int(stream, sizeTSize)
        chunk.source = stream.read(size).decode('utf-8')

        # read the line defined for the chunk
        chunk.lineDefined = read_int(stream, intSize)

        # read the last line defined for the chunk
        chunk.lastLineDefined = read_int(stream, intSize)

        # read the number of upvalues
        chunk.numUpvalues = int.from_bytes(stream.read(1))

        # read the number of parameters
        chunk.numParameters = int.from_bytes(stream.read(1))

        # read the vararg flag
        chunk.isVararg = int.from_bytes(stream.read(1))

        # read the maximum stack size
        chunk.maxStackSize = int.from_bytes(stream.read(1))

        # read the instructions
        numInstructions = read_int(stream, intSize)
        print(numInstructions)
        for i in range(numInstructions):
            startAddress = stream.tell()
            chunk.instructions.append(WorkingData.from_data(WorkingType.INSTRUCTION, startAddress, LuaInstruction.read(sizes, stream)))

        # read the constants
        numConstants = read_int(stream, intSize)
        print(numConstants)
        for i in range(numConstants):
            startAddress = stream.tell()
            chunk.constants.append(WorkingData.from_data(WorkingType.CONSTANT, startAddress, LuaConstant.read(sizes, stream)))

        # read other prototypes
        for i in range(read_int(stream, intSize)):
            nextChunk = LuaChunk.read(sizes, stream)
            chunk.chunks.append(WorkingData.from_data(WorkingType.FUNCTION, nextChunk.__startAddress__, nextChunk))
        
        # read the debug information
        for i in range(read_int(stream, intSize)):
            chunk.debug['lines'].append(stream.read(4))

        for i in range(read_int(stream, intSize)):
            startAddress = stream.tell()
            chunk.debug['locals'].append(
                WorkingData.from_data(WorkingType.LOCAL, startAddress, LuaLocal.read(sizes, stream))
            )

        for i in range(read_int(stream, intSize)):
            startAddress = stream.tell()
            chunk.debug['upvalues'].append(
                WorkingData.from_data(WorkingType.UPVALUE, startAddress, LuaUpvalue.read(sizes, stream))
            )

        return chunk