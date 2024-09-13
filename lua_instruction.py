from io import BytesIO
from enum import IntEnum, Enum, auto

class LuaOpcode(IntEnum):
    MOVE = 0
    LOADK = 1
    LOADBOOL = 2
    LOADNIL = 3
    GETUPVAL = 4

    GETGLOBAL = 5
    GETTABLE = 6

    SETGLOBAL = 7
    SETUPVAL = 8
    SETTABLE = 9

    NEWTABLE = 10

    SELF = 11

    ADD = 12
    SUB = 13
    MUL = 14
    DIV = 15
    MOD = 16
    POW = 17
    UNM = 18
    NOT = 19
    LEN = 20

    CONCAT = 21

    JMP = 22

    EQ = 23
    LT = 24
    LE = 25

    TEST = 26
    TESTSET = 27

    CALL = 28
    TAILCALL = 29
    RETURN = 30

    FORLOOP = 31

    FORPREP = 32

    TFORLOOP = 33

    SETLIST = 34

    CLOSE = 35
    CLOSURE = 36

    VARARG = 37

    def __str__(self):
        return self.name


class LuaInstructionType(Enum):
    A = 0
    AB = 1
    AC = 2
    ABC = 3
    ABx = 4
    AsBx = 5
    sBx = 6

InstructionTypeLookup = {
    LuaOpcode.MOVE: LuaInstructionType.ABC, 
    LuaOpcode.LOADK: LuaInstructionType.ABx, 
    LuaOpcode.LOADBOOL: LuaInstructionType.ABC,
    LuaOpcode.LOADNIL: LuaInstructionType.AB, 
    LuaOpcode.GETUPVAL: LuaInstructionType.AB, 
    
    LuaOpcode.GETGLOBAL: LuaInstructionType.ABx,
    LuaOpcode.GETTABLE: LuaInstructionType.ABC, 
    
    LuaOpcode.SETGLOBAL: LuaInstructionType.ABx, 
    LuaOpcode.SETUPVAL: LuaInstructionType.AB,
    LuaOpcode.SETTABLE: LuaInstructionType.ABC,

    LuaOpcode.NEWTABLE: LuaInstructionType.ABC,

    LuaOpcode.SELF: LuaInstructionType.ABC,

    LuaOpcode.ADD: LuaInstructionType.ABC,
    LuaOpcode.SUB: LuaInstructionType.ABC,
    LuaOpcode.MUL: LuaInstructionType.ABC,
    LuaOpcode.DIV: LuaInstructionType.ABC,
    LuaOpcode.MOD: LuaInstructionType.ABC,
    LuaOpcode.POW: LuaInstructionType.ABC,
    LuaOpcode.UNM: LuaInstructionType.AB,
    LuaOpcode.NOT: LuaInstructionType.AB,
    LuaOpcode.LEN: LuaInstructionType.AB,

    LuaOpcode.CONCAT: LuaInstructionType.ABC,

    LuaOpcode.JMP: LuaInstructionType.sBx,

    LuaOpcode.EQ: LuaInstructionType.ABC,
    LuaOpcode.LT: LuaInstructionType.ABC,
    LuaOpcode.LE: LuaInstructionType.ABC,

    LuaOpcode.TEST: LuaInstructionType.AC,
    LuaOpcode.TESTSET: LuaInstructionType.ABC,

    LuaOpcode.CALL: LuaInstructionType.ABC,
    LuaOpcode.TAILCALL: LuaInstructionType.ABC,
    LuaOpcode.RETURN: LuaInstructionType.AB,
    
    LuaOpcode.FORLOOP: LuaInstructionType.AsBx,
    LuaOpcode.FORPREP: LuaInstructionType.AsBx,

    LuaOpcode.TFORLOOP: LuaInstructionType.AC,
    LuaOpcode.SETLIST: LuaInstructionType.ABC,

    LuaOpcode.CLOSE: LuaInstructionType.A,
    LuaOpcode.CLOSURE: LuaInstructionType.ABx,

    LuaOpcode.VARARG: LuaInstructionType.AB
}

class LuaRegisterName(Enum):
    A = 0
    B = 1
    C = 2
    Bx = 3
    sBx = 4

