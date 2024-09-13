from enum import Enum

class ToolingState:
    def __init__(self):
        self.working_file = None
        self.working_code = None
        
        self.selected_data = None