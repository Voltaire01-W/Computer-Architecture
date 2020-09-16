"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256    # stores the program on load()
        self.reg = [0] * 8      # 8 registers
        self.pc = 0             # current address
        self.fl = 0             # flags
        self.reg[7] = 0xF4      # init registry holding stack pointer

    def load(self):
        """Load a program into memory."""

        # For now, we've just hardcoded a program:

        # program = [
        #     # From print8.ls8
        #     0b10000010, # LDI R0,8
        #     0b00000000,
        #     0b00001000,
        #     0b01000111, # PRN R0
        #     0b00000000,
        #     0b00000001, # HLT
        # ]

        # grab a file through sys.argv, parse and process,
        # raise an error if no file is given
        # print(sys.argv)
        if len(sys.argv) < 2:
            raise RuntimeError('Missing argument: file to execute.')

        address = 0

        # for instruction in program:
        #     self.ram[address] = instruction
        #     address += 1

        # open and parse file
        try: # catch FileNotFound errors
            with open(sys.argv[1]) as f:
                for line in f:
                    try:
                        line = line.split("#",1)[0] # drop comments
                        line = int(line, 2) # set nums as binary
                        self.ram[address] = line
                        address += 1
                    except ValueError:
                        pass
        except FileNotFoundError:
            print(f'Could not find file: {sys.argv[1]}')
            sys.exit(1)


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        # standardize values for input
        reg_a = reg_a & 0b00000111
        reg_b = reg_b & 0b00000111
        if op ==   0b10100000:  # ADD
            self.reg[reg_a] += self.reg[reg_b]
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        elif op == 0b10100001:  # SUB
            self.reg[reg_a] -= self.reg[reg_b]
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        elif op == 0b10100010:  # MUL
            self.reg[reg_a] *= self.reg[reg_b]
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        elif op == 0b10100011:  # DIV
            self.reg[reg_a] //= self.reg[reg_b]
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        elif op == 0b10100100:  # MOD
            self.reg[reg_a] %= self.reg[reg_b]
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        elif op == 0b01100101:  # INC
            self.reg[reg_a] += 1
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        elif op == 0b01100110:   # DEC
            self.reg[reg_a] -= 1
            self.reg[reg_a] = self.reg[reg_a] & 0b11111111
        else:
            raise Exception(f"Unsupported ALU operation: {op}")

    def ldi(self, reg, val):
        reg = reg & 0b00000111 # bitwise AND to prevent out-of-index
        val = val & 0b11111111 # bitwise AND to limit values
        self.reg[reg] = val

    def push(self, reg):
        # decrement value in register 7 (stack pointer)
        self.alu(0b01100110, 7, 0)
        # filter incoming register value and write to RAM
        reg = reg & 0b00000111
        # write value in reg a in RAM at address given by
        # stack pointer (register 7)
        self.ram_write(self.reg[reg], self.reg[7])

    def pop(self, reg):
        # filter incoming register value and read from
        # the address stored in that address
        reg = reg & 0b00000111
        # read value in RAM at address given by stack pointer
        # store in reg a
        mem_data_reg = self.ram_read(self.reg[7])
        self.ldi(reg, mem_data_reg)
        # increment the stack pointer
        self.alu(0b01100101, 7, 0)

    def ram_read(self, addr):
        return self.ram[addr]

    def ram_write(self, val, addr):
        self.ram[addr] = val

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        self.pc = 0
        ir = 0 # instruction register

        while True: # use HLT to escape loop
            ir = self.ram_read(self.pc)

            # if ALU func
            if (ir & 0b00100000) >> 5 == 1:
                # grab these regardless just to have them beforehand
                mem_addr_reg = self.ram_read(self.pc + 1) # reg a
                mem_data_reg = self.ram_read(self.pc + 2) # reg b
                # send the opcode to the ALU and have it deal with it
                self.alu(ir, mem_addr_reg, mem_data_reg)
                # increment PC after running funcs
                if (ir & 0b11000000) >> 6 == 0b00000011:
                    self.pc += 4
                elif (ir & 0b11000000) >> 6 == 0b00000010:
                    self.pc += 3
                elif (ir & 0b11000000) >> 6 == 0b00000001:
                    self.pc += 2
                else:
                    self.pc += 1
            # if PC mutator func
            elif (ir & 0b00010000) >> 4 == 1:
                pass
            # other funcs
            else:
                if ir == 0b00000000:    # NOP: no operation
                    pass # do nothing
                elif ir == 0b00000001:  # HLT: halt command
                    break
                elif ir == 0b01000101:  # PUSH: push val in reg a onto stack
                    mem_addr_reg = self.ram_read(self.pc + 1)
                    self.push(mem_addr_reg)
                elif ir == 0b01000110:  # POP: pop val from stack, store in reg a
                    mem_addr_reg = self.ram_read(self.pc + 1)
                    self.pop(mem_addr_reg)
                elif ir == 0b01000111:  # PRN: print from register
                    mem_addr_reg = self.ram_read(self.pc + 1)
                    mem_addr_reg = mem_addr_reg & 0b00000111 # OoB limiter
                    print(self.reg[mem_addr_reg])
                elif ir == 0b10000010:  # LDI: set register value
                    mem_addr_reg = self.ram_read(self.pc + 1)
                    mem_data_reg = self.ram_read(self.pc + 2)
                    self.ldi(mem_addr_reg, mem_data_reg)
                else:
                    print(f'Unsupported opcode: {ir:b} at address: {self.pc}')
                    break

                # increment PC after running funcs
                if (ir & 0b11000000) >> 6 == 0b00000011:
                    self.pc += 4
                elif (ir & 0b11000000) >> 6 == 0b00000010:
                    self.pc += 3
                elif (ir & 0b11000000) >> 6 == 0b00000001:
                    self.pc += 2
                else:
                    self.pc += 1
