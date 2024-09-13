from io import BytesIO
from lua_chunk import LuaChunk
from working_data import WorkingData, WorkingType

class LuaBytecode:
    def __init__(self):
        self.signature = None
        self.version = None
        self.format = None
        self.endianness = None
        self.intSize = None
        self.sizeTSize = None
        self.instructinoSize = None
        self.numberSize = None
        self.integralFlag = None

        self.chunks = []


    def read(bytes):
        bytecode = LuaBytecode()

        stream = BytesIO(bytes)

        bytecode.signature = WorkingData.from_data(WorkingType.HEADER, 0, stream.read(4))
        bytecode.version = WorkingData.from_data(WorkingType.HEADER, 4, int.from_bytes(stream.read(1)))
        bytecode.format = WorkingData.from_data(WorkingType.HEADER, 5, int.from_bytes(stream.read(1)))
        bytecode.endianness = WorkingData.from_data(WorkingType.HEADER, 6, int.from_bytes(stream.read(1)))
        bytecode.intSize = WorkingData.from_data(WorkingType.HEADER, 7, int.from_bytes(stream.read(1)))
        bytecode.sizeTSize = WorkingData.from_data(WorkingType.HEADER, 8, int.from_bytes(stream.read(1)))
        bytecode.instructionSize = WorkingData.from_data(WorkingType.HEADER, 9, int.from_bytes(stream.read(1)))
        bytecode.numberSize = WorkingData.from_data(WorkingType.HEADER, 10, int.from_bytes(stream.read(1)))
        bytecode.integralFlag = WorkingData.from_data(WorkingType.HEADER, 11, int.from_bytes(stream.read(1)))

        mainChunk = LuaChunk.read([bytecode.intSize, bytecode.sizeTSize, bytecode.instructionSize, bytecode.numberSize], stream)

        # DFS to read all the chunks
        def read_chunks(chunk):
            bytecode.chunks.append(WorkingData.from_data(WorkingType.FUNCTION, chunk.__startAddress__, chunk))
            for c in chunk.chunks:
                read_chunks(c)
        
        read_chunks(mainChunk)

        return bytecode