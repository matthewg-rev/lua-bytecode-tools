from termcolor import colored
from enum import Enum, auto
import os
import argparse
import sys

from output_system import OutputSystem, OutputType

from tooling_state import ToolingState
from lua_bytecode import LuaBytecode
from lua_instruction import LuaInstructionType, LuaRegisterName
from working_data import WorkingDataObjects, WorkingType

tool_state = ToolingState()

parser = argparse.ArgumentParser()
parser.add_argument('file', type=argparse.FileType('rb'), help='File for tooling to work with.')

args = parser.parse_args()
tool_state.working_file = args.file
fileString = tool_state.working_file.read()
tool_state.working_code = LuaBytecode.read(fileString)

def input_prefix():
    if tool_state.selected_data is None:
        return f"@{colored('file', 'grey')}>> "
    if tool_state.selected_data.userDefinedTag is None:
        return f"@{colored(str(tool_state.selected_data.type) + ':' + hex(tool_state.selected_data.address), 'grey')}>> "
    return f"@{colored(str(tool_state.selected_data.type), 'grey') + ':' + colored(tool_state.selected_data.userDefinedTag, 'yellow')}>> "

class ErrorCatchingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)
    
    def exit(self, status=0, message=None):
        raise SystemExit(message)

print(colored("lua-bytecode-tooling", "light_blue"))
print("")
print("developed by @matthewg-rev")
print("type 'help' for help.")
print("")

output_system = OutputSystem()

def output_function_signature(data = None):
    if data is None:
        data = tool_state.selected_data

    functionSignature = "{}[{}] @ {}"
    kw1 = output_system.color_from_type("function", OutputType.KEYWORD)
    sizeCode = output_system.color_from_type(str(len(data.value.instructions)), OutputType.NUMBER)
    if data.userDefinedTag is None:
        address = output_system.color_from_type(hex(data.address), OutputType.ADDRESS)
        print(functionSignature.format(kw1, sizeCode, address))
    else:
        tag = output_system.color_from_type(data.userDefinedTag, OutputType.TAG)
        print(functionSignature.format(kw1, sizeCode, tag))

while True:
    command = input(input_prefix()).split(' ')
    commandName = command[0]
    if commandName == 'exit':
        sys.exit(0)
    elif commandName == 'pseudo':
        if tool_state.selected_data is None:
            print(output_system.color_from_type("error: no data selected.", OutputType.ERROR))
            continue
        if tool_state.selected_data.type != WorkingType.FUNCTION:
            print(output_system.color_from_type("error: selected data is not a function.", OutputType.ERROR))
            continue

        output_function_signature()

        output_system.load_format("{:<10} {:<15}")
        for i, instruction in enumerate(tool_state.selected_data.value.instructions):
            output_system.add_data(hex(instruction.address), OutputType.ADDRESS)
            instruction.value.pseudo(output_system)
            output_system.end_of_line()
        output_system.print_data()
        output_system.clear_format()
    elif commandName == 'addr':
        if tool_state.selected_data is None:
            print(output_system.color_from_type("error: no data selected.", OutputType.ERROR))
            continue
        print(output_system.color_from_type(hex(tool_state.selected_data.address), OutputType.ADDRESS))
    elif commandName == 'list':
        try:
            parser = ErrorCatchingArgumentParser(exit_on_error=False)
            parser.add_argument('type', choices=['functions', 'instructions', 'constants', 'locals', 'upvalues'], help='Type of data to list.')

            args = parser.parse_args(command[1:])
            if args.type == 'functions':
                for data in WorkingDataObjects:
                    if data.type == WorkingType.FUNCTION:
                        output_function_signature(data)
            
            elif args.type == 'instructions':
                if tool_state.selected_data is None:
                    print(output_system.color_from_type("error: no data selected.", OutputType.ERROR))
                    continue
                if tool_state.selected_data.type != WorkingType.FUNCTION:
                    print(output_system.color_from_type("error: selected data is not a function.", OutputType.ERROR))
                    continue

                output_function_signature()
                output_system.load_format("{:<10} {:<15} {:<20} {:<3} {:<3} {:<3}")
                for i, instruction in enumerate(tool_state.selected_data.value.instructions):
                    output_system.add_data(hex(instruction.address), OutputType.ADDRESS)
                    output_system.add_data('[' + str(int(instruction.value.opcode)) + ']', OutputType.NUMBER)
                    output_system.add_data(instruction.value.opcode, OutputType.INSTRUCTION)
                    
                    r1_val = instruction.value.get_register(0)
                    r2_val = instruction.value.get_register(1)
                    r3_val = instruction.value.get_register(2)

                    r1_val = str(r1_val) if r1_val is not None else ''
                    r2_val = str(r2_val) if r2_val is not None else ''
                    r3_val = str(r3_val) if r3_val is not None else ''

                    output_system.add_data(r1_val, OutputType.REGISTER)
                    output_system.add_data(r2_val, OutputType.REGISTER)
                    output_system.add_data(r3_val, OutputType.REGISTER)
                    output_system.end_of_line()
                output_system.print_data()
                output_system.clear_format()
            elif args.type == 'constants':
                if tool_state.selected_data is None:
                    print(output_system.color_from_type("error: no data selected.", OutputType.ERROR))
                    continue
                if tool_state.selected_data.type != WorkingType.FUNCTION:
                    print(output_system.color_from_type("error: selected data is not a function.", OutputType.ERROR))
                    continue

                output_function_signature()
                
                output_system.load_format("{:<10} {}{}{:<10} {:<20}")
                for i, constant in enumerate(tool_state.selected_data.value.constants):
                    output_system.add_data(hex(constant.address), OutputType.ADDRESS)

                    output_system.add_data('[')
                    output_system.add_data(str(constant.value.type), OutputType.CONSTANTTYPE)
                    output_system.add_data(']')

                    output_system.add_data(constant.value.value, OutputType.CONSTANT)
                    output_system.end_of_line()
                output_system.print_data()
                output_system.clear_format()
        except argparse.ArgumentError as e:
            print(output_system.color_from_type(f"error: {e}", OutputType.ERROR))
            continue
    elif commandName == 'select':
        try:
            parser = ErrorCatchingArgumentParser(exit_on_error=False)
            parser.add_argument('type', choices=['address', 'tag'], help='Address of data to select.')
            parser.add_argument('value', type=str, help='value with respect to type.')

            args = parser.parse_args(command[1:])
            if args.type == 'address':
                address = int(args.value, 16)
                for data in WorkingDataObjects:
                    if data.address == address:
                        tool_state.selected_data = data
                        break
            elif args.type == 'tag':
                for data in WorkingDataObjects:
                    if data.userDefinedTag == args.value:
                        tool_state.selected_data = data
                        break
        except argparse.ArgumentError as e:
            print(output_system.color_from_type(f"error: {e}", OutputType.ERROR))
            continue
    elif commandName == 'tag':
        try:
            parser = ErrorCatchingArgumentParser(exit_on_error=False)
            parser.add_argument('tag', type=str, help='tag for the selected data.')

            args = parser.parse_args(command[1:])
            if tool_state.selected_data is not None:
                tool_state.selected_data.userDefinedTag = args.tag
        except argparse.ArgumentError as e:
            print(output_system.color_from_type(f"error: {e}", OutputType.ERROR))
            continue
    elif commandName == 'clear':
        os.system('cls')
    elif commandName == 'help':
        print("list: list data of a certain type")
        print("select: select data by address or tag")
        print("tag: tag the selected data")
        print("exit: exit the tooling")
        print("help: print this help message")