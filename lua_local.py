from io import BytesIO

def read_int(stream: BytesIO, size: int) -> int:
    if size == 4:
        return int.from_bytes(stream.read(4), byteorder='little')
    elif size == 8:
        return int.from_bytes(stream.read(8), byteorder='little')

class LuaLocal:
    def __init__(self):
        self.name = None
        self.start = None
        self.end = None

    def read(sizes, stream: BytesIO):
        sizeTSize = sizes[1].value
        local = LuaLocal()

        local.name = stream.read(
            read_int(stream, sizeTSize)
        ).decode('utf-8')

        local.start = stream.read(4)
        local.end = stream.read(4)

        return local