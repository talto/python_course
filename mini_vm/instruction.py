class Instruction:
    def __init__(self, opcode: str, argument=None):
        self.opcode = opcode
        self.argument = argument

    def __repr__(self):
        return f"Instruction({self.opcode}, {self.argument})"