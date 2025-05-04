from .frame import Frame
from .opcodes import *
from .instruction import Instruction

class VirtualMachine:
    def __init__(self):
        self.frames = []
        self.frame = None

    def run(self, instructions: list[Instruction]):
        frame = Frame(instructions)
        self.frames.append(frame)
        self.frame = frame
        return self.run_frame()

    def run_frame(self):
        frame = self.frame
        while frame.pc < len(frame.instructions):
            instr = frame.instructions[frame.pc]
            frame.pc += 1
            self.dispatch(instr)
        return frame.stack.pop()

    def dispatch(self, instr: Instruction):
        opcode = instr.opcode
        arg = instr.argument

        if opcode == LOAD_CONST:
            self.frame.stack.append(arg)

        elif opcode == STORE_NAME:
            value = self.frame.stack.pop()
            self.frame.locals[arg] = value

        elif opcode == LOAD_NAME:
            value = self.frame.locals[arg]
            self.frame.stack.append(value)

        elif opcode == BINARY_ADD:
            b = self.frame.stack.pop()
            a = self.frame.stack.pop()
            self.frame.stack.append(a + b)

        elif opcode == RETURN_VALUE:
            pass  
        elif opcode == POP_JUMP_IF_FALSE:
            value = self.frame.stack.pop()
            if not value:
                self.frame.pc = arg  
        elif opcode == JUMP_FORWARD:
            self.frame.pc = arg
        elif opcode == COMPARE_OP:
            b = self.frame.stack.pop()
            a = self.frame.stack.pop()
            if arg == "<":
                self.frame.stack.append(a < b)
            elif arg == ">":
                self.frame.stack.append(a > b)
            elif arg == "==":
                self.frame.stack.append(a == b)
            else:
                raise Exception(f"Unknown COMPARE_OP argument: {arg}")
        elif opcode == JUMP_BACKWARD:
            self.frame.pc = arg
        elif opcode == SETUP_EXCEPT:
                # arg — индекс, куда перейти в случае исключения
            self.frame.exception_handler = arg
        
        elif opcode == RAISE_EXCEPTION:
            # эмулируем исключение: прыгаем на exception_handler
            if self.frame.exception_handler is None:
                raise Exception("Unhandled exception in VM")
            self.frame.stack.clear()  # очищаем стек как при исключении
            self.frame.pc = self.frame.exception_handler
        
        elif opcode == POP_BLOCK:
            # очищаем обработчик исключения
            self.frame.exception_handler = None


        else:
            raise Exception(f"Unknown opcode {opcode}")
