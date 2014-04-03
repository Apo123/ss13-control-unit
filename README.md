Space Station 13 Control Unit Emulator and Assembler
=================

These scripts are still a work in progress!

This is an attempt to create a macro assembler and an emulator for the Mechanic's new Control Unit in Space Station 13.

Note that the emulator has many, many assumptions built into it (such as input/output pins being separate). These will need to be corrected as more experimentation is done.

Current assumptions in the emulator:
  Input/output pins are separate
  IEN being set to 1 doesn't affect the program's state mid-run if inputs suddenly change
  IP is incremented after an instruction is read (meaning jmp calculations are done from AFTER the jmp instruction)
  LD/LDC/AND/ANDC/OR/ORC/XNOR on operands greater than 8 fetches from RAM the same way STO/STOC do
