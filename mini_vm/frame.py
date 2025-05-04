class Frame:
    def __init__(self, instructions: list):
        self.instructions = instructions
        self.stack = []
        self.locals = {}
        self.pc = 0  # program counter — текущая позиция
        self.exception_handler = None
