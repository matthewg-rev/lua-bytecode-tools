from io import BytesIO
from enum import IntEnum, Enum, auto
from termcolor import colored
from output_system import OutputSystem, OutputType
from working_data import WorkingDataObjects, WorkingType, WorkingData

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

def isRK(reg):
    return ((reg) & (1 << (9 - 1)))

def RK(chunk, reg, output_system):
    if isRK(reg):
        if reg-256 < len(chunk.constants):
            return f"{output_system.color_from_type(chunk.constants[reg-256].value.value, OutputType.CONSTANT)}"
        return f"K({output_system.color_from_type(reg, OutputType.REGISTER)})"
    return f"R({output_system.color_from_type(reg, OutputType.REGISTER)})"

def UPV(chunk, reg, output_system):
    if reg < len(chunk.debug['upvalues']):
        return f"{output_system.color_from_type(chunk.debug['upvalues'][reg].value.value, OutputType.CONSTANT)}"
    return f"upvalues[{output_system.color_from_type(reg, OutputType.REGISTER)}]"

# TODO: fix multiple registers
def multiple_registers(start, end, output_system):
    if start == end or end < start:
        return f"R({output_system.color_from_type(start, OutputType.REGISTER)})"
    return ", ".join([f"R({output_system.color_from_type(i, OutputType.REGISTER)})" for i in range(start, end + 1)])