class LuaRegister:
    def __init__(self, name: LuaRegisterName):
        self.name = name
        self.value = None

    def __str__(self):
        return f"{self.value}"

class LuaInstruction:
    def __init__(self):
        self.opcode = None
        self.type = None
        self.registers = {
            LuaRegisterName.A: LuaRegister(LuaRegisterName.A),
            LuaRegisterName.B: LuaRegister(LuaRegisterName.B),
            LuaRegisterName.C: LuaRegister(LuaRegisterName.C),
            LuaRegisterName.Bx: LuaRegister(LuaRegisterName.Bx),
            LuaRegisterName.sBx: LuaRegister(LuaRegisterName.sBx)
        }

    def read(byteorder, sizes, stream: BytesIO):
        instructionSize = sizes[2].value
        instruction = LuaInstruction()

        raw = int.from_bytes(stream.read(instructionSize), byteorder=byteorder, signed=False)

        instruction.opcode = LuaOpcode(raw & 0x3F)
        instruction.type = InstructionTypeLookup[instruction.opcode]

        if instruction.type == LuaInstructionType.A:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
        elif instruction.type == LuaInstructionType.AB:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
            instruction.registers[LuaRegisterName.B].value = (raw >> 23) & 0x1FF
        elif instruction.type == LuaInstructionType.AC:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
            instruction.registers[LuaRegisterName.C].value = (raw >> 14) & 0x1FF
        elif instruction.type == LuaInstructionType.ABx:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
            instruction.registers[LuaRegisterName.Bx].value = (raw >> 14) & 0x3FFFF
        elif instruction.type == LuaInstructionType.AsBx:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
            instruction.registers[LuaRegisterName.sBx].value = (raw >> 14) & 0x3FFFF
        elif instruction.type == LuaInstructionType.ABC:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
            instruction.registers[LuaRegisterName.B].value = (raw >> 23) & 0x1FF
            instruction.registers[LuaRegisterName.C].value = (raw >> 14) & 0x1FF
        elif instruction.type == LuaInstructionType.sBx:
            instruction.registers[LuaRegisterName.sBx].value = (raw >> 14) & 0x3FFFF

        return instruction
    
    def get_register(self, index: int):
        if index == 0:
            if self.type == LuaInstructionType.sBx:
                return str(self.registers[LuaRegisterName.sBx].value)
            return str(self.registers[LuaRegisterName.A].value)
        elif index == 1:
            if self.type == LuaInstructionType.AB:
                return str(self.registers[LuaRegisterName.B].value)
            elif self.type == LuaInstructionType.AC:
                return str(self.registers[LuaRegisterName.C].value)
            elif self.type == LuaInstructionType.ABx:
                return str(self.registers[LuaRegisterName.Bx].value)
            elif self.type == LuaInstructionType.ABC:
                return str(self.registers[LuaRegisterName.B].value)
            return ""
        elif index == 2:
            if self.type == LuaInstructionType.ABC:
                return str(self.registers[LuaRegisterName.C].value)
            return ""

    def __str__(self):
        if self.type == LuaInstructionType.A:
            return f"{self.opcode} {self.registers[LuaRegisterName.A]}"
        elif self.type == LuaInstructionType.AB:
            return f"{self.opcode} {self.registers[LuaRegisterName.A]} {self.registers[LuaRegisterName.B]}"
        elif self.type == LuaInstructionType.AC:
            return f"{self.opcode} {self.registers[LuaRegisterName.A]} {self.registers[LuaRegisterName.C]}"
        elif self.type == LuaInstructionType.ABx:
            return f"{self.opcode} {self.registers[LuaRegisterName.A]} {self.registers[LuaRegisterName.Bx]}"
        elif self.type == LuaInstructionType.AsBx:
            return f"{self.opcode} {self.registers[LuaRegisterName.A]} {self.registers[LuaRegisterName.sBx]}"
        elif self.type == LuaInstructionType.ABC:
            return f"{self.opcode} {self.registers[LuaRegisterName.A]} {self.registers[LuaRegisterName.B]} {self.registers[LuaRegisterName.C]}"