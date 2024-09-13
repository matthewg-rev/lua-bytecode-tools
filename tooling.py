from termcolor import colored
import argparse
import sys

from tooling_state import ToolingState
from lua_bytecode import LuaBytecode
from working_data import WorkingDataObjects, WorkingType

tool_state = ToolingState()

parser = argparse.ArgumentParser()
parser.add_argument('file', type=argparse.FileType('r'), help='File for tooling to work with.')

args = parser.parse_args()
tool_state.working_file = args.file
fileString = tool_state.working_file.read()
fileBytes = fileString.encode('utf-8')
tool_state.working_code = LuaBytecode.read(fileBytes)

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

while True:
    command = input(input_prefix()).split(' ')
    commandName = command[0]
    if commandName == 'exit':
        sys.exit(0)
    elif commandName == 'list':
        try:
            parser = ErrorCatchingArgumentParser(exit_on_error=False)
            parser.add_argument('type', choices=['functions', 'instructions', 'constants', 'locals', 'upvalues'], help='Type of data to list.')

            args = parser.parse_args(command[1:])
            if args.type == 'functions':
                for data in WorkingDataObjects:
                    if data.type == WorkingType.FUNCTION:
                        if data.userDefinedTag is None:
                            print(f"{colored('function', 'green')}[{colored(len(data.value.instructions), 'light_magenta')}] @ {colored(hex(data.address), 'cyan')}")
                        else:
                            print(f"{colored('function', 'green')}[{colored(len(data.value.instructions), 'light_magenta')}] @ {colored(data.userDefinedTag, 'yellow')}")
            elif args.type == 'instructions':
                if tool_state.selected_data is None:
                    print(colored("error: no data selected.", 'light_red'))
                    continue
                if tool_state.selected_data.type != WorkingType.FUNCTION:
                    print(colored("error: selected data is not a function.", 'light_red'))
                    continue

        except argparse.ArgumentError as e:
            print(colored(f"error: {e}", 'light_red'))
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
            print(colored(f"error: {e}", 'light_red'))
            continue
    elif commandName == 'tag':
        try:
            parser = ErrorCatchingArgumentParser(exit_on_error=False)
            parser.add_argument('tag', type=str, help='tag for the selected data.')

            args = parser.parse_args(command[1:])
            if tool_state.selected_data is not None:
                tool_state.selected_data.userDefinedTag = args.tag
        except argparse.ArgumentError as e:
            print(colored(f"error: {e}", 'light_red'))
            continue
    elif commandName == 'help':
        print("list: list data of a certain type")
        print("select: select data by address or tag")
        print("tag: tag the selected data")
        print("exit: exit the tooling")
        print("help: print this help message")