def multiple_registers_set(start, end, output_system):
    if start == end or end < start:
        return f"R({output_system.color_from_type(start, OutputType.REGISTER)})" + " = "
    return ", ".join([f"R({output_system.color_from_type(i, OutputType.REGISTER)})" for i in range(start, end + 1)]) + " = "

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
        self.chunk = None
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
            instruction.registers[LuaRegisterName.sBx].value = ((raw >> 14) & 0x3FFFF) - 131071
        elif instruction.type == LuaInstructionType.ABC:
            instruction.registers[LuaRegisterName.A].value = (raw >> 6) & 0xFF
            instruction.registers[LuaRegisterName.B].value = (raw >> 23) & 0x1FF
            instruction.registers[LuaRegisterName.C].value = (raw >> 14) & 0x1FF
        elif instruction.type == LuaInstructionType.sBx:
            instruction.registers[LuaRegisterName.sBx].value = ((raw >> 14) & 0x3FFFF) - 131071

        return instruction
    
    def get_register(self, index: int):
        if index == 0:
            if self.type == LuaInstructionType.sBx:
                return self.registers[LuaRegisterName.sBx].value
            return self.registers[LuaRegisterName.A].value
        elif index == 1:
            if self.type == LuaInstructionType.AB:
                return self.registers[LuaRegisterName.B].value
            elif self.type == LuaInstructionType.AC:
                return self.registers[LuaRegisterName.C].value
            elif self.type == LuaInstructionType.ABx:
                return self.registers[LuaRegisterName.Bx].value
            elif self.type == LuaInstructionType.ABC:
                return self.registers[LuaRegisterName.B].value
            return None
        elif index == 2:
            if self.type == LuaInstructionType.ABC:
                return self.registers[LuaRegisterName.C].value
            return None
        
    def pseudo(self, output_system):
        def reg(index):
            return f"R({output_system.color_from_type(self.get_register(index), OutputType.REGISTER)})"
        def reg_no_get(index):
            return f"R({output_system.color_from_type(index, OutputType.REGISTER)})"
        def kst(index):
            return f"{output_system.color_from_type(self.chunk.constants[self.get_register(index)].value.value, OutputType.CONSTANT)}"
        
        match self.opcode:
            case LuaOpcode.MOVE:
                reg1 = reg(0)
                reg2 = reg(1)
                output_system.add_data(f"{reg1} = {reg2}")
            case LuaOpcode.LOADK:
                reg1 = reg(0)
                reg2 = kst(1)
                output_system.add_data(f"{reg1} = {reg2}")
            case LuaOpcode.LOADBOOL:
                reg1 = reg(0)
                reg2 = f"{output_system.color_from_type(self.get_register(1), OutputType.REGISTER)}"
                nm1 = f"{output_system.color_from_type(1, OutputType.NUMBER)}"
                pc = f"{output_system.color_from_type('PC', OutputType.INSTRUCTION)}++" if self.get_register(2) != 0 else ""
                output_system.add_data(f"{reg1} = {reg2} == {nm1} {pc}")
            case LuaOpcode.LOADNIL:
                registers = multiple_registers(self.get_register(0), self.get_register(1), output_system)
                output_system.add_data(f"{registers} = {output_system.color_from_type('nil', OutputType.CONSTANT)}")
            case LuaOpcode.GETUPVAL:
                reg1 = reg(0)
                reg2 = UPV(self.chunk, self.get_register(1), output_system)
                output_system.add_data(f"{reg1} = {reg2}")
            case LuaOpcode.GETGLOBAL:
                reg1 = reg(0)
                reg2 = f"_G[{kst(1)}]"
                output_system.add_data(f"{reg1} = {reg2}")
            case LuaOpcode.GETTABLE:
                reg1 = reg(0)
                reg2 = reg(1)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2}[{reg3}]")
            case LuaOpcode.SETGLOBAL:
                reg1 = kst(1)
                reg2 = reg(0)
                output_system.add_data(f"_G[{reg1}] = {reg2}")
            case LuaOpcode.SETUPVAL:
                reg1 = UPV(self.chunk, self.get_register(1), output_system)
                reg2 = reg(0)
                output_system.add_data(f"{reg1} = {reg2}")
            case LuaOpcode.SETTABLE:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1}[{reg2}] = {reg3}")
            case LuaOpcode.NEWTABLE:
                reg1 = reg(0)
                reg2 = f"newtable({reg(1)}, {reg(2)})"
            case LuaOpcode.SELF:
                reg1 = reg_no_get(self.get_register(0) + 1)
                reg2 = reg(1)
                reg3 = reg(0)
                rk1 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2}; {reg3} = {reg2}[{rk1}]")
            case LuaOpcode.ADD:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2} + {reg3}")
            case LuaOpcode.SUB:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
            case LuaOpcode.SUB:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2} - {reg3}")
            case LuaOpcode.MUL:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2} * {reg3}")
            case LuaOpcode.DIV:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2} / {reg3}")
            case LuaOpcode.MOD:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2} % {reg3}")
            case LuaOpcode.POW:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
            case LuaOpcode.POW:
                reg1 = reg(0)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                output_system.add_data(f"{reg1} = {reg2} ^ {reg3}")
            case LuaOpcode.UNM:
                reg1 = reg(0)
                reg2 = reg(1)
                output_system.add_data(f"{reg1} = -{reg2}")
            case LuaOpcode.NOT:
                reg1 = reg(0)
                reg2 = reg(1)
                kw1 = output_system.color_from_type("not", OutputType.KEYWORD)
                output_system.add_data(f"{reg1} = {kw1} {reg2}")
            case LuaOpcode.LEN:
                reg1 = reg(0)
                reg2 = reg(1)
                output_system.add_data(f"{reg1} = len({reg2})")
            case LuaOpcode.CONCAT:
                reg1 = reg(0)
                reg2 = reg(1)
                reg3 = reg(2)
                output_system.add_data(f"{reg1} = {reg2} .. ... .. {reg3}")
            case LuaOpcode.JMP:
                reg1 = output_system.color_from_type(self.get_register(0), OutputType.NUMBER)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"{pc} += {reg1}")
            case LuaOpcode.EQ:
                reg1 = output_system.color_from_type(self.get_register(0), OutputType.REGISTER)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"if ({reg2} == {reg3}) != {reg1} then {pc}++")
            case LuaOpcode.LT:
                reg1 = output_system.color_from_type(self.get_register(0), OutputType.REGISTER)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"if ({reg2} < {reg3}) != {reg1} then {pc}++")
            case LuaOpcode.LE:
                reg1 = output_system.color_from_type(self.get_register(0), OutputType.REGISTER)
                reg2 = RK(self.chunk, self.get_register(1), output_system)
                reg3 = RK(self.chunk, self.get_register(2), output_system)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"if ({reg2} <= {reg3}) != {reg1} then {pc}++")
            case LuaOpcode.TEST:
                reg1 = output_system.color_from_type(self.get_register(0), OutputType.REGISTER)
                reg2 = output_system.color_from_type(self.get_register(1), OutputType.NUMBER)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"if not ({reg1} <=> {reg2}) then {pc}++")
            case LuaOpcode.TESTSET:
                reg1 = output_system.color_from_type(self.get_register(0), OutputType.REGISTER)
                reg2 = output_system.color_from_type(self.get_register(1), OutputType.REGISTER)
                reg3 = output_system.color_from_type(self.get_register(2), OutputType.NUMBER)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"if not ({reg2} <=> {reg3}) then {reg1} = {reg2}; {pc}++")
            case LuaOpcode.CALL:
                call_reg = reg(0)
                A = self.get_register(0)
                B = self.get_register(1)
                C = self.get_register(2)

                if B == 0:
                    # if B == 0, then function params are from R(A+1) to top of the stack.
                    call_args = reg_no_get(A+1)
                elif B == 1:
                    call_args = ""
                elif B >= 2:
                    call_args = multiple_registers(A + 1, A + B - 1, output_system)

                if C == 0:
                    results = reg(0) + " = "
                elif C == 1:
                    results = ""
                elif C >= 2:
                    results = multiple_registers_set(A, A + C - 2, output_system)

                output_system.add_data(f"{results}{call_reg}({call_args})")
            case LuaOpcode.TAILCALL:
                call_reg = reg(0)
                call_args = multiple_registers(self.get_register(0) + 1, self.get_register(0) + self.get_register(1) - 1, output_system)
                output_system.add_data(f"return {call_reg}({call_args})")
            case LuaOpcode.RETURN:
                A = self.get_register(0)
                B = self.get_register(1)
                if B == 1:
                    return_regs = ""
                elif B == 0:
                    return_regs = multiple_registers(A, A + self.chunk.maxStackSize - 1, output_system)
                elif B >= 2:
                    return_regs = multiple_registers(self.get_register(0), self.get_register(0) + self.get_register(1) - 2, output_system)

                output_system.add_data(f"return {return_regs}")
            case LuaOpcode.FORLOOP:
                reg1 = reg(0)
                reg2 = reg_no_get(self.get_register(0) + 2)
                reg3 = reg_no_get(self.get_register(0) + 1)
                reg4 = reg_no_get(self.get_register(0) + 3)
                pcInc = output_system.color_from_type(self.get_register(1), OutputType.NUMBER)
                pc = output_system.color_from_type("PC", OutputType.KEYWORD)
                output_system.add_data(f"{reg1} += {reg2}; if {reg1} <?= {reg3} then {pc} += {pcInc} {reg4} = {reg1};")
            case LuaOpcode.FORPREP:
                reg1 = reg(0)
                reg2 = reg_no_get(self.get_register(0) + 2)
                pcInc = output_system.color_from_type(self.get_register(1), OutputType.NUMBER)
                pc = output_system.color_from_type("PC", OutputType.INSTRUCTION)
                output_system.add_data(f"{reg1} -= {reg2}; {pc} += {pcInc}")
            case LuaOpcode.TFORLOOP:
                set_regs = multiple_registers_set(
                    self.get_register(0)+3,
                    self.get_register(0)+2+self.get_register(1)
                )
                call_reg = reg(0)
                call_args = multiple_registers(self.get_register(0)+1, self.get_register(0)+2)
                cond = reg_no_get(self.get_register(0) + 3)
                nil = output_system.color_from_type("nil", OutputType.CONSTANT)
                reg1 = reg_no_get(self.get_register(0) + 2)
                reg2 = reg_no_get(self.get_register(0) + 3)
                pc = output_system.color_from_type("PC", OutputType.INSTRUCTION)
                output_system.add_data(f"{set_regs}{call_reg}({call_args}) if {cond} ~= {nil} then {reg1}={reg2} else {pc}++")
            case LuaOpcode.SETLIST:
                output_system.add_data("TODO: SETLIST")
            case LuaOpcode.CLOSE:
                output_system.add_data("TODO: CLOSE")
            case LuaOpcode.CLOSURE:
                line = "{} = {}[{}] @ {}"
                reg1 = reg(0)
                kw1 = output_system.color_from_type("function", OutputType.KEYWORD)

                closure = self.chunk.chunks[self.get_register(1)]
                closure = [data for data in WorkingDataObjects if data.address == closure.__startAddress__][0]

                sizeCode = output_system.color_from_type(len(closure.value.instructions), OutputType.NUMBER)

                addressOrTag = None
                if closure.userDefinedTag is None:
                    addressOrTag = output_system.color_from_type(hex(closure.address), OutputType.ADDRESS)
                else:
                    addressOrTag = output_system.color_from_type(closure.userDefinedTag, OutputType.TAG)
                output_system.add_data(line.format(reg1, kw1, sizeCode, addressOrTag))
            case LuaOpcode.VARARG:
                output_system.add_data("TODO: VARARG")
            case _:
                output_system.add_data(None)
        #InstructionPseudoLookup[self.opcode](self.chunk, self, output_system)

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