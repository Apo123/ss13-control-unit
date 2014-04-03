; The sample program if you examine the emulator, 30A0B01181
	and 0 ; and rr (0 by default) with input 0 (1 by default), setting rr to 0
	ien 0 ; set ien to the value contained in input 0
	oen 0 ; set ien to the value contained in input 0
	ld 1 ; set rr to the value contained in input 1
	sto 1 ; set output pin 1 to the value contained in rr
	
	; After a program's end is reached, the control unit will jump back to the beginning and continue