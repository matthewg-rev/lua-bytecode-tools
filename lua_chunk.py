from io import BytesIO

from lua_instruction import LuaInstruction
from lua_constant import LuaConstant
from lua_local import LuaLocal
from lua_upvalue import LuaUpvalue
from working_data import WorkingData, WorkingType

def read_int(byteorder, stream: BytesIO, size: int) -> int:
    if size == 4:
        return int.from_bytes(stream.read(4), byteorder=byteorder, signed=False)
    elif size == 8:
        return int.from_bytes(stream.read(8), byteorder=byteorder, signed=False)

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
        
    def read(byteorder, sizes, stream: BytesIO):
        intSize, sizeTSize = sizes[0].value, sizes[1].value

        chunk = LuaChunk()
        chunk.__startAddress__ = stream.tell()

        # read the size of the source string
        size = read_int(byteorder, stream, sizeTSize)
        chunk.source = stream.read(size).decode('utf-8')

        # read the line defined for the chunk
        chunk.lineDefined = read_int(byteorder, stream, intSize)

        # read the last line defined for the chunk
        chunk.lastLineDefined = read_int(byteorder, stream, intSize)

        # read the number of upvalues
        chunk.numUpvalues = int.from_bytes(stream.read(1), byteorder=byteorder)

        # read the number of parameters
        chunk.numParameters = int.from_bytes(stream.read(1), byteorder=byteorder)

        # read the vararg flag
        chunk.isVararg = int.from_bytes(stream.read(1), byteorder=byteorder)

        # read the maximum stack size
        chunk.maxStackSize = int.from_bytes(stream.read(1), byteorder=byteorder)

        # read the instructions
        numInstructions = read_int(byteorder, stream, intSize)
        for i in range(numInstructions):
            startAddress = stream.tell()
            instruction = LuaInstruction.read(byteorder, sizes, stream)
            instruction.chunk = chunk
            chunk.instructions.append(WorkingData.from_data(WorkingType.INSTRUCTION, startAddress, instruction))

        # read the constants
        numConstants = read_int(byteorder, stream, intSize)
        for i in range(numConstants):
            startAddress = stream.tell()
            chunk.constants.append(WorkingData.from_data(WorkingType.CONSTANT, startAddress, LuaConstant.read(byteorder, sizes, stream)))

        # read other prototypes
        for i in range(read_int(byteorder, stream, intSize)):
            nextChunk = LuaChunk.read(byteorder, sizes, stream)
            chunk.chunks.append(nextChunk)
        
        # read the debug information
        for i in range(read_int(byteorder, stream, intSize)):
            chunk.debug['lines'].append(stream.read(4))

        for i in range(read_int(byteorder, stream, intSize)):
            startAddress = stream.tell()
            chunk.debug['locals'].append(
                WorkingData.from_data(WorkingType.LOCAL, startAddress, LuaLocal.read(byteorder, sizes, stream))
            )

        for i in range(read_int(byteorder, stream, intSize)):
            startAddress = stream.tell()
            chunk.debug['upvalues'].append(
                WorkingData.from_data(WorkingType.UPVALUE, startAddress, LuaUpvalue.read(byteorder, sizes, stream))
            )

        return chunk