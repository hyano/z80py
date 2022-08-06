from pprint import pprint
from z80 import Z80, Bus
import time

class VM:
    def __init__(self):
        self.mem_bus = Bus(self.mem_read, self.mem_write)
        self.io_bus = Bus(self.io_read, self.io_write)
        self.cpu = Z80(self.mem_bus, self.io_bus)
        self.cpu.m_opcodes = Bus(self.mem_read_op, self.mem_write)
        self.cpu.m_args = Bus(self.mem_read_arg, self.mem_write)

        self.memory = bytearray([0] * 0x10000)

        fh = open('zexall.bin', 'rb')
        zex = [ int(b) for b in fh.read() ]
        fh.close()

        p = 0x0100
        for b in zex:
            self.memory[p] = b
            p += 1

        self.memory[0x00] = 0xd3    # OUT   (0),A
        self.memory[0x01] = 0x00    
        self.memory[0x03] = 0x18    # JR    *
        self.memory[0x04] = 0xfe

        self.memory[0x05] = 0xff    # RST   38H

        self.memory[0x06] = 0x00    # initial SP
        self.memory[0x07] = 0xf0

        self.memory[0x38] = 0xf1    # POP   AF
        self.memory[0x39] = 0xdb    # IN    A,(0)
        self.memory[0x3a] = 0x00
        self.memory[0x3b] = 0xc9    # RET

        testno = 0x00
        # 0 adc16add16   add16x  add16y  alu8i   alu8r   alu8rx  alu8x
        #   bitx    bitz80  cpd1    cpi1    daa     inca    incb    incbc
        # 1 incc    incd    incde   ince    inch    inchl   incix   inciy
        #   incl    incm    incsp   incx    incxh   incxl   incyh   incyl
        # 2 ld161   ld162   ld163   ld164   ld165   ld166   ld167   ld168
        #   ld16im  ld16ix  ld8bd   ld8im   ld8imx  ld8ix1  ld8ix2  ld8ix3
        # 3 ld8ixy  ld8rr   ld8rrx  lda     ldd1    ldd2    ldi1    ldi2
        #   neg     rld     rot8080 rotxy   rotz80  srz80   srzx    st8ix1
        # 4 st8ix2  st8ix3  stabd
        tests = (self.memory[0x0121] << 8) | self.memory[0x0120]
        tests += testno * 2
        self.memory[0x120] = tests & 0xff
        self.memory[0x121] = (tests>>8) & 0xff

        self.finished = False
        self.enable_debug = False

    def run(self, cycles):
        self.cpu.m_icount += cycles
        self.cpu.execute_run()

    def debug(self, msg):
        if self.enable_debug:
            print(msg, flush=True)

    def mem_read(self, addr):
        self.debug("RD: {:04x} {:02x}".format(addr, self.memory[addr]))
        return self.memory[addr]

    def mem_read_op(self, addr):
        self.debug("RD: {:04x} {:02x} OP".format(addr, self.memory[addr]))
        return self.memory[addr]

    def mem_read_arg(self, addr):
        self.debug("RD: {:04x} {:02x}   ARG".format(addr, self.memory[addr]))
        return self.memory[addr]

    def mem_write(self, addr, value):
        self.debug("                        WR: {:04x} {:02x}".format(addr, value))
        self.memory[addr] = value

    def io_read(self, addr):
        self.debug("                        IN {:04x}".format(addr))
        self.syscall(self.cpu.C)
        return 0

    def io_write(self, addr, value):
        self.debug("                        OUT {:04x} {:02x}".format(addr, value))
        print("")
        self.finished = True

    def syscall(self, no):
        if no == 0x02:
            c = self.cpu.E
            self.debug("02 {:02x}".format(c))
            print("{:c}".format(c), end='', flush=True)
        if no == 0x09:
            addr = self.cpu.DE
            self.debug("09 {:04x}".format(addr))
            while True:
                c = self.memory[addr]
                addr += 1
                if c == ord('$'):
                    break
                if c == 13:
                    continue
                print("{:c}".format(c), end='', flush=True)

if __name__ == '__main__':
    vm = VM()

    #vm.enable_debug = True
    vm.cpu.PC = 0x0100

    prev = time.time()
    while not vm.finished:
        vm.run(4_000_000)
        now = time.time()
        #print("{:.3f}s".format(now - prev))
        prev = now