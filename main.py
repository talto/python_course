from mini_vm.virtual_machine import VirtualMachine
from mini_vm.instruction import Instruction
from mini_vm.opcodes import *

if __name__ == "__main__":
    instructions = [
        Instruction(LOAD_CONST, 2),
        Instruction(LOAD_CONST, 3),
        Instruction(COMPARE_OP, "<"), 
    ]

    vm = VirtualMachine()
    result = vm.run(instructions)
    print(result)
