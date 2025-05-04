import pytest
from mini_vm.instruction import Instruction
from mini_vm.virtual_machine import VirtualMachine
from mini_vm.opcodes import *

def test_simple_addition():
    instructions = [
        Instruction(LOAD_CONST, 10),
        Instruction(LOAD_CONST, 20),
        Instruction(BINARY_ADD),
        Instruction(RETURN_VALUE)
    ]

    vm = VirtualMachine()
    result = vm.run(instructions)
    assert result == 30

def test_variable_assignment():
    instructions = [
        Instruction(LOAD_CONST, 42),
        Instruction(STORE_NAME, "x"),
        Instruction(LOAD_NAME, "x"),
        Instruction(LOAD_CONST, 8),
        Instruction(BINARY_ADD),
        Instruction(RETURN_VALUE)
    ]

    vm = VirtualMachine()
    result = vm.run(instructions)
    assert result == 50

def test_pop_jump_if_false_true_branch():
    vm = VirtualMachine()
    instructions = [
        Instruction(LOAD_CONST, 0),          # x = 0
        Instruction(STORE_NAME, "x"),
        Instruction(LOAD_NAME, "x"),         # if x:
        Instruction(POP_JUMP_IF_FALSE, 6),   # jump to 6 if False (x == 0)
        Instruction(LOAD_CONST, 1),        # y = 1 (if) → пропустим
        Instruction(STORE_NAME, "y"),
        Instruction(LOAD_CONST, 2),        # y = 2 (else)
        Instruction(STORE_NAME, "y"),
        Instruction(LOAD_NAME, "y"),
        Instruction(RETURN_VALUE),
    ]
    result = vm.run(instructions)
    assert result == 2

def test_jump_forward_skips_else_branch():
    vm = VirtualMachine()

    instructions = [
        Instruction(LOAD_CONST, 1),          # x = 1
        Instruction(STORE_NAME, "x"),
        Instruction(LOAD_NAME, "x"),
        Instruction(POP_JUMP_IF_FALSE, 7),   # if not x → skip to else
        Instruction(LOAD_CONST, 100),        # y = 100 (if)
        Instruction(STORE_NAME, "y"),
        Instruction(JUMP_FORWARD, 9),        # skip else
        Instruction(LOAD_CONST, 200),        # y = 200 (else) — пропускается
        Instruction(STORE_NAME, "y"),
        Instruction(LOAD_NAME, "y"),
        Instruction(RETURN_VALUE),
    ]

    result = vm.run(instructions)
    assert result == 100


def test_while_loop_behavior():
    from mini_vm.virtual_machine import VirtualMachine
    from mini_vm.instruction import Instruction
    from mini_vm.opcodes import (
        LOAD_CONST, STORE_NAME, LOAD_NAME,
        BINARY_ADD, COMPARE_OP,
        POP_JUMP_IF_FALSE, JUMP_BACKWARD,
        RETURN_VALUE
    )

    vm = VirtualMachine()

    instructions = [
        Instruction(LOAD_CONST, 0),              # i = 0
        Instruction(STORE_NAME, "i"),

        # loop_start (index 2)
        Instruction(LOAD_NAME, "i"),             # while i < 3:
        Instruction(LOAD_CONST, 3),
        Instruction(COMPARE_OP, "<"),
        Instruction(POP_JUMP_IF_FALSE, 11),      # if not (i < 3): jump to end

        Instruction(LOAD_NAME, "i"),             # i = i + 1
        Instruction(LOAD_CONST, 1),
        Instruction(BINARY_ADD, None),
        Instruction(STORE_NAME, "i"),

        Instruction(JUMP_BACKWARD, 2),           # jump back to condition

        # loop_end
        Instruction(LOAD_NAME, "i"),             # return i
        Instruction(RETURN_VALUE),
    ]

    result = vm.run(instructions)
    assert result == 3

def test_raise_and_catch_exception():
    vm = VirtualMachine()

    instructions = [
        Instruction(SETUP_EXCEPT, 6),          # try:
        Instruction(RAISE_EXCEPTION, None),    # raise
        Instruction(LOAD_CONST, "Should not run"),
        Instruction(STORE_NAME, "x"),
        Instruction(LOAD_CONST, "FAIL"),
        Instruction(RETURN_VALUE),

        # except:
        Instruction(LOAD_CONST, "Handled"),
        Instruction(POP_BLOCK, None),
        Instruction(RETURN_VALUE),
    ]

    result = vm.run(instructions)
    assert result == "Handled"