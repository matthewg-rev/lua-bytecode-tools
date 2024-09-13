from io import BytesIO

class LuaUpvalue:
    def __init__(self):
        self.name = None

    def read(byteorder, sizes, stream: BytesIO):
        sizeTSize = sizes[1].value
        upvalue = LuaUpvalue()

        size = int.from_bytes(stream.read(sizeTSize), byteorder=byteorder)
        upvalue.name = stream.read(size).decode('utf-8')

        return upvalue

    def __str__(self):
        return f"Upvalue: {self.name}"