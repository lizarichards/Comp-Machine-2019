"""
Project: Duck Machine

Name: Liza Richards
Duck Machine model DM2020W CPU
"""

from instr_format import Instruction, OpCode, CondFlag, decode
from typing import Tuple
from memory import Memory
from register import Register, ZeroRegister
from mvc import MVCEvent, MVCListenable
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class ALU(object):
    """The arithmetic logic unit (also called a "functional unit"
    in a modern CPU) executes a selected function but does not
    otherwise manage CPU state. A modern CPU core may have several
    ALUs to boost performance by performing multiple operatons
    in parallel, but the Duck Machine has just one ALU in one core.
    """
    # The ALU chooses one operation to apply based on a provided
    # operation code.  These are just simple functions of two arguments;
    # in hardware we would use a multiplexer circuit to connect the
    # inputs and output to the selected circuitry for each operation.
    ALU_OPS = {
        OpCode.ADD: lambda x, y: x + y,
        OpCode.SUB: lambda x, y: x - y,
        OpCode.MUL: lambda x, y: x * y,
        OpCode.DIV: lambda x, y: x // y,
        # FIXME:  We need subtraction, multiplication, division
        #
        # For memory access operations load, store, the ALU
        # performs the address calculation
        OpCode.LOAD: lambda x, y: x + y,
        OpCode.STORE: lambda x, y: x + y,
        # Some operations perform no operation
        OpCode.HALT: lambda x, y: 0
    }

    def exec(self, op: OpCode, in1: int, in2: int) -> Tuple[int, CondFlag]:
        try:
            global ALU_OPS
            result = ALU.ALU_OPS[op](in1, in2)
            if result == 0:
                return result, CondFlag.Z
            elif result < 0:
                return result, CondFlag.M
            else:
                return result, CondFlag.P
        except ZeroDivisionError:
            return 0, CondFlag.V

class CPUStep(MVCEvent):
    """CPU is beginning step with PC at a given address"""
    def __init__(self, subject: "CPU", pc_addr: int,
                 instr_word: int, instr: Instruction)-> None:
        self.subject = subject
        self.pc_addr = pc_addr
        self.instr_word = instr_word
        self.instr = instr

class CPU(MVCListenable):
    """Duck Machine central processing unit (CPU)
    has 16 registers (including r0 that always holds zero
    and r15 that holds the program counter), a few
    flag registers (condition codes, halted state),
    and some logic for sequencing execution.  The CPU
    does not contain the main memory but has a bus connecting
    it to a separate memory.
    """
    def __init__(self, memory: Memory):
        super().__init__()
        self.memory = memory  # Not part of CPU; what we really have is a connection
        self.registers = [ ZeroRegister(), Register(), Register(), Register(),
                           Register(), Register(), Register(), Register(),
                           Register(), Register(), Register(), Register(),
                           Register(), Register(), Register(), Register() ]
        self.condition = CondFlag.ALWAYS
        self.halted = False
        self.alu = ALU()
        self.pc = self.registers[15]

    def step(self):
        '''fetch, decode, and execute part of CPU'''
        # Fetch
        address = self.registers[15].get()
        result = self.memory.get(address)

        # Decode
        instr = decode(result)
        # Display the CPU state when we have decoded the instruction,
        # before we have executed it
        self.notify_all(CPUStep(self, address, result, instr))

        #Execute
        if instr.cond.value & self.condition.value > 0:
            left = self.registers[instr.reg_src1].get()
            right = self.registers[instr.reg_src2].get() + instr.offset
            prog = self.pc.get()
            self.pc.put((prog + 1))
            value, flag = ALU.exec(self.alu, instr.op, left, right)
            if instr.op == OpCode.ADD or instr.op == OpCode.SUB or instr.op == OpCode.MUL or instr.op == OpCode.DIV:
                self.registers[instr.reg_target].put(value)
                self.condition = flag
            elif instr.op == OpCode.STORE:
                self.memory.put(value, self.registers[instr.reg_target].get())
                self.condition = flag
            elif instr.op == OpCode.LOAD:
                get = self.memory.get(value)
                self.registers[instr.reg_target].put(get)
                self.condition = flag
            elif instr.op == OpCode.HALT:
                self.halted = True
        else:
            prog1 = self.registers[15].get()
            self.registers[15].put(prog1 + 1)

    def run(self, from_addr=0,  single_step=False) -> None:
        '''executes fetch, decode, and execute parts of step over and over again'''
        self.halted = False
        self.pc.put(from_addr)
        step_count = 0
        while not self.halted:
            if single_step:
                input("Step {}; press enter".format(step_count))
            self.step()
            step_count += 1










