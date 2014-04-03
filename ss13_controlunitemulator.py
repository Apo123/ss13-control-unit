"""
 *	 Instructions: Word size in this setup is one byte, one nibble is the instruction and the other is the operand. In that order. A0 is opcode A operand 0.
 *	 0 and F are NOPs
 *	 1 (LD) loads an input value into the accumulator, RR
 *	 2 (LDC) acts like 1, but with the complement of the input
 *	 3 (AND) sets RR to the logical AND of RR and the input.
 *	 4 (ANDC) sets RR to the logical AND of RR and the complement of the input
 *	 5 (OR) sets RR to the logical OR of RR and the input
 *	 6 (ORC) sets RR to the logical OR of RR and the complement of the input
 *	 7 (XNOR) essentially equates RR and the input, with RR set to the result of the test.
 *	 8 (STO) store RR in either a RAM addess (High 8 bits) or one of 8 outputs (Low 8 bits).
 *	 9 (STOC) store complement of RR in the same was as STO.
 *	 A (IEN) sets IEN to the input
 *	 B (OEN) sets OEN to the input
 *	 C (JMP) will adjust the program counter by up to 32 addresses, forward or backward from the current instruction. Arguments 8+ will subtract 7 and then jump 4x that value forward, less than that will jump back 4x (that value + 1)
 *	 D (RTN) skip next instruction.  For some reason.
 *	 E (SKZ) skip next instruction if RR is zero.
 Output signals have the value "PIN:VALUE" i.e "2:1" to output true on pin 2.  You can filter this with OR gate triggers, ok.
 Example program: "30A0B01181" Will AND RR with !RR (Set it to zero), load !RR (1) into IEN and OEN, then load input 1 and send it to output 1.  This will repeat without end.
"""

(INSTR_NOP, INSTR_LD, INSTR_LDC, INSTR_AND, INSTR_ANDC,
 INSTR_OR, INSTR_ORC, INSTR_XNOR, INSTR_STO, INSTR_STOC,
 INSTR_IEN, INSTR_OEN, INSTR_JMP, INSTR_RTN, INSTR_SKZ, INSTR_NOP2) = range(0x10)

class ControlUnitEmulator():
    def __init__(self, program):
        # Current state of RAM
        self.rammap = { }
        for i in range(1, 8):
            self.rammap[i] = 0
        # Registers
        self.rr = 0
        # Input enable
        self.ien = 0
        # Output enable
        self.oen = 0
        # Current state of input pins
        self.inputpins = { }
        # Input "pin" 0 starts off as the complement of rr (1)
        self.inputpins[0] = 1
        for i in range(1, 8):
            self.inputpins[i] = 0
        # Current state of output pins
        self.outputpins = { }
        for i in range(1, 8):
            self.outputpins[i] = 0
        # The program itself
        self.program = program
        # How far we are into the program
        self.progoffset = 0

    def setInput(self, pin, value):
        self.inputpins[pin] = value

    def printState(self):
        print "RR = " + hex(self.rr)
        print "IEN = " + hex(self.ien)
        print "OEN = " + hex(self.oen)
        print "RAM: "
        for i in range(1, 4):
            print str(i) + ": " + hex(self.rammap[i]),
        print ""
        for i in range(4, 8):
            print str(i) + ": " + hex(self.rammap[i]),
        print "\nInput: "
        for i in range(0, 4):
            print str(i) + ": " + hex(self.inputpins[i]),
        print ""
        for i in range(4, 8):
            print str(i) + ": " + hex(self.inputpins[i]),
        print "\nOutput: "
        for i in range(1, 4):
            print str(i) + ": " + hex(self.outputpins[i]),
        print ""
        for i in range(4, 8):
            print str(i) + ": " + hex(self.outputpins[i]),
        print "\n"

    def singleStep(self):
        print "Handling: " + self.program[self.progoffset:self.progoffset+2]
        opcode, operand = self.readOpcode()
        self.handleOpcode(opcode, operand)
        if self.progoffset != len(self.program):
            return True
        else:
            return False
        
    def readOpcode(self):
        opcode = self.program[self.progoffset]
        operand = self.program[self.progoffset + 1]
        self.progoffset += 2
        return (int(opcode, 16), int(operand, 16))

    def handleOpcode(self, opcode, operand):
        if opcode == INSTR_NOP:
            return
        elif opcode == INSTR_LD:
            # If the operand is 8 or more, we fetch from RAM
            if operand & 0x8:
                operand -= 8
                self.rr = self.rammap[operand]
            else:
                self.rr = self.inputpins[operand]
        elif opcode == INSTR_LDC:
            if operand & 0x8:
                operand -= 8
                self.rr = self.rammap[operand] ^ 0x1
            else:
                self.rr = self.inputpins[operand] ^ 0x1
        elif opcode == INSTR_AND:
            if operand & 0x8:
                operand -= 8
                self.rr = self.rr & self.rammap[operand]
            else:
                self.rr = self.rr & self.inputpins[operand]
        elif opcode == INSTR_ANDC:
            if operand & 0x8:
                operand -= 8
                self.rr = self.rr & self.rammap[operand] ^ 0x1
            else:
                self.rr = self.rr & self.inputpins[operand] ^ 0x1
        elif opcode == INSTR_OR:
            if operand & 0x8:
                operand -= 8
                self.rr = self.rr | self.rammap[operand]
            else:
                self.rr = self.rr | self.inputpins[operand]
        elif opcode == INSTR_ORC:
            if operand & 0x8:
                operand -= 8
                self.rr = self.rr | self.rammap[operand] ^ 0x1
            else:
                self.rr = self.rr | self.inputpins[operand] ^ 0x1
        elif opcode == INSTR_XNOR:
            # This is the python way of saying rr = (rr == operand ? 1 : 0)
            if operand & 0x8:
                operand -= 8
                self.rr = (self.rr == self.rammap[operand] and 1 or 0)
            else:
                self.rr = (self.rr == self.inputpins[operand] and 1 or 0)
        elif opcode == INSTR_STO:
            # If the operand is 8 or more, we store rr in RAM
            if operand & 0x8:
                operand -= 8
                self.rammap[operand] = self.rr
            # Otherwise, we store in an output pin
            else:
                self.outputpins[operand] = self.rr
        elif opcode == INSTR_STOC:
            # If the operand is 8 or more, we store rr in RAM
            if operand & 0x8:
                operand -= 8
                self.rammap[operand] = self.rr ^ 0x1
            # Otherwise, we store in an output pin
            else:
                self.outputpins[operand] = self.rr ^ 0x1
        # Not sure if these are correct
        elif opcode == INSTR_IEN:
            self.ien = operand
        elif opcode == INSTR_OEN:
            self.oen = operand
        elif opcode == INSTR_JMP:
            if operand & 0x8:
                operand -= 7
                self.progoffset += (operand * 8)
            else:
                self.progoffset -= ((operand + 1) * 8)
        elif opcode == INSTR_RTN:
            self.progoffset += 2
        elif opcode == INSTR_SKZ:
            if self.rr == 0:
                self.progoffset += 2
        elif opcode == INSTR_NOP2:
            return

if __name__ == "__main__":
    c = ControlUnitEmulator("30A0B01181")
    while c.singleStep():
        c.printState()
    c.printState()
