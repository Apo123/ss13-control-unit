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

# Basic mnemonics
mnems = { "nop": INSTR_NOP, "ld": INSTR_LD, "ldc": INSTR_LDC,
          "and": INSTR_AND, "andc": INSTR_ANDC, "or": INSTR_OR,
          "orc": INSTR_ORC, "xnor": INSTR_XNOR, "sto": INSTR_STO,
          "stoc": INSTR_STOC, "ien": INSTR_IEN, "oen": INSTR_OEN,
          "jmp": INSTR_JMP, "ret": INSTR_RTN, "skz": INSTR_SKZ }

"""
Macro definitions:
    Key is the mnemonic you want to have translated
    Value is the actual macro expansion.
    
    A list of tuples is expected. Each tuple should have a string representation for the instruction, and the arguments to pass in.
    Specify a negative number to use an argument to the macro, specify a positive number to use a literal value. 

    For example, our definition of "xor" is as follows:
        "xor": [("xnor", -1), ("ldc", 0)]

    This translates to:

    "xor" - Mnemonic for the macro
    ("xnor", -1) - The first instruction the macro resolves to. This uses xnor with the first argument passed in. "xor 2" would translate this line to "xnor 2".
    ("ldc", 0) - The second instruction the macro resolves to. This uses ldc with the literal argument 0.

    Therefore, having the line "xor 2" in your code would expand to the following:
        xnor 2
        ldc 0

    Macros are expanded recursively until they consist only of basic mnemonics. This allows you to have macros that reference other macros.
"""
macros = {
            # Some convenience macros
            "nand": [
                ("andc", -1)
                ],
            "nor": [
                ("orc", -1)
                ],
            "jz": [
                ("skz"),
                ("jmp", -1)
                ],
            "jnz": [
                ("skz", 1),
                ("jmp", 1),
                ("nop"),
                ("nop"),
                ("nop"),
                ("jmp", -1)
                ],
            "xor": [
                ("xnor", -1),
                ("ldc", 0)
                ]
         }

class ControlUnitAssembler():
    def __init__(self, verbosemode):
        self.verbose = verbosemode
        pass

    # Accepts a list of tuples where each tuple has the form (opcode, operand)
    def build(self, program):
        ret = ""
        for item in program:
            ret += hex(item[0])[2:] + hex(item[1])[2:]
        return ret

    # Recursively expand a macro
    def expandMacro(self, macroparams):
        expanded = []
        # Fetch the definition for this macro
        macrodef = macros[macroparams[0]]
        for item in macrodef:
            instr = item[0]
            # Check if this is a basic mnemonic
            if instr in mnems:
                # If so, make sure there is only one argument
                if len(item) > 2:
                    raise Exception("Too many parameters in macro definition")
                # Is this a literal argument or a reference to a parameter passed in to us?
                arg = item[1]
                if arg < 0:
                    if -arg >= len(macroparams):
                        raise Exception("Too few parameters for macro expansion")
                    arg = macroparams[-arg]
                expanded.append((mnems[instr], int(str(arg), 16)))
            else:
                # Make sure this is another macro
                if instr not in macros:
                    raise Exception("Unknown instruction in macro expansion: " + instr)
                # OK, this is another macro. Translate arguments, then translate the macro.
                transmacroparams = [instr]
                # Handle the macro arguments
                for i in range(1, len(item)):
                    # Is this a literal argument or a reference to a parameter passed in to us?
                    arg = item[i]
                    if arg < 0:
                        if -arg >= len(macroparams):
                            raise Exception("Too few parameters for macro expansion")
                        arg = macroparams[-arg]
                    transmacroparams.append(str(arg))
                expanded.extend(self.expandMacro(transmacroparams))
        return expanded
                    

    def assembleLine(self, line):
        # Treat ; as comment
        line = line.split(";")[0]
        mo = line.strip().split(" ")
        if self.verbose:
            print mo
        # Check for an empty line
        if (len(mo) == 0) or mo[0] == "":
            return None
        instr = mo[0].lower()
        if (len(mo) == 1):
            # Check for instructions that don't require arguments
            if instr == "skz" or instr == "nop" or instr == "ret":
                return (mnems[instr], 1)
        operand = mo[1]
        if instr not in mnems:
            if instr not in macros:
                raise Exception("Unknown instruction: " + instr)
            else:
                return self.expandMacro(mo)
        else:
            if len(mo) > 2:
                raise Exception("Too many parameters")
        if operand == "!rr":
            operand = 0
        else:
            operand = int(operand, 16)
        return (mnems[instr], operand)

    def assembleProgram(self, program):
        assembled = []
        curline = 1
        for line in program.split("\n"):
            try:
                b = self.assembleLine(line)
                if b != None:
                    # If the line expanded to a macro, add each resulting tuple to our list
                    if type(b) == type([]):
                        assembled.extend(b)
                    # Otherwise, we only need to add the single returned tuple
                    else:
                        assembled.append(b)
                curline += 1
            except Exception, e:
                raise Exception(str(e) + " on line " + str(curline))
        if self.verbose:
            print assembled
        return self.build(assembled)

    def assembleFile(self, filename):
        f = open(filename, "r")
        d = f.read()
        f.close()
        if self.verbose:
            print d
        return self.assembleProgram(d)

if __name__ == "__main__":
    prog = ControlUnitAssembler(False)
    p = prog.assembleFile("ss13_controlunit_testing.asm")
    print p
