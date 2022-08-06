class Pair:
    def __init__(self, value = 0):
        self.w = value
    @property
    def w(self):
        return self.h << 8 | self.l
    @w.setter
    def w(self, value):
        self.h = (value >> 8) & 0xff
        self.l = value & 0xff

class Bus:
    def __init__(self, read, write):
        self.read = read
        self.write = write


class Z80:
    """Z80 Class

    A port of Z80 emulator (z80.cpp) from MAME
    Python port copyright (c) 2022 Hirokuni Yano
    This software is released under the BSD-3-Clause license.
    See https://opensource.org/licenses/BSD-3-Clause

    Original z80.cpp:
    Portable Z80 emulator V3.9
    license:BSD-3-Clause
    copyright-holders:Juergen Buchmueller
    """

    # The Z80 registers. halt is set to 1 when the CPU is halted, the refresh
    # register is calculated as follows: refresh=(r&127)|(r2&128)
    CF = 0x01
    NF = 0x02
    PF = 0x04
    VF = PF
    XF = 0x08
    HF = 0x10
    YF = 0x20
    ZF = 0x40
    SF = 0x80

    tables_initialized = False
    SZ = bytearray([0] * 256)       # zero and sign flags
    SZ_BIT = bytearray([0] *256)    # zero, sign and parity/overflow (=zero) flags for BIT opcode
    SZP = bytearray([0] * 256)      # zero, sign and parity flags */
    SZHV_inc = bytearray([0] * 256) # zero, sign, half carry and overflow flags INC r8
    SZHV_dec = bytearray([0] * 256) # zero, sign, half carry and overflow flags DEC r8
    SZHVC_add = bytearray([0] * 2*256*256)
    SZHVC_sub = bytearray([0] * 2*256*256)

    S8 = [0] * 0x100
    S16 = [0] * 0x10000

    INPUT_LINE_IRQ0 = 0
    INPUT_LINE_NMI = 1
    INPUT_LINE_WAIT = 2
    INPUT_LINE_BUSRQ = 3

    CLEAR_LINE = 0
    ASSERT_LINE = 1
    HOLD_LINE = 2

    cc_op = [
        4,10, 7, 6, 4, 4, 7, 4, 4,11, 7, 6, 4, 4, 7, 4,
        8,10, 7, 6, 4, 4, 7, 4,12,11, 7, 6, 4, 4, 7, 4,
        7,10,16, 6, 4, 4, 7, 4, 7,11,16, 6, 4, 4, 7, 4,
        7,10,13, 6,11,11,10, 4, 7,11,13, 6, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        7, 7, 7, 7, 7, 7, 4, 7, 4, 4, 4, 4, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        4, 4, 4, 4, 4, 4, 7, 4, 4, 4, 4, 4, 4, 4, 7, 4,
        5,10,10,10,10,11, 7,11, 5,10,10, 4,10,17, 7,11, # cb -> cc_cb
        5,10,10,11,10,11, 7,11, 5, 4,10,11,10, 4, 7,11, # dd -> cc_xy
        5,10,10,19,10,11, 7,11, 5, 4,10, 4,10, 4, 7,11, # ed -> cc_ed
        5,10,10, 4,10,11, 7,11, 5, 6,10, 4,10, 4, 7,11  # fd -> cc_xy
    ]

    cc_cb = [
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4, 8, 4, 4, 4, 4, 4, 4, 4, 8, 4,
        4, 4, 4, 4, 4, 4, 8, 4, 4, 4, 4, 4, 4, 4, 8, 4,
        4, 4, 4, 4, 4, 4, 8, 4, 4, 4, 4, 4, 4, 4, 8, 4,
        4, 4, 4, 4, 4, 4, 8, 4, 4, 4, 4, 4, 4, 4, 8, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4,
        4, 4, 4, 4, 4, 4,11, 4, 4, 4, 4, 4, 4, 4,11, 4
    ]

    cc_ed = [
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        8, 8,11,16, 4,10, 4, 5, 8, 8,11,16, 4,10, 4, 5,
        8, 8,11,16, 4,10, 4, 5, 8, 8,11,16, 4,10, 4, 5,
        8, 8,11,16, 4,10, 4,14, 8, 8,11,16, 4,10, 4,14,
        8, 8,11,16, 4,10, 4, 4, 8, 8,11,16, 4,10, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        12,12,12,12,4, 4, 4, 4,12,12,12,12, 4, 4, 4, 4,
        12,12,12,12,4, 4, 4, 4,12,12,12,12, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4
    ]

    # ix/iy: with the exception of (i+offset) opcodes, for total add t-states from main_opcode_table[DD/FD] == 4
    cc_xy = [
         4,10, 7, 6, 4, 4, 7, 4, 4,11, 7, 6, 4, 4, 7, 4,
         8,10, 7, 6, 4, 4, 7, 4,12,11, 7, 6, 4, 4, 7, 4,
         7,10,16, 6, 4, 4, 7, 4, 7,11,16, 6, 4, 4, 7, 4,
         7,10,13, 6,19,19,15, 4, 7,11,13, 6, 4, 4, 7, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
        15,15,15,15,15,15, 4,15, 4, 4, 4, 4, 4, 4,15, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
         4, 4, 4, 4, 4, 4,15, 4, 4, 4, 4, 4, 4, 4,15, 4,
         5,10,10,10,10,11, 7,11, 5,10,10, 7,10,17, 7,11, # cb -> cc_xycb
         5,10,10,11,10,11, 7,11, 5, 4,10,11,10, 4, 7,11, # dd -> cc_xy again
         5,10,10,19,10,11, 7,11, 5, 4,10, 4,10, 4, 7,11, # ed -> cc_ed
         5,10,10, 4,10,11, 7,11, 5, 6,10, 4,10, 4, 7,11  # fd -> cc_xy again
    ]

    cc_xycb = [
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
         9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
         9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
         9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
         9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,
        12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12
    ]

    # extra cycles if jr/jp/call taken and 'interrupt latency' on rst 0-7
    cc_ex = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # DJNZ
        5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, # JR NZ/JR Z
        5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, # JR NC/JR C
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        5, 5, 5, 5, 0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0, # LDIR/CPIR/INIR/OTIR LDDR/CPDR/INDR/OTDR
        6, 0, 0, 0, 7, 0, 0, 2, 6, 0, 0, 0, 7, 0, 0, 2,
        6, 0, 0, 0, 7, 0, 0, 2, 6, 0, 0, 0, 7, 0, 0, 2,
        6, 0, 0, 0, 7, 0, 0, 2, 6, 0, 0, 0, 7, 0, 0, 2,
        6, 0, 0, 0, 7, 0, 0, 2, 6, 0, 0, 0, 7, 0, 0, 2
    ]

    cc_dd = cc_xy
    cc_fd = cc_xy

    @property
    def PC(self):
        return self.m_pc.w
    @PC.setter
    def PC(self, value):
        self.m_pc.w = value
    @property
    def SP(self):
        return self.m_sp.w
    @SP.setter
    def SP(self, value):
        self.m_sp.w = value

    @property
    def AF(self):
        return self.m_af.w
    @AF.setter
    def AF(self, value):
        self.m_af.w = value
    @property
    def A(self):
        return self.m_af.h
    @A.setter
    def A(self, value):
        self.m_af.h = value
    @property
    def F(self):
        return self.m_af.l
    @F.setter
    def F(self, value):
        self.m_af.l = value

    @property
    def BC(self):
        return self.m_bc.w
    @BC.setter
    def BC(self, value):
        self.m_bc.w = value
    @property
    def B(self):
        return self.m_bc.h
    @B.setter
    def B(self, value):
        self.m_bc.h = value
    @property
    def C(self):
        return self.m_bc.l
    @C.setter
    def C(self, value):
        self.m_bc.l = value

    @property
    def DE(self):
        return self.m_de.w
    @DE.setter
    def DE(self, value):
        self.m_de.w = value
    @property
    def D(self):
        return self.m_de.h
    @D.setter
    def D(self, value):
        self.m_de.h = value
    @property
    def E(self):
        return self.m_de.l
    @E.setter
    def E(self, value):
        self.m_de.l = value

    @property
    def HL(self):
        return self.m_hl.w
    @HL.setter
    def HL(self, value):
        self.m_hl.w = value
    @property
    def H(self):
        return self.m_hl.h
    @H.setter
    def H(self, value):
        self.m_hl.h = value
    @property
    def L(self):
        return self.m_hl.l
    @L.setter
    def L(self, value):
        self.m_hl.l = value

    @property
    def IX(self):
        return self.m_ix.w
    @IX.setter
    def IX(self, value):
        self.m_ix.w = value
    @property
    def HX(self):
        return self.m_ix.h
    @HX.setter
    def HX(self, value):
        self.m_ix.h = value
    @property
    def LX(self):
        return self.m_ix.l
    @LX.setter
    def LX(self, value):
        self.m_ix.l = value

    @property
    def IY(self):
        return self.m_iy.w
    @IY.setter
    def IY(self, value):
        self.m_iy.w = value
    @property
    def HY(self):
        return self.m_iy.h
    @HY.setter
    def HY(self, value):
        self.m_iy.h = value
    @property
    def LY(self):
        return self.m_iy.l
    @LY.setter
    def LY(self, value):
        self.m_iy.l = value

    @property
    def WZ(self):
        return self.m_wz.w
    @WZ.setter
    def WZ(self, value):
        self.m_wz.w = value
    @property
    def WZ_H(self):
        return self.m_wz.h
    @WZ_H.setter
    def WZ_H(self, value):
        self.m_wz.h = value
    @property
    def WZ_L(self):
        return self.m_wz.l
    @WZ_L.setter
    def WZ_L(self, value):
        self.m_wz.l = value

    def __init__(self, mem_bus, io_bus):
        self.initialize_tables()

        self.m_data = mem_bus
        self.m_opcodes = mem_bus
        self.m_args = mem_bus
        self.m_io = io_bus

        # Reset registers to their initial values
        self.m_pc = Pair()
        self.m_sp = Pair()
        self.m_af = Pair()
        self.m_bc = Pair()
        self.m_de = Pair()
        self.m_hl = Pair()
        self.m_ix = Pair()
        self.m_iy = Pair()
        self.m_wz = Pair()

        self.m_af2 = Pair()
        self.m_bc2 = Pair()
        self.m_de2 = Pair()
        self.m_hl2 = Pair()

        self.IX = self.IY = 0xffff  # IX and IY are FFFF after a reset!
        self.F = Z80.ZF             # Zero flag is set

        self.m_r = 0
        self.m_r2 = 0
        self.m_iff1 = 0
        self.m_iff2 = 0
        self.m_halt = 0
        self.m_im = 0
        self.m_i = 0
        self.m_nmi_state = 0
        self.m_nmi_pending = False
        self.m_irq_state = 0
        self.m_wait_state = 0
        self.m_busrq_state = 0
        self.m_after_ei = False
        self.m_after_ldair = False
        self.m_ea = 0

        self.m_icount = 0
        self.m_icount_executing = 0

        self.MTM = Z80.cc_op[0] - 1

        self.m_irq_vector = None

        self.m_enable_debug = False

    def CC(self, table, opcode):
        self.m_icount_executing += table[opcode]

    def T(self, icount):
        self.m_icount -= icount
        self.m_icount_executing -= icount

    def EXEC(self, cc_table, op_table, opcode):
        self.CC(cc_table, opcode)
        op_table[opcode]()
        if self.m_icount_executing > 0:
            self.T(self.m_icount_executing)
        else:
            self.m_icount_executing = 0

    def halt(self):
        """Enter halt state; write 1 to callback on first execution
        """
        m_halt = 1
    
    def leave_halt(self):
        """Leave halt state; write 0 to callback
        """
        m_halt = 0

    def inp(self, port):
        """Input a byte from given I/O port
        """
        res = self.m_io.read(port)
        self.T(4)
        return res

    def out(self, port, value):
        """Output a byte to given I/O port
        """
        self.m_io.write(port, value)
        self.T(4)

    def rm(self, addr):
        """Read a byte from given memory location
        """
        res = self.m_data.read(addr)
        self.T(self.MTM)
        return res

    def rm_reg(self, addr):
        """Read a byte from given memory location
        """
        res = self.rm(addr)
        self.nomreq_addr(addr, 1)
        return res

    def rm16(self, addr, r):
        """Read a word from given memory location
        """
        r.l = self.rm(addr)
        r.h = self.rm(addr+1)

    def wm(self, addr, data):
        """Write a byte to given memory location
        """
        if self.m_icount_executing != self.MTM:
             self.T(self.m_icount_executing - self.MTM)
        self.m_data.write(addr, data)
        self.T(self.MTM)

    def wm16(self, addr, r):
        """Write a word to given memory location
        """
        self.m_icount_executing -= self.MTM
        self.wm(addr, r.l)
        self.m_icount_executing += self.MTM
        self.wm(addr+1, r.h)

    def wm16_sp(self, r):
        """Write a word to (SP)
        """
        self.SP -= 1
        self.m_icount_executing -= self.MTM
        self.wm(self.SP, r.h)
        self.m_icount_executing += self.MTM
        self.SP -= 1
        self.wm(self.SP, r.l)

    def rop(self):
        """Read an opcode from (PC)

        rop() is identical to rm() except it is used for
        reading opcodes. In case of system with memory mapped I/O,
        this function can be used to greatly speed up emulation
        """
        if self.m_icount_executing:
            self.T(self.m_icount_executing)
        res = self.m_opcodes.read(self.PC)
        self.T(self.execute_min_cycles())
        # refresh
        self.T(self.execute_min_cycles())
        self.PC += 1
        self.m_r += 1
        return res

    def arg(self):
        """Read an opcode argument from (PC)

        arg() is identical to rop() except it is used
        for reading opcode arguments. This difference can be used to
        support systems that use different encoding mechanisms for
        opcodes and opcode arguments
        """
        res = self.m_args.read(self.PC)
        self.T(self.MTM)
        self.PC += 1
        return res
    
    def arg16(self):
        """Read a 16bits opcode argument from (PC)

        arg() is identical to rop() except it is used
        for reading opcode arguments. This difference can be used to
        support systems that use different encoding mechanisms for
        opcodes and opcode arguments
        """
        res = self.arg()
        return (self.arg() << 8) | res

    def eax(self):
        """ Calculate the effective address EA of an opcode using IX+offset
        """
        self.m_ea = (self.IX + Z80.S8[self.arg()]) & 0xffff
        self.WZ = self.m_ea

    def eay(self):
        """ Calculate the effective address EA of an opcode using IY+offset
        """
        self.m_ea = (self.IY + Z80.S8[self.arg()]) & 0xffff
        self.WZ = self.m_ea

    def pop(self, r):
        """POP
        """
        self.rm16(self.SP, r)
        self.SP += 2

    def push(self, r):
        """PUSH
        """
        self.nomreq_ir(1)
        self.wm16_sp(r)

    def jp(self):
        """JP
        """
        self.PC = self.arg16()
        self.WZ = self.PC

    def jp_cond(self, cond):
        """JP_COND
        """
        if cond:
            self.PC = self.arg16()
            self.WZ = self.PC
        else:
            self.WZ = self.arg16()
    
    def jr(self):
        """JR
        """
        self.PC += Z80.S8[self.arg()]
        self.nomreq_addr(self.PC - 1, 5)
        self.WZ = self.PC

    def jr_cond(self, cond, opcode):
        """JR_COND
        """
        if cond:
            self.CC(Z80.cc_ex, opcode)
            self.jr()
        else:
            self.WZ = self.arg()
    
    def call(self):
        """CALL
        """
        self.m_ea = self.arg16()
        self.nomreq_addr(self.PC - 1, 1)
        self.WZ = self.m_ea
        self.wm16_sp(self.m_pc)
        self.PC = self.m_ea

    def call_cond(self, cond, opcode):
        """CALL_COND
        """
        if cond:
            self.CC(Z80.cc_ex, opcode)
            self.m_ea = self.arg16()
            self.nomreq_addr(self.PC - 1, 1)
            self.WZ = self.m_ea
            self.wm16_sp(self.m_pc)
            self.PC = self.m_ea
        else:
            self.WZ = self.arg16()

    def ret_cond(self, cond, opcode):
        """RET_COND
        """
        self.nomreq_ir(1)
        if cond:
            self.CC(Z80.cc_ex, opcode)
            self.pop(self.m_pc)
            self.WZ = self.PC

    def retn(self):
        """RETN
        """
        self.pop(self.m_pc)
        self.WZ = self.PC
        self.m_iff1 = self.m_iff2

    def reti(self):
        """RETI
        """
        self.pop(self.m_pc)
        self.WZ = self.PC
        self.m_iff1 = self.m_iff2

    def ld_r_a(self):
        """LD   R,A
        """
        self.nomreq_ir(1)
        self.m_r = self.A
        self.m_r2 = self.A & 0x80

    def ld_a_r(self):
        """LD   A,R
        """
        self.nomreq_ir(1)
        self.A = (self.m_r & 0x7f) | self.m_r2
        self.F = (self.F & Z80.CF) | Z80.SZ[self.A] | (self.m_iff2 << 2)
        self.m_after_ldair = True

    def ld_i_a(self):
        """LD   I,A
        """
        self.nomreq_ir(1)
        self.m_i = self.A

    def ld_a_i(self):
        """LD   A,I
        """
        self.nomreq_ir(1)
        self.A = self.m_i
        self.F = (self.F & Z80.CF) | Z80.SZ[self.A] | (self.m_iff2 << 2)
        self.m_after_ldair = True

    def rst(self, addr):
        """RST
        """
        self.push(self.m_pc)
        self.PC = addr
        self.WZ = self.PC

    def inc(self, value):
        """INC  r8
        """
        res = (value + 1) & 0xff
        self.F = (self.F & Z80.CF) | Z80.SZHV_inc[res]
        return res

    def dec(self, value):
        """DEC  r8
        """
        res = (value - 1) & 0xff
        self.F = (self.F & Z80.CF) | Z80.SZHV_dec[res]
        return res

    def rlca(self):
        """RLCA
        """
        self.A = ((self.A << 1) | (self.A >> 7)) & 0xff
        self.F = (self.F & (Z80.SF | Z80.ZF | Z80.PF)) | (self.A & (Z80.YF | Z80.XF | Z80.CF))

    def rrca(self):
        """RRCA
        """
        self.F = (self.F & (Z80.SF | Z80.ZF | Z80.PF)) | (self.A & Z80.CF)
        self.A = ((self.A >> 1) | (self.A << 7)) & 0xff
        self.F |= (self.A & (Z80.YF | Z80.XF))

    def rla(self):
        """RLA
        """
        res = ((self.A << 1) | (self.F & Z80.CF)) & 0xff
        c = Z80.CF if (self.A & 0x80) else 0
        self.F = (self.F & (Z80.SF | Z80.ZF | Z80.PF)) | c | (res & (Z80.YF | Z80.XF))
        self.A = res

    def rra(self):
        """RRA
        """
        res = ((self.A >> 1) | (self.F << 7)) & 0xff
        c = Z80.CF if (self.A & 0x01) else 0
        self.F = (self.F & (Z80.SF | Z80.ZF | Z80.PF)) | c | (res & (Z80.YF | Z80.XF))
        self.A = res

    def rrd(self):
        """RRD
        """
        n = self.rm(self.HL)
        self.WZ = self.HL + 1
        self.nomreq_addr(self.HL, 4)
        self.wm(self.HL, ((n >> 4) | (self.A << 4)) & 0xff)
        self.A = (self.A & 0xf0) | (n & 0x0f)
        self.F = (self.F & Z80.CF) | Z80.SZP[self.A]

    def rld(self):
        """RLD
        """
        n = self.rm(self.HL)
        self.WZ = self.HL + 1
        self.nomreq_addr(self.HL, 4)
        self.wm(self.HL, ((n << 4) | (self.A & 0x0f)) & 0xff)
        self.A = (self.A & 0xf0) | (n >> 4)
        self.F = (self.F & Z80.CF) | Z80.SZP[self.A]

    def add_a(self, value):
        """ADD  A,n
        """
        ah = self.AF & 0xff00
        res = ((ah >> 8) + value) & 0xff
        self.F = Z80.SZHVC_add[ah | res]
        self.A = res

    def adc_a(self, value):
        """ADC  A,n
        """
        ah = self.AF & 0xff00
        c = self.F & 1
        res = ((ah >> 8) + value + c) & 0xff
        self.F = Z80.SZHVC_add[(c << 16) | ah | res]
        self.A = res

    def sub(self, value):
        """SUB  n
        """
        ah = self.AF & 0xff00
        res = ((ah >> 8) - value) & 0xff
        self.F = Z80.SZHVC_sub[ah | res]
        self.A = res

    def sbc_a(self, value):
        """SBC  A,n
        """
        ah = self.AF & 0xff00
        c = self.F & 1
        res = ((ah >> 8) - value - c) & 0xff
        self.F = Z80.SZHVC_sub[(c << 16) | ah | res]
        self.A = res

    def neg(self):
        """NEG
        """
        value = self.A
        self.A = 0
        self.sub(value)
    
    def daa(self):
        """DAA
        """
        a = self.A
        if self.F & Z80.NF:
            if (self.F & Z80.HF) | ((self.A & 0x0f) > 9):
                a = (a - 6) & 0xff
            if (self.F & Z80.CF) | (self.A > 0x99):
                a = (a - 0x60) & 0xff
        else:
            if (self.F & Z80.HF) | ((self.A & 0x0f) > 9):
                a = (a + 6) & 0xff
            if (self.F & Z80.CF) | (self.A > 0x99):
                a = (a + 0x60) & 0xff
        self.F = (self.F & (Z80.CF | Z80.NF)) | (self.A > 0x99) | ((self.A ^ a) & Z80.HF) | Z80.SZP[a]
        self.A = a
    
    def and_a(self, value):
        """AND  n
        """
        self.A &= value
        self.F = Z80.SZP[self.A] | Z80.HF

    def or_a(self, value):
        """OR   n
        """
        self.A |= value
        self.F = Z80.SZP[self.A]

    def xor_a(self, value):
        """XOR  n
        """
        self.A ^= value
        self.F = Z80.SZP[self.A]

    def cp(self, value):
        """CP   n
        """
        ah = self.AF & 0xff00
        res = ((ah >> 8) - value) & 0xff
        self.F = Z80.SZHVC_sub[ah | res] & ~(Z80.YF | Z80.XF) \
            | (value & (Z80.YF | Z80.XF))

    def ex_af(self):
        """EX   AF,AF'
        """
        tmp = self.m_af.w
        self.m_af.w = self.m_af2.w
        self.m_af2.w = tmp

    def ex_de_hl(self):
        """EX   DE,HL
        """
        tmp = self.m_de.w
        self.m_de.w = self.m_hl.w
        self.m_hl.w = tmp

    def exx(self):
        """EXX
        """
        tmp = self.m_bc.w
        self.m_bc.w = self.m_bc2.w
        self.m_bc2.w = tmp
        tmp = self.m_de.w
        self.m_de.w = self.m_de2.w
        self.m_de2.w = tmp
        tmp = self.m_hl.w
        self.m_hl.w = self.m_hl2.w
        self.m_hl2.w = tmp

    def ex_sp(self, r):
        """EX   (SP),r16
        """
        tmp =  Pair()
        self.pop(tmp)
        self.nomreq_addr(self.SP - 1, 1)
        self.m_icount_executing -= 2
        self.wm16_sp(r)
        self.m_icount_executing += 2
        self.nomreq_addr(self.SP, 2)
        r.w = tmp.w
        self.WZ = r.w

    def add16(self, dr, sr):
        """ADD16
        """
        self.nomreq_ir(7)
        res = dr.w + sr.w
        self.WZ = dr.w + 1
        self.F = (self.F & (Z80.SF | Z80.ZF | self.VF)) \
            | (((dr.w ^ res ^ sr.w) >> 8) & Z80.HF) \
            | ((res >> 16) & Z80.CF) \
            | ((res >> 8) & (Z80.YF | Z80.XF))
        dr.w = res

    def adc_hl(self, r):
        """ADC  HL,r16
        """
        self.nomreq_ir(7)
        res = self.HL + r.w + (self.F & Z80.CF)
        self.WZ = self.HL + 1
        self.F = (((self.HL ^ res ^ r.w) >> 8) & Z80.HF) \
            | ((res >> 16) & Z80.CF) \
            | ((res >> 8) & (Z80.SF | Z80.YF | Z80.XF)) \
            | (0 if (res & 0xffff) else Z80.ZF) \
            | (((r.w ^ self.HL ^ 0x8000) & (r.w ^ res) & 0x8000) >> 13)
        self.HL = res

    def sbc_hl(self, r):
        """SBC  HL,r16
        """
        self.nomreq_ir(7)
        res = self.HL - r.w - (self.F & Z80.CF)
        self.WZ = self.HL + 1
        self.F = (((self.HL ^ res ^ r.w) >> 8) & Z80.HF) \
            | Z80.NF \
            | ((res >> 16) & Z80.CF) \
            | ((res >> 8) & (Z80.SF | Z80.YF | Z80.XF)) \
            | (0 if (res & 0xffff) else Z80.ZF) \
            | (((r.w ^ self.HL) & (self.HL ^ res) & 0x8000) >> 13)
        self.HL = res

    def rlc(self, value):
        """RLC  r8
        """
        res = value
        c = Z80.CF if (res & 0x80) else 0
        res = ((res << 1) | (res >> 7)) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def rrc(self, value):
        """RRC  r8
        """
        res = value
        c = Z80.CF if (res & 0x01) else 0
        res = ((res >> 1) | (res << 7)) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def rl(self, value):
        """RL   r8
        """
        res = value
        c = Z80.CF if (res & 0x80) else 0
        res = ((res << 1) | (self.F & Z80.CF)) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def rr(self, value):
        """RR   r8
        """
        res = value
        c = Z80.CF if (res & 0x01) else 0
        res = ((res >> 1) | (self.F << 7)) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def sla(self, value):
        """SLA  r8
        """
        res = value
        c = Z80.CF if (res & 0x80) else 0
        res = (res << 1)  & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def sra(self, value):
        """SRA  r8
        """
        res = value
        c = Z80.CF if (res & 0x01) else 0
        res = ((res >> 1) | (res & 0x80)) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def sll(self, value):
        """SLL  r8
        """
        res = value
        c = Z80.CF if (res & 0x80) else 0
        res = ((res << 1) | 0x01) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def srl(self, value):
        """SRL  r8
        """
        res = value
        c = Z80.CF if (res & 0x01) else 0
        res = (res >> 1) & 0xff
        self.F = Z80.SZP[res] | c
        return res

    def bit(self, bit, value):
        """BIT  bit,r8
        """
        self.F = (self.F & Z80.CF) \
            | Z80.HF \
            | (Z80.SZ_BIT[value & (1 << bit)] & ~(Z80.YF | Z80.XF)) \
            | (value & (Z80.YF | Z80.XF))

    def bit_hl(self, bit, value):
        """BIT  bit,(HL)
        """
        self.F = (self.F & Z80.CF) \
            | Z80.HF \
            | (Z80.SZ_BIT[value & (1 << bit)] & ~(Z80.YF | Z80.XF)) \
            | (self.WZ_H & (Z80.YF | Z80.XF))

    def bit_xy(self, bit, value):
        """BIT  bit,(IX/Y+o)
        """
        self.F = (self.F & Z80.CF) \
            | Z80.HF \
            | (Z80.SZ_BIT[value & (1 << bit)] & ~(Z80.YF | Z80.XF)) \
            | ((self.m_ea >> 8) & (Z80.YF | Z80.XF))

    def res(self, bit, value):
        """RES  bit,r8
        """
        return value & ~(1 << bit)

    def set(self, bit, value):
        """SET  bit,r8
        """
        return value | (1 << bit)

    def ldi(self):
        """LDI
        """
        io = self.rm(self.HL)
        self.m_icount_executing -= 2
        self.wm(self.DE, io)
        self.m_icount_executing += 2
        self.nomreq_addr(self.DE, 2)
        self.F &= Z80.SF | Z80.ZF | Z80.CF
        if (self.A + io) & 0x02:
            self.F |= Z80.YF
        if (self.A + io) & 0x08:
            self.F |= Z80.XF
        self.HL += 1
        self.DE += 1
        self.BC -= 1
        if self.BC:
            self.F |= Z80.VF

    def cpi(self):
        """CPI
        """
        val = self.rm(self.HL)
        self.nomreq_addr(self.DE, 5)
        res = (self.A - val) & 0xff
        self.WZ += 1
        self.HL += 1
        self.BC -= 1
        self.F = (self.F & Z80.CF) \
            | (Z80.SZ[res] & ~(Z80.YF | Z80.XF)) \
            | ((self.A ^ val ^ res) & Z80.HF) \
            | Z80.NF
        if self.F & Z80.HF:
            res -= 1
        if res & 0x02:
            self.F |= Z80.YF
        if res & 0x08:
            self.F |= Z80.XF
        if self.BC:
            self.F |= Z80.VF

    def ini(self):
        """INI
        """
        self.nomreq_ir(1)
        io = self.inp(self.BC)
        self.WZ = self.BC + 1
        self.B = (self.B - 1) & 0xff
        self.wm(self.HL, io)
        self.HL += 1
        self.F = Z80.SZ[self.B]
        t = ((self.C + 1) & 0xff) + io
        if io & Z80.SF:
            self.F |= Z80.NF
        if t & 0x100:
            self.F |= Z80.HF | Z80.CF
        self.F |= Z80.SZP[(t & 0x07) ^ self.B] & Z80.PF

    def outi(self):
        """OUTI
        """
        self.nomreq_ir(1)
        io = self.rm(self.HL)
        self.B = (self.B - 1) & 0xff
        self.WZ = self.BC + 1
        self.out(self.BC, io)
        self.HL += 1
        self.F = Z80.SZ[self.B]
        t = self.L + io
        if io & Z80.SF:
            self.F |= Z80.NF
        if t & 0x100:
            self.F |= Z80.HF | Z80.CF
        self.F |= Z80.SZP[(t & 0x07) ^ self.B] & Z80.PF

    def ldd(self):
        """LDD
        """
        io = self.rm(self.HL)
        self.m_icount_executing -= 2
        self.wm(self.DE, io)
        self.m_icount_executing += 2
        self.nomreq_addr(self.DE, 2)
        self.F &= Z80.SF | Z80.ZF | Z80.CF
        if (self.A + io) & 0x02:
            self.F |= Z80.YF
        if (self.A + io) & 0x08:
            self.F |= Z80.XF
        self.HL -= 1
        self.DE -= 1
        self.BC -= 1
        if self.BC:
            self.F |= Z80.VF

    def cpd(self):
        """CPD
        """
        val = self.rm(self.HL)
        self.nomreq_addr(self.DE, 5)
        res = (self.A - val) & 0xff
        self.WZ -= 1
        self.HL -= 1
        self.BC -= 1
        self.F = (self.F & Z80.CF) \
            | (Z80.SZ[res] & ~(Z80.YF | Z80.XF)) \
            | ((self.A ^ val ^ res) & Z80.HF) \
            | Z80.NF
        if self.F & Z80.HF:
            res -= 1
        if res & 0x02:
            self.F |= Z80.YF
        if res & 0x08:
            self.F |= Z80.XF
        if self.BC:
            self.F |= Z80.VF

    def ind(self):
        """IND
        """
        self.nomreq_ir(1)
        io = self.inp(self.BC)
        self.WZ = self.BC - 1
        self.B = (self.B - 1) & 0xff
        self.wm(self.HL, io)
        self.HL -= 1
        self.F = Z80.SZ[self.B]
        t = ((self.C - 1) & 0xff) + io
        if io & Z80.SF:
            self.F |= Z80.NF
        if t & 0x100:
            self.F |= Z80.HF | Z80.CF
        self.F |= Z80.SZP[(t & 0x07) ^ self.B] & Z80.PF

    def outd(self):
        """OUTD
        """
        self.nomreq_ir(1)
        io = self.rm(self.HL)
        self.B = (self.B - 1) & 0xff
        self.WZ = self.BC - 1
        self.out(self.BC, io)
        self.HL -= 1
        self.F = Z80.SZ[self.B]
        t = self.L + io
        if io & Z80.SF:
            self.F |= Z80.NF
        if t & 0x100:
            self.F |= Z80.HF | Z80.CF
        self.F |= Z80.SZP[(t & 0x07) ^ self.B] & Z80.PF

    def ldir(self):
        """LDIR
        """
        self.ldi()
        if self.BC != 0:
            self.CC(Z80.cc_ex, 0xb0)
            self.nomreq_addr(self.DE, 5)
            self.PC -= 2
            self.WZ = self.PC + 1

    def cpir(self):
        """CPIR
        """
        self.cpi()
        if (self.BC != 0) and (not (self.F & Z80.ZF)):
            self.CC(Z80.cc_ex, 0xb1)
            self.nomreq_addr(self.HL, 5)
            self.PC -= 2
            self.WZ = self.PC + 1

    def inir(self):
        """INIR
        """
        self.ini()
        if self.B != 0:
            self.CC(Z80.cc_ex, 0xb2)
            self.nomreq_addr(self.HL, 5)
            self.PC -= 2

    def otir(self):
        """OTIR
        """
        self.outi()
        if self.B != 0:
            self.CC(Z80.cc_ex, 0xb3)
            self.nomreq_addr(self.BC, 5)
            self.PC -= 2
    
    def lddr(self):
        """LDDR
        """
        self.ldd()
        if self.BC != 0:
            self.CC(Z80.cc_ex, 0xb8)
            self.nomreq_addr(self.DE, 5)
            self.PC -= 2
            self.WZ = self.PC + 1

    def cpdr(self):
        """CPDR
        """
        self.cpd()
        if (self.BC != 0) and (not (self.F & Z80.ZF)):
            self.CC(Z80.cc_ex, 0xb9)
            self.nomreq_addr(self.HL, 5)
            self.PC -= 2
            self.WZ = self.PC + 1

    def indr(self):
        """INDR
        """
        self.ind()
        if self.B != 0:
            self.CC(Z80.cc_ex, 0xba)
            self.nomreq_addr(self.HL, 5)
            self.PC -= 2

    def otdr(self):
        """OTDR
        """
        self.outd()
        if self.B != 0:
            self.CC(Z80.cc_ex, 0xbb)
            self.nomreq_addr(self.BC, 5)
            self.PC -= 2

    def ei(self):
        """EI
        """
        self.m_iff1 = self.m_iff2 = 1
        self.m_after_ei = True

    # opcodes with CB prefix
    # rotate, shift and bit operations
    def op_cb_00(self): self.B = self.rlc(self.B)
    def op_cb_01(self): self.C = self.rlc(self.C)
    def op_cb_02(self): self.D = self.rlc(self.D)
    def op_cb_03(self): self.E = self.rlc(self.E)
    def op_cb_04(self): self.H = self.rlc(self.H)
    def op_cb_05(self): self.L = self.rlc(self.L)
    def op_cb_06(self): self.wm(self.HL, self.rlc(self.rm_reg(self.HL)))
    def op_cb_07(self): self.A = self.rlc(self.A)

    def op_cb_08(self): self.B = self.rrc(self.B)
    def op_cb_09(self): self.C = self.rrc(self.C)
    def op_cb_0a(self): self.D = self.rrc(self.D)
    def op_cb_0b(self): self.E = self.rrc(self.E)
    def op_cb_0c(self): self.H = self.rrc(self.H)
    def op_cb_0d(self): self.L = self.rrc(self.L)
    def op_cb_0e(self): self.wm(self.HL, self.rrc(self.rm_reg(self.HL)))
    def op_cb_0f(self): self.A = self.rrc(self.A)

    def op_cb_10(self): self.B = self.rl(self.B)
    def op_cb_11(self): self.C = self.rl(self.C)
    def op_cb_12(self): self.D = self.rl(self.D)
    def op_cb_13(self): self.E = self.rl(self.E)
    def op_cb_14(self): self.H = self.rl(self.H)
    def op_cb_15(self): self.L = self.rl(self.L)
    def op_cb_16(self): self.wm(self.HL, self.rl(self.rm_reg(self.HL)))
    def op_cb_17(self): self.A = self.rl(self.A)

    def op_cb_18(self): self.B = self.rr(self.B)
    def op_cb_19(self): self.C = self.rr(self.C)
    def op_cb_1a(self): self.D = self.rr(self.D)
    def op_cb_1b(self): self.E = self.rr(self.E)
    def op_cb_1c(self): self.H = self.rr(self.H)
    def op_cb_1d(self): self.L = self.rr(self.L)
    def op_cb_1e(self): self.wm(self.HL, self.rr(self.rm_reg(self.HL)))
    def op_cb_1f(self): self.A = self.rr(self.A)

    def op_cb_20(self): self.B = self.sla(self.B)
    def op_cb_21(self): self.C = self.sla(self.C)
    def op_cb_22(self): self.D = self.sla(self.D)
    def op_cb_23(self): self.E = self.sla(self.E)
    def op_cb_24(self): self.H = self.sla(self.H)
    def op_cb_25(self): self.L = self.sla(self.L)
    def op_cb_26(self): self.wm(self.HL, self.sla(self.rm_reg(self.HL)))
    def op_cb_27(self): self.A = self.sla(self.A)

    def op_cb_28(self): self.B = self.sra(self.B)
    def op_cb_29(self): self.C = self.sra(self.C)
    def op_cb_2a(self): self.D = self.sra(self.D)
    def op_cb_2b(self): self.E = self.sra(self.E)
    def op_cb_2c(self): self.H = self.sra(self.H)
    def op_cb_2d(self): self.L = self.sra(self.L)
    def op_cb_2e(self): self.wm(self.HL, self.sra(self.rm_reg(self.HL)))
    def op_cb_2f(self): self.A = self.sra(self.A)

    def op_cb_30(self): self.B = self.sll(self.B)
    def op_cb_31(self): self.C = self.sll(self.C)
    def op_cb_32(self): self.D = self.sll(self.D)
    def op_cb_33(self): self.E = self.sll(self.E)
    def op_cb_34(self): self.H = self.sll(self.H)
    def op_cb_35(self): self.L = self.sll(self.L)
    def op_cb_36(self): self.wm(self.HL, self.sll(self.rm_reg(self.HL)))
    def op_cb_37(self): self.A = self.sll(self.A)

    def op_cb_38(self): self.B = self.srl(self.B)
    def op_cb_39(self): self.C = self.srl(self.C)
    def op_cb_3a(self): self.D = self.srl(self.D)
    def op_cb_3b(self): self.E = self.srl(self.E)
    def op_cb_3c(self): self.H = self.srl(self.H)
    def op_cb_3d(self): self.L = self.srl(self.L)
    def op_cb_3e(self): self.wm(self.HL, self.srl(self.rm_reg(self.HL)))
    def op_cb_3f(self): self.A = self.srl(self.A)

    def op_cb_40(self): self.bit(0, self.B)
    def op_cb_41(self): self.bit(0, self.C)
    def op_cb_42(self): self.bit(0, self.D)
    def op_cb_43(self): self.bit(0, self.E)
    def op_cb_44(self): self.bit(0, self.H)
    def op_cb_45(self): self.bit(0, self.L)
    def op_cb_46(self): self.bit_hl(0, self.rm_reg(self.HL))
    def op_cb_47(self): self.bit(0, self.A)

    def op_cb_48(self): self.bit(1, self.B)
    def op_cb_49(self): self.bit(1, self.C)
    def op_cb_4a(self): self.bit(1, self.D)
    def op_cb_4b(self): self.bit(1, self.E)
    def op_cb_4c(self): self.bit(1, self.H)
    def op_cb_4d(self): self.bit(1, self.L)
    def op_cb_4e(self): self.bit_hl(1, self.rm_reg(self.HL))
    def op_cb_4f(self): self.bit(1, self.A)

    def op_cb_50(self): self.bit(2, self.B)
    def op_cb_51(self): self.bit(2, self.C)
    def op_cb_52(self): self.bit(2, self.D)
    def op_cb_53(self): self.bit(2, self.E)
    def op_cb_54(self): self.bit(2, self.H)
    def op_cb_55(self): self.bit(2, self.L)
    def op_cb_56(self): self.bit_hl(2, self.rm_reg(self.HL))
    def op_cb_57(self): self.bit(2, self.A)

    def op_cb_58(self): self.bit(3, self.B)
    def op_cb_59(self): self.bit(3, self.C)
    def op_cb_5a(self): self.bit(3, self.D)
    def op_cb_5b(self): self.bit(3, self.E)
    def op_cb_5c(self): self.bit(3, self.H)
    def op_cb_5d(self): self.bit(3, self.L)
    def op_cb_5e(self): self.bit_hl(3, self.rm_reg(self.HL))
    def op_cb_5f(self): self.bit(3, self.A)

    def op_cb_60(self): self.bit(4, self.B)
    def op_cb_61(self): self.bit(4, self.C)
    def op_cb_62(self): self.bit(4, self.D)
    def op_cb_63(self): self.bit(4, self.E)
    def op_cb_64(self): self.bit(4, self.H)
    def op_cb_65(self): self.bit(4, self.L)
    def op_cb_66(self): self.bit_hl(4, self.rm_reg(self.HL))
    def op_cb_67(self): self.bit(4, self.A)

    def op_cb_68(self): self.bit(5, self.B)
    def op_cb_69(self): self.bit(5, self.C)
    def op_cb_6a(self): self.bit(5, self.D)
    def op_cb_6b(self): self.bit(5, self.E)
    def op_cb_6c(self): self.bit(5, self.H)
    def op_cb_6d(self): self.bit(5, self.L)
    def op_cb_6e(self): self.bit_hl(5, self.rm_reg(self.HL))
    def op_cb_6f(self): self.bit(5, self.A)

    def op_cb_70(self): self.bit(6, self.B)
    def op_cb_71(self): self.bit(6, self.C)
    def op_cb_72(self): self.bit(6, self.D)
    def op_cb_73(self): self.bit(6, self.E)
    def op_cb_74(self): self.bit(6, self.H)
    def op_cb_75(self): self.bit(6, self.L)
    def op_cb_76(self): self.bit_hl(6, self.rm_reg(self.HL))
    def op_cb_77(self): self.bit(6, self.A)

    def op_cb_78(self): self.bit(7, self.B)
    def op_cb_79(self): self.bit(7, self.C)
    def op_cb_7a(self): self.bit(7, self.D)
    def op_cb_7b(self): self.bit(7, self.E)
    def op_cb_7c(self): self.bit(7, self.H)
    def op_cb_7d(self): self.bit(7, self.L)
    def op_cb_7e(self): self.bit_hl(7, self.rm_reg(self.HL))
    def op_cb_7f(self): self.bit(7, self.A)

    def op_cb_80(self): self.B = self.res(0, self.B)
    def op_cb_81(self): self.C = self.res(0, self.C)
    def op_cb_82(self): self.D = self.res(0, self.D)
    def op_cb_83(self): self.E = self.res(0, self.E)
    def op_cb_84(self): self.H = self.res(0, self.H)
    def op_cb_85(self): self.L = self.res(0, self.L)
    def op_cb_86(self): self.wm(self.HL, self.res(0, self.rm_reg(self.HL)))
    def op_cb_87(self): self.A = self.res(0, self.A)

    def op_cb_88(self): self.B = self.res(1, self.B)
    def op_cb_89(self): self.C = self.res(1, self.C)
    def op_cb_8a(self): self.D = self.res(1, self.D)
    def op_cb_8b(self): self.E = self.res(1, self.E)
    def op_cb_8c(self): self.H = self.res(1, self.H)
    def op_cb_8d(self): self.L = self.res(1, self.L)
    def op_cb_8e(self): self.wm(self.HL, self.res(1, self.rm_reg(self.HL)))
    def op_cb_8f(self): self.A = self.res(1, self.A)

    def op_cb_90(self): self.B = self.res(2, self.B)
    def op_cb_91(self): self.C = self.res(2, self.C)
    def op_cb_92(self): self.D = self.res(2, self.D)
    def op_cb_93(self): self.E = self.res(2, self.E)
    def op_cb_94(self): self.H = self.res(2, self.H)
    def op_cb_95(self): self.L = self.res(2, self.L)
    def op_cb_96(self): self.wm(self.HL, self.res(2, self.rm_reg(self.HL)))
    def op_cb_97(self): self.A = self.res(2, self.A)

    def op_cb_98(self): self.B = self.res(3, self.B)
    def op_cb_99(self): self.C = self.res(3, self.C)
    def op_cb_9a(self): self.D = self.res(3, self.D)
    def op_cb_9b(self): self.E = self.res(3, self.E)
    def op_cb_9c(self): self.H = self.res(3, self.H)
    def op_cb_9d(self): self.L = self.res(3, self.L)
    def op_cb_9e(self): self.wm(self.HL, self.res(3, self.rm_reg(self.HL)))
    def op_cb_9f(self): self.A = self.res(3, self.A)

    def op_cb_a0(self): self.B = self.res(4, self.B)
    def op_cb_a1(self): self.C = self.res(4, self.C)
    def op_cb_a2(self): self.D = self.res(4, self.D)
    def op_cb_a3(self): self.E = self.res(4, self.E)
    def op_cb_a4(self): self.H = self.res(4, self.H)
    def op_cb_a5(self): self.L = self.res(4, self.L)
    def op_cb_a6(self): self.wm(self.HL, self.res(4, self.rm_reg(self.HL)))
    def op_cb_a7(self): self.A = self.res(4, self.A)

    def op_cb_a8(self): self.B = self.res(5, self.B)
    def op_cb_a9(self): self.C = self.res(5, self.C)
    def op_cb_aa(self): self.D = self.res(5, self.D)
    def op_cb_ab(self): self.E = self.res(5, self.E)
    def op_cb_ac(self): self.H = self.res(5, self.H)
    def op_cb_ad(self): self.L = self.res(5, self.L)
    def op_cb_ae(self): self.wm(self.HL, self.res(5, self.rm_reg(self.HL)))
    def op_cb_af(self): self.A = self.res(5, self.A)

    def op_cb_b0(self): self.B = self.res(6, self.B)
    def op_cb_b1(self): self.C = self.res(6, self.C)
    def op_cb_b2(self): self.D = self.res(6, self.D)
    def op_cb_b3(self): self.E = self.res(6, self.E)
    def op_cb_b4(self): self.H = self.res(6, self.H)
    def op_cb_b5(self): self.L = self.res(6, self.L)
    def op_cb_b6(self): self.wm(self.HL, self.res(6, self.rm_reg(self.HL)))
    def op_cb_b7(self): self.A = self.res(6, self.A)

    def op_cb_b8(self): self.B = self.res(7, self.B)
    def op_cb_b9(self): self.C = self.res(7, self.C)
    def op_cb_ba(self): self.D = self.res(7, self.D)
    def op_cb_bb(self): self.E = self.res(7, self.E)
    def op_cb_bc(self): self.H = self.res(7, self.H)
    def op_cb_bd(self): self.L = self.res(7, self.L)
    def op_cb_be(self): self.wm(self.HL, self.res(7, self.rm_reg(self.HL)))
    def op_cb_bf(self): self.A = self.res(7, self.A)

    def op_cb_c0(self): self.B = self.set(0, self.B)
    def op_cb_c1(self): self.C = self.set(0, self.C)
    def op_cb_c2(self): self.D = self.set(0, self.D)
    def op_cb_c3(self): self.E = self.set(0, self.E)
    def op_cb_c4(self): self.H = self.set(0, self.H)
    def op_cb_c5(self): self.L = self.set(0, self.L)
    def op_cb_c6(self): self.wm(self.HL, self.set(0, self.rm_reg(self.HL)))
    def op_cb_c7(self): self.A = self.set(0, self.A)

    def op_cb_c8(self): self.B = self.set(1, self.B)
    def op_cb_c9(self): self.C = self.set(1, self.C)
    def op_cb_ca(self): self.D = self.set(1, self.D)
    def op_cb_cb(self): self.E = self.set(1, self.E)
    def op_cb_cc(self): self.H = self.set(1, self.H)
    def op_cb_cd(self): self.L = self.set(1, self.L)
    def op_cb_ce(self): self.wm(self.HL, self.set(1, self.rm_reg(self.HL)))
    def op_cb_cf(self): self.A = self.set(1, self.A)

    def op_cb_d0(self): self.B = self.set(2, self.B)
    def op_cb_d1(self): self.C = self.set(2, self.C)
    def op_cb_d2(self): self.D = self.set(2, self.D)
    def op_cb_d3(self): self.E = self.set(2, self.E)
    def op_cb_d4(self): self.H = self.set(2, self.H)
    def op_cb_d5(self): self.L = self.set(2, self.L)
    def op_cb_d6(self): self.wm(self.HL, self.set(2, self.rm_reg(self.HL)))
    def op_cb_d7(self): self.A = self.set(2, self.A)

    def op_cb_d8(self): self.B = self.set(3, self.B)
    def op_cb_d9(self): self.C = self.set(3, self.C)
    def op_cb_da(self): self.D = self.set(3, self.D)
    def op_cb_db(self): self.E = self.set(3, self.E)
    def op_cb_dc(self): self.H = self.set(3, self.H)
    def op_cb_dd(self): self.L = self.set(3, self.L)
    def op_cb_de(self): self.wm(self.HL, self.set(3, self.rm_reg(self.HL)))
    def op_cb_df(self): self.A = self.set(3, self.A)

    def op_cb_e0(self): self.B = self.set(4, self.B)
    def op_cb_e1(self): self.C = self.set(4, self.C)
    def op_cb_e2(self): self.D = self.set(4, self.D)
    def op_cb_e3(self): self.E = self.set(4, self.E)
    def op_cb_e4(self): self.H = self.set(4, self.H)
    def op_cb_e5(self): self.L = self.set(4, self.L)
    def op_cb_e6(self): self.wm(self.HL, self.set(4, self.rm_reg(self.HL)))
    def op_cb_e7(self): self.A = self.set(4, self.A)

    def op_cb_e8(self): self.B = self.set(5, self.B)
    def op_cb_e9(self): self.C = self.set(5, self.C)
    def op_cb_ea(self): self.D = self.set(5, self.D)
    def op_cb_eb(self): self.E = self.set(5, self.E)
    def op_cb_ec(self): self.H = self.set(5, self.H)
    def op_cb_ed(self): self.L = self.set(5, self.L)
    def op_cb_ee(self): self.wm(self.HL, self.set(5, self.rm_reg(self.HL)))
    def op_cb_ef(self): self.A = self.set(5, self.A)

    def op_cb_f0(self): self.B = self.set(6, self.B)
    def op_cb_f1(self): self.C = self.set(6, self.C)
    def op_cb_f2(self): self.D = self.set(6, self.D)
    def op_cb_f3(self): self.E = self.set(6, self.E)
    def op_cb_f4(self): self.H = self.set(6, self.H)
    def op_cb_f5(self): self.L = self.set(6, self.L)
    def op_cb_f6(self): self.wm(self.HL, self.set(6, self.rm_reg(self.HL)))
    def op_cb_f7(self): self.A = self.set(6, self.A)

    def op_cb_f8(self): self.B = self.set(7, self.B)
    def op_cb_f9(self): self.C = self.set(7, self.C)
    def op_cb_fa(self): self.D = self.set(7, self.D)
    def op_cb_fb(self): self.E = self.set(7, self.E)
    def op_cb_fc(self): self.H = self.set(7, self.H)
    def op_cb_fd(self): self.L = self.set(7, self.L)
    def op_cb_fe(self): self.wm(self.HL, self.set(7, self.rm_reg(self.HL)))
    def op_cb_ff(self): self.A = self.set(7, self.A)

    # opcodes with DD/FD CB prefix
    # rotate, shift and bit operations with (IX+o)
    def op_xycb_00(self): self.B = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_01(self): self.C = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_02(self): self.D = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_03(self): self.E = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_04(self): self.H = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_05(self): self.L = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_06(self): self.wm(self.m_ea, self.rlc(self.rm_reg(self.m_ea)))
    def op_xycb_07(self): self.A = self.rlc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_08(self): self.B = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_09(self): self.C = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_0a(self): self.D = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_0b(self): self.E = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_0c(self): self.H = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_0d(self): self.L = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_0e(self): self.wm(self.m_ea, self.rrc(self.rm_reg(self.m_ea)))
    def op_xycb_0f(self): self.A = self.rrc(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_10(self): self.B = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_11(self): self.C = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_12(self): self.D = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_13(self): self.E = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_14(self): self.H = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_15(self): self.L = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_16(self): self.wm(self.m_ea, self.rl(self.rm_reg(self.m_ea)))
    def op_xycb_17(self): self.A = self.rl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_18(self): self.B = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_19(self): self.C = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_1a(self): self.D = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_1b(self): self.E = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_1c(self): self.H = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_1d(self): self.L = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_1e(self): self.wm(self.m_ea, self.rr(self.rm_reg(self.m_ea)))
    def op_xycb_1f(self): self.A = self.rr(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_20(self): self.B = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_21(self): self.C = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_22(self): self.D = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_23(self): self.E = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_24(self): self.H = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_25(self): self.L = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_26(self): self.wm(self.m_ea, self.sla(self.rm_reg(self.m_ea)))
    def op_xycb_27(self): self.A = self.sla(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_28(self): self.B = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_29(self): self.C = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_2a(self): self.D = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_2b(self): self.E = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_2c(self): self.H = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_2d(self): self.L = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_2e(self): self.wm(self.m_ea, self.sra(self.rm_reg(self.m_ea)))
    def op_xycb_2f(self): self.A = self.sra(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_30(self): self.B = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_31(self): self.C = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_32(self): self.D = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_33(self): self.E = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_34(self): self.H = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_35(self): self.L = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_36(self): self.wm(self.m_ea, self.sll(self.rm_reg(self.m_ea)))
    def op_xycb_37(self): self.A = self.sll(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_38(self): self.B = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_39(self): self.C = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_3a(self): self.D = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_3b(self): self.E = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_3c(self): self.H = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_3d(self): self.L = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_3e(self): self.wm(self.m_ea, self.srl(self.rm_reg(self.m_ea)))
    def op_xycb_3f(self): self.A = self.srl(self.rmreg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_40(self): self.op_xycb_46()
    def op_xycb_41(self): self.op_xycb_46()
    def op_xycb_42(self): self.op_xycb_46()
    def op_xycb_43(self): self.op_xycb_46()
    def op_xycb_44(self): self.op_xycb_46()
    def op_xycb_45(self): self.op_xycb_46()
    def op_xycb_46(self): self.bit_xy(0, self.rm_reg(self.m_ea))
    def op_xycb_47(self): self.op_xycb_46()

    def op_xycb_48(self): self.op_xycb_4e()
    def op_xycb_49(self): self.op_xycb_4e()
    def op_xycb_4a(self): self.op_xycb_4e()
    def op_xycb_4b(self): self.op_xycb_4e()
    def op_xycb_4c(self): self.op_xycb_4e()
    def op_xycb_4d(self): self.op_xycb_4e()
    def op_xycb_4e(self): self.bit_xy(1, self.rm_reg(self.m_ea))
    def op_xycb_4f(self): self.op_xycb_4e()

    def op_xycb_50(self): self.op_xycb_56()
    def op_xycb_51(self): self.op_xycb_56()
    def op_xycb_52(self): self.op_xycb_56()
    def op_xycb_53(self): self.op_xycb_56()
    def op_xycb_54(self): self.op_xycb_56()
    def op_xycb_55(self): self.op_xycb_56()
    def op_xycb_56(self): self.bit_xy(2, self.rm_reg(self.m_ea))
    def op_xycb_57(self): self.op_xycb_56()

    def op_xycb_58(self): self.op_xycb_5e()
    def op_xycb_59(self): self.op_xycb_5e()
    def op_xycb_5a(self): self.op_xycb_5e()
    def op_xycb_5b(self): self.op_xycb_5e()
    def op_xycb_5c(self): self.op_xycb_5e()
    def op_xycb_5d(self): self.op_xycb_5e()
    def op_xycb_5e(self): self.bit_xy(3, self.rm_reg(self.m_ea))
    def op_xycb_5f(self): self.op_xycb_5e()

    def op_xycb_60(self): self.op_xycb_66()
    def op_xycb_61(self): self.op_xycb_66()
    def op_xycb_62(self): self.op_xycb_66()
    def op_xycb_63(self): self.op_xycb_66()
    def op_xycb_64(self): self.op_xycb_66()
    def op_xycb_65(self): self.op_xycb_66()
    def op_xycb_66(self): self.bit_xy(4, self.rm_reg(self.m_ea))
    def op_xycb_67(self): self.op_xycb_66()

    def op_xycb_68(self): self.op_xycb_6e()
    def op_xycb_69(self): self.op_xycb_6e()
    def op_xycb_6a(self): self.op_xycb_6e()
    def op_xycb_6b(self): self.op_xycb_6e()
    def op_xycb_6c(self): self.op_xycb_6e()
    def op_xycb_6d(self): self.op_xycb_6e()
    def op_xycb_6e(self): self.bit_xy(5, self.rm_reg(self.m_ea))
    def op_xycb_6f(self): self.op_xycb_6e()

    def op_xycb_70(self): self.op_xycb_76()
    def op_xycb_71(self): self.op_xycb_76()
    def op_xycb_72(self): self.op_xycb_76()
    def op_xycb_73(self): self.op_xycb_76()
    def op_xycb_74(self): self.op_xycb_76()
    def op_xycb_75(self): self.op_xycb_76()
    def op_xycb_76(self): self.bit_xy(6, self.rm_reg(self.m_ea))
    def op_xycb_77(self): self.op_xycb_76()

    def op_xycb_78(self): self.op_xycb_7e()
    def op_xycb_79(self): self.op_xycb_7e()
    def op_xycb_7a(self): self.op_xycb_7e()
    def op_xycb_7b(self): self.op_xycb_7e()
    def op_xycb_7c(self): self.op_xycb_7e()
    def op_xycb_7d(self): self.op_xycb_7e()
    def op_xycb_7e(self): self.bit_xy(7, self.rm_reg(self.m_ea))
    def op_xycb_7f(self): self.op_xycb_7e()

    def op_xycb_80(self): self.B = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_81(self): self.C = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_82(self): self.D = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_83(self): self.E = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_84(self): self.H = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_85(self): self.L = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_86(self): self.wm(self.m_ea, self.res(0, self.rm_reg(self.m_ea)))
    def op_xycb_87(self): self.A = self.res(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_88(self): self.B = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_89(self): self.C = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_8a(self): self.D = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_8b(self): self.E = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_8c(self): self.H = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_8d(self): self.L = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_8e(self): self.wm(self.m_ea, self.res(1, self.rm_reg(self.m_ea)))
    def op_xycb_8f(self): self.A = self.res(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_90(self): self.B = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_91(self): self.C = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_92(self): self.D = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_93(self): self.E = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_94(self): self.H = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_95(self): self.L = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_96(self): self.wm(self.m_ea, self.res(2, self.rm_reg(self.m_ea)))
    def op_xycb_97(self): self.A = self.res(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_98(self): self.B = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_99(self): self.C = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_9a(self): self.D = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_9b(self): self.E = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_9c(self): self.H = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_9d(self): self.L = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_9e(self): self.wm(self.m_ea, self.res(3, self.rm_reg(self.m_ea)))
    def op_xycb_9f(self): self.A = self.res(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_a0(self): self.B = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_a1(self): self.C = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_a2(self): self.D = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_a3(self): self.E = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_a4(self): self.H = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_a5(self): self.L = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_a6(self): self.wm(self.m_ea, self.res(4, self.rm_reg(self.m_ea)))
    def op_xycb_a7(self): self.A = self.res(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_a8(self): self.B = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_a9(self): self.C = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_aa(self): self.D = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_ab(self): self.E = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_ac(self): self.H = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_ad(self): self.L = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_ae(self): self.wm(self.m_ea, self.res(5, self.rm_reg(self.m_ea)))
    def op_xycb_af(self): self.A = self.res(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_b0(self): self.B = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_b1(self): self.C = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_b2(self): self.D = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_b3(self): self.E = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_b4(self): self.H = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_b5(self): self.L = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_b6(self): self.wm(self.m_ea, self.res(6, self.rm_reg(self.m_ea)))
    def op_xycb_b7(self): self.A = self.res(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_b8(self): self.B = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_b9(self): self.C = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_ba(self): self.D = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_bb(self): self.E = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_bc(self): self.H = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_bd(self): self.L = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_be(self): self.wm(self.m_ea, self.res(7, self.rm_reg(self.m_ea)))
    def op_xycb_bf(self): self.A = self.res(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_c0(self): self.B = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_c1(self): self.C = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_c2(self): self.D = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_c3(self): self.E = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_c4(self): self.H = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_c5(self): self.L = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_c6(self): self.wm(self.m_ea, self.set(0, self.rm_reg(self.m_ea)))
    def op_xycb_c7(self): self.A = self.set(0, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_c8(self): self.B = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_c9(self): self.C = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_ca(self): self.D = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_cb(self): self.E = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_cc(self): self.H = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_cd(self): self.L = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_ce(self): self.wm(self.m_ea, self.set(1, self.rm_reg(self.m_ea)))
    def op_xycb_cf(self): self.A = self.set(1, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_d0(self): self.B = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_d1(self): self.C = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_d2(self): self.D = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_d3(self): self.E = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_d4(self): self.H = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_d5(self): self.L = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_d6(self): self.wm(self.m_ea, self.set(2, self.rm_reg(self.m_ea)))
    def op_xycb_d7(self): self.A = self.set(2, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_d8(self): self.B = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_d9(self): self.C = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_da(self): self.D = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_db(self): self.E = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_dc(self): self.H = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_dd(self): self.L = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_de(self): self.wm(self.m_ea, self.set(3, self.rm_reg(self.m_ea)))
    def op_xycb_df(self): self.A = self.set(3, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_e0(self): self.B = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_e1(self): self.C = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_e2(self): self.D = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_e3(self): self.E = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_e4(self): self.H = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_e5(self): self.L = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_e6(self): self.wm(self.m_ea, self.set(4, self.rm_reg(self.m_ea)))
    def op_xycb_e7(self): self.A = self.set(4, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_e8(self): self.B = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_e9(self): self.C = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_ea(self): self.D = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_eb(self): self.E = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_ec(self): self.H = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_ed(self): self.L = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_ee(self): self.wm(self.m_ea, self.set(5, self.rm_reg(self.m_ea)))
    def op_xycb_ef(self): self.A = self.set(5, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_f0(self): self.B = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_f1(self): self.C = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_f2(self): self.D = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_f3(self): self.E = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_f4(self): self.H = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_f5(self): self.L = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_f6(self): self.wm(self.m_ea, self.set(6, self.rm_reg(self.m_ea)))
    def op_xycb_f7(self): self.A = self.set(6, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_xycb_f8(self): self.B = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.B)
    def op_xycb_f9(self): self.C = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.C)
    def op_xycb_fa(self): self.D = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.D)
    def op_xycb_fb(self): self.E = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.E)
    def op_xycb_fc(self): self.H = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.H)
    def op_xycb_fd(self): self.L = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.L)
    def op_xycb_fe(self): self.wm(self.m_ea, self.set(7, self.rm_reg(self.m_ea)))
    def op_xycb_ff(self): self.A = self.set(7, self.rm_reg(self.m_ea)); self.wm(self.m_ea, self.A)

    def op_illegal_1(self):
        self.log("Z80 ill. opcode ${:02x} ${:02x} (${:04x})".format(
            self.m_opcodes.read(self.PC-2),
            self.m_opcodes.read(self.PC-1),
            self.PC-2))

    # IX register related opcodes (DD prefix)
    def op_dd_00(self): self.op_illegal_1(); self.op_op_00()
    def op_dd_01(self): self.op_illegal_1(); self.op_op_01()
    def op_dd_02(self): self.op_illegal_1(); self.op_op_02()
    def op_dd_03(self): self.op_illegal_1(); self.op_op_03()
    def op_dd_04(self): self.op_illegal_1(); self.op_op_04()
    def op_dd_05(self): self.op_illegal_1(); self.op_op_05()
    def op_dd_06(self): self.op_illegal_1(); self.op_op_06()
    def op_dd_07(self): self.op_illegal_1(); self.op_op_07()

    def op_dd_08(self): self.op_illegal_1(); self.op_op_08()
    def op_dd_09(self): self.add16(self.m_ix, self.m_bc)
    def op_dd_0a(self): self.op_illegal_1(); self.op_op_0a()
    def op_dd_0b(self): self.op_illegal_1(); self.op_op_0b()
    def op_dd_0c(self): self.op_illegal_1(); self.op_op_0c()
    def op_dd_0d(self): self.op_illegal_1(); self.op_op_0d()
    def op_dd_0e(self): self.op_illegal_1(); self.op_op_0e()
    def op_dd_0f(self): self.op_illegal_1(); self.op_op_0f()

    def op_dd_10(self): self.op_illegal_1(); self.op_op_10()
    def op_dd_11(self): self.op_illegal_1(); self.op_op_11()
    def op_dd_12(self): self.op_illegal_1(); self.op_op_12()
    def op_dd_13(self): self.op_illegal_1(); self.op_op_13()
    def op_dd_14(self): self.op_illegal_1(); self.op_op_14()
    def op_dd_15(self): self.op_illegal_1(); self.op_op_15()
    def op_dd_16(self): self.op_illegal_1(); self.op_op_16()
    def op_dd_17(self): self.op_illegal_1(); self.op_op_17()

    def op_dd_18(self): self.op_illegal_1(); self.op_op_18()
    def op_dd_19(self): self.add16(self.m_ix, self.m_de)
    def op_dd_1a(self): self.op_illegal_1(); self.op_op_1a()
    def op_dd_1b(self): self.op_illegal_1(); self.op_op_1b()
    def op_dd_1c(self): self.op_illegal_1(); self.op_op_1c()
    def op_dd_1d(self): self.op_illegal_1(); self.op_op_1d()
    def op_dd_1e(self): self.op_illegal_1(); self.op_op_1e()
    def op_dd_1f(self): self.op_illegal_1(); self.op_op_1f()

    def op_dd_20(self): self.op_illegal_1(); self.op_op_20()
    def op_dd_21(self): self.IX = self.arg16()
    def op_dd_22(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_ix); self.WZ = self.m_ea + 1
    def op_dd_23(self): self.nomreq_ir(2); self.IX += 1
    def op_dd_24(self): self.HX = self.inc(self.HX)
    def op_dd_25(self): self.HX = self.dec(self.HX)
    def op_dd_26(self): self.HX = self.arg()
    def op_dd_27(self): self.op_illegal_1(); self.op_op_27()

    def op_dd_28(self): self.op_illegal_1(); self.op_op_28()
    def op_dd_29(self): self.add16(self.m_ix, self.m_ix)
    def op_dd_2a(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_ix); self.WZ = self.m_ea + 1
    def op_dd_2b(self): self.nomreq_ir(2); self.IX -= 1
    def op_dd_2c(self): self.LX = self.inc(self.LX)
    def op_dd_2d(self): self.LX = self.dec(self.LX)
    def op_dd_2e(self): self.LX = self.arg()
    def op_dd_2f(self): self.op_illegal_1(); self.op_op_2f()

    def op_dd_30(self): self.op_illegal_1(); self.op_op_30()
    def op_dd_31(self): self.op_illegal_1(); self.op_op_31()
    def op_dd_32(self): self.op_illegal_1(); self.op_op_32()
    def op_dd_33(self): self.op_illegal_1(); self.op_op_33()
    def op_dd_34(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.inc(self.rm_reg(self.m_ea)))
    def op_dd_35(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.dec(self.rm_reg(self.m_ea)))
    def op_dd_36(self): self.eax(); a = self.arg(); self.nomreq_addr(self.PC - 1, 2); self.wm(self.m_ea, a)
    def op_dd_37(self): self.op_illegal_1(); self.op_op_37()

    def op_dd_38(self): self.op_illegal_1(); self.op_op_38()
    def op_dd_39(self): self.add16(self.m_ix, self.m_sp)
    def op_dd_3a(self): self.op_illegal_1(); self.op_op_3a()
    def op_dd_3b(self): self.op_illegal_1(); self.op_op_3b()
    def op_dd_3c(self): self.op_illegal_1(); self.op_op_3c()
    def op_dd_3d(self): self.op_illegal_1(); self.op_op_3d()
    def op_dd_3e(self): self.op_illegal_1(); self.op_op_3e()
    def op_dd_3f(self): self.op_illegal_1(); self.op_op_3f()

    def op_dd_40(self): self.op_illegal_1(); self.op_op_40()
    def op_dd_41(self): self.op_illegal_1(); self.op_op_41()
    def op_dd_42(self): self.op_illegal_1(); self.op_op_42()
    def op_dd_43(self): self.op_illegal_1(); self.op_op_43()
    def op_dd_44(self): self.B = self.HX
    def op_dd_45(self): self.B = self.LX
    def op_dd_46(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.B = self.rm(self.m_ea)
    def op_dd_47(self): self.op_illegal_1(); self.op_op_47()

    def op_dd_48(self): self.op_illegal_1(); self.op_op_48()
    def op_dd_49(self): self.op_illegal_1(); self.op_op_49()
    def op_dd_4a(self): self.op_illegal_1(); self.op_op_4a()
    def op_dd_4b(self): self.op_illegal_1(); self.op_op_4b()
    def op_dd_4c(self): self.C = self.HX
    def op_dd_4d(self): self.C = self.LX
    def op_dd_4e(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.C = self.rm(self.m_ea)
    def op_dd_4f(self): self.op_illegal_1(); self.op_op_4f()

    def op_dd_50(self): self.op_illegal_1(); self.op_op_50()
    def op_dd_51(self): self.op_illegal_1(); self.op_op_51()
    def op_dd_52(self): self.op_illegal_1(); self.op_op_52()
    def op_dd_53(self): self.op_illegal_1(); self.op_op_53()
    def op_dd_54(self): self.D = self.HX
    def op_dd_55(self): self.D = self.LX
    def op_dd_56(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.D = self.rm(self.m_ea)
    def op_dd_57(self): self.op_illegal_1(); self.op_op_57()

    def op_dd_58(self): self.op_illegal_1(); self.op_op_58()
    def op_dd_59(self): self.op_illegal_1(); self.op_op_59()
    def op_dd_5a(self): self.op_illegal_1(); self.op_op_5a()
    def op_dd_5b(self): self.op_illegal_1(); self.op_op_5b()
    def op_dd_5c(self): self.E = self.HX
    def op_dd_5d(self): self.E = self.LX
    def op_dd_5e(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.E = self.rm(self.m_ea)
    def op_dd_5f(self): self.op_illegal_1(); self.op_op_5f()

    def op_dd_60(self): self.HX = self.B
    def op_dd_61(self): self.HX = self.C
    def op_dd_62(self): self.HX = self.D
    def op_dd_63(self): self.HX = self.E
    def op_dd_64(self): pass
    def op_dd_65(self): self.HX = self.LX
    def op_dd_66(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.H = self.rm(self.m_ea)
    def op_dd_67(self): self.HX = self.A

    def op_dd_68(self): self.LX = self.B
    def op_dd_69(self): self.LX = self.C
    def op_dd_6a(self): self.LX = self.D
    def op_dd_6b(self): self.LX = self.E
    def op_dd_6c(self): self.LX = self.HX
    def op_dd_6d(self): pass
    def op_dd_6e(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.L = self.rm(self.m_ea)
    def op_dd_6f(self): self.LX = self.A

    def op_dd_70(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.B)
    def op_dd_71(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.C)
    def op_dd_72(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.D)
    def op_dd_73(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.E)
    def op_dd_74(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.H)
    def op_dd_75(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.L)
    def op_dd_76(self): self.op_illegal_1(); self.op_op_76()
    def op_dd_77(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.A)

    def op_dd_78(self): self.op_illegal_1(); self.op_op_78()
    def op_dd_79(self): self.op_illegal_1(); self.op_op_79()
    def op_dd_7a(self): self.op_illegal_1(); self.op_op_7a()
    def op_dd_7b(self): self.op_illegal_1(); self.op_op_7b()
    def op_dd_7c(self): self.A = self.HX
    def op_dd_7d(self): self.A = self.LX
    def op_dd_7e(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.A = self.rm(self.m_ea)
    def op_dd_7f(self): self.op_illegal_1(); self.op_op_7f()

    def op_dd_80(self): self.op_illegal_1(); self.op_op_80()
    def op_dd_81(self): self.op_illegal_1(); self.op_op_81()
    def op_dd_82(self): self.op_illegal_1(); self.op_op_82()
    def op_dd_83(self): self.op_illegal_1(); self.op_op_83()
    def op_dd_84(self): self.add_a(self.HX)
    def op_dd_85(self): self.add_a(self.LX)
    def op_dd_86(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.add_a(self.rm(self.m_ea))
    def op_dd_87(self): self.op_illegal_1(); self.op_op_87()

    def op_dd_88(self): self.op_illegal_1(); self.op_op_88()
    def op_dd_89(self): self.op_illegal_1(); self.op_op_89()
    def op_dd_8a(self): self.op_illegal_1(); self.op_op_8a()
    def op_dd_8b(self): self.op_illegal_1(); self.op_op_8b()
    def op_dd_8c(self): self.adc_a(self.HX)
    def op_dd_8d(self): self.adc_a(self.LX)
    def op_dd_8e(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.adc_a(self.rm(self.m_ea))
    def op_dd_8f(self): self.op_illegal_1(); self.op_op_8f()

    def op_dd_90(self): self.op_illegal_1(); self.op_op_90()
    def op_dd_91(self): self.op_illegal_1(); self.op_op_91()
    def op_dd_92(self): self.op_illegal_1(); self.op_op_92()
    def op_dd_93(self): self.op_illegal_1(); self.op_op_93()
    def op_dd_94(self): self.sub(self.HX)
    def op_dd_95(self): self.sub(self.LX)
    def op_dd_96(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.sub(self.rm(self.m_ea))
    def op_dd_97(self): self.op_illegal_1(); self.op_op_97()

    def op_dd_98(self): self.op_illegal_1(); self.op_op_98()
    def op_dd_99(self): self.op_illegal_1(); self.op_op_99()
    def op_dd_9a(self): self.op_illegal_1(); self.op_op_9a()
    def op_dd_9b(self): self.op_illegal_1(); self.op_op_9b()
    def op_dd_9c(self): self.sbc_a(self.HX)
    def op_dd_9d(self): self.sbc_a(self.LX)
    def op_dd_9e(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.sbc_a(self.rm(self.m_ea))
    def op_dd_9f(self): self.op_illegal_1(); self.op_op_9f()

    def op_dd_a0(self): self.op_illegal_1(); self.op_op_a0()
    def op_dd_a1(self): self.op_illegal_1(); self.op_op_a1()
    def op_dd_a2(self): self.op_illegal_1(); self.op_op_a2()
    def op_dd_a3(self): self.op_illegal_1(); self.op_op_a3()
    def op_dd_a4(self): self.and_a(self.HX)
    def op_dd_a5(self): self.and_a(self.LX)
    def op_dd_a6(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.and_a(self.rm(self.m_ea))
    def op_dd_a7(self): self.op_illegal_1(); self.op_op_a7()

    def op_dd_a8(self): self.op_illegal_1(); self.op_op_a8()
    def op_dd_a9(self): self.op_illegal_1(); self.op_op_a9()
    def op_dd_aa(self): self.op_illegal_1(); self.op_op_aa()
    def op_dd_ab(self): self.op_illegal_1(); self.op_op_ab()
    def op_dd_ac(self): self.xor_a(self.HX)
    def op_dd_ad(self): self.xor_a(self.LX)
    def op_dd_ae(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.xor_a(self.rm(self.m_ea))
    def op_dd_af(self): self.op_illegal_1(); self.op_op_af()

    def op_dd_b0(self): self.op_illegal_1(); self.op_op_b0()
    def op_dd_b1(self): self.op_illegal_1(); self.op_op_b1()
    def op_dd_b2(self): self.op_illegal_1(); self.op_op_b2()
    def op_dd_b3(self): self.op_illegal_1(); self.op_op_b3()
    def op_dd_b4(self): self.or_a(self.HX)
    def op_dd_b5(self): self.or_a(self.LX)
    def op_dd_b6(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.or_a(self.rm(self.m_ea))
    def op_dd_b7(self): self.op_illegal_1(); self.op_op_b7()

    def op_dd_b8(self): self.op_illegal_1(); self.op_op_b8()
    def op_dd_b9(self): self.op_illegal_1(); self.op_op_b9()
    def op_dd_ba(self): self.op_illegal_1(); self.op_op_ba()
    def op_dd_bb(self): self.op_illegal_1(); self.op_op_bb()
    def op_dd_bc(self): self.cp(self.HX)
    def op_dd_bd(self): self.cp(self.LX)
    def op_dd_be(self): self.eax(); self.nomreq_addr(self.PC - 1, 5); self.cp(self.rm(self.m_ea))
    def op_dd_bf(self): self.op_illegal_1(); self.op_op_bf()

    def op_dd_c0(self): self.op_illegal_1(); self.op_op_c0()
    def op_dd_c1(self): self.op_illegal_1(); self.op_op_c1()
    def op_dd_c2(self): self.op_illegal_1(); self.op_op_c2()
    def op_dd_c3(self): self.op_illegal_1(); self.op_op_c3()
    def op_dd_c4(self): self.op_illegal_1(); self.op_op_c4()
    def op_dd_c5(self): self.op_illegal_1(); self.op_op_c5()
    def op_dd_c6(self): self.op_illegal_1(); self.op_op_c6()
    def op_dd_c7(self): self.op_illegal_1(); self.op_op_c7()

    def op_dd_c8(self): self.op_illegal_1(); self.op_op_c8()
    def op_dd_c9(self): self.op_illegal_1(); self.op_op_c9()
    def op_dd_ca(self): self.op_illegal_1(); self.op_op_ca()
    def op_dd_cb(self): self.eax(); a = self.arg(); self.nomreq_addr(self.PC - 1, 2); self.EXEC(Z80.cc_xycb, self.op_xycb, a)
    def op_dd_cc(self): self.op_illegal_1(); self.op_op_cc()
    def op_dd_cd(self): self.op_illegal_1(); self.op_op_cd()
    def op_dd_ce(self): self.op_illegal_1(); self.op_op_ce()
    def op_dd_cf(self): self.op_illegal_1(); self.op_op_cf()

    def op_dd_d0(self): self.op_illegal_1(); self.op_op_d0()
    def op_dd_d1(self): self.op_illegal_1(); self.op_op_d1()
    def op_dd_d2(self): self.op_illegal_1(); self.op_op_d2()
    def op_dd_d3(self): self.op_illegal_1(); self.op_op_d3()
    def op_dd_d4(self): self.op_illegal_1(); self.op_op_d4()
    def op_dd_d5(self): self.op_illegal_1(); self.op_op_d5()
    def op_dd_d6(self): self.op_illegal_1(); self.op_op_d6()
    def op_dd_d7(self): self.op_illegal_1(); self.op_op_d7()

    def op_dd_d8(self): self.op_illegal_1(); self.op_op_d8()
    def op_dd_d9(self): self.op_illegal_1(); self.op_op_d9()
    def op_dd_da(self): self.op_illegal_1(); self.op_op_da()
    def op_dd_db(self): self.op_illegal_1(); self.op_op_db()
    def op_dd_dc(self): self.op_illegal_1(); self.op_op_dc()
    def op_dd_dd(self): self.op_illegal_1(); self.op_op_dd()
    def op_dd_de(self): self.op_illegal_1(); self.op_op_de()
    def op_dd_df(self): self.op_illegal_1(); self.op_op_df()

    def op_dd_e0(self): self.op_illegal_1(); self.op_op_e0()
    def op_dd_e1(self): self.pop(self.m_ix)
    def op_dd_e2(self): self.op_illegal_1(); self.op_op_e2()
    def op_dd_e3(self): self.ex_sp(self.m_ix)
    def op_dd_e4(self): self.op_illegal_1(); self.op_op_e4()
    def op_dd_e5(self): self.push(self.m_ix)
    def op_dd_e6(self): self.op_illegal_1(); self.op_op_e6()
    def op_dd_e7(self): self.op_illegal_1(); self.op_op_e7()

    def op_dd_e8(self): self.op_illegal_1(); self.op_op_e8()
    def op_dd_e9(self): self.PC = self.IX
    def op_dd_ea(self): self.op_illegal_1(); self.op_op_ea()
    def op_dd_eb(self): self.op_illegal_1(); self.op_op_eb()
    def op_dd_ec(self): self.op_illegal_1(); self.op_op_ec()
    def op_dd_ed(self): self.op_illegal_1(); self.op_op_ed()
    def op_dd_ee(self): self.op_illegal_1(); self.op_op_ee()
    def op_dd_ef(self): self.op_illegal_1(); self.op_op_ef()

    def op_dd_f0(self): self.op_illegal_1(); self.op_op_f0()
    def op_dd_f1(self): self.op_illegal_1(); self.op_op_f1()
    def op_dd_f2(self): self.op_illegal_1(); self.op_op_f2()
    def op_dd_f3(self): self.op_illegal_1(); self.op_op_f3()
    def op_dd_f4(self): self.op_illegal_1(); self.op_op_f4()
    def op_dd_f5(self): self.op_illegal_1(); self.op_op_f5()
    def op_dd_f6(self): self.op_illegal_1(); self.op_op_f6()
    def op_dd_f7(self): self.op_illegal_1(); self.op_op_f7()

    def op_dd_f8(self): self.op_illegal_1(); self.op_op_f8()
    def op_dd_f9(self): self.nomreq_ir(2); self.SP = self.IX
    def op_dd_fa(self): self.op_illegal_1(); self.op_op_fa()
    def op_dd_fb(self): self.op_illegal_1(); self.op_op_fb()
    def op_dd_fc(self): self.op_illegal_1(); self.op_op_fc()
    def op_dd_fd(self): self.op_illegal_1(); self.op_op_fd()
    def op_dd_fe(self): self.op_illegal_1(); self.op_op_fe()
    def op_dd_ff(self): self.op_illegal_1(); self.op_op_ff()

    # IY register related opcodes (FD prefix)
    def op_fd_00(self): self.op_illegal_1(); self.op_op_00()
    def op_fd_01(self): self.op_illegal_1(); self.op_op_01()
    def op_fd_02(self): self.op_illegal_1(); self.op_op_02()
    def op_fd_03(self): self.op_illegal_1(); self.op_op_03()
    def op_fd_04(self): self.op_illegal_1(); self.op_op_04()
    def op_fd_05(self): self.op_illegal_1(); self.op_op_05()
    def op_fd_06(self): self.op_illegal_1(); self.op_op_06()
    def op_fd_07(self): self.op_illegal_1(); self.op_op_07()

    def op_fd_08(self): self.op_illegal_1(); self.op_op_08()
    def op_fd_09(self): self.add16(self.m_iy, self.m_bc)
    def op_fd_0a(self): self.op_illegal_1(); self.op_op_0a()
    def op_fd_0b(self): self.op_illegal_1(); self.op_op_0b()
    def op_fd_0c(self): self.op_illegal_1(); self.op_op_0c()
    def op_fd_0d(self): self.op_illegal_1(); self.op_op_0d()
    def op_fd_0e(self): self.op_illegal_1(); self.op_op_0e()
    def op_fd_0f(self): self.op_illegal_1(); self.op_op_0f()

    def op_fd_10(self): self.op_illegal_1(); self.op_op_10()
    def op_fd_11(self): self.op_illegal_1(); self.op_op_11()
    def op_fd_12(self): self.op_illegal_1(); self.op_op_12()
    def op_fd_13(self): self.op_illegal_1(); self.op_op_13()
    def op_fd_14(self): self.op_illegal_1(); self.op_op_14()
    def op_fd_15(self): self.op_illegal_1(); self.op_op_15()
    def op_fd_16(self): self.op_illegal_1(); self.op_op_16()
    def op_fd_17(self): self.op_illegal_1(); self.op_op_17()

    def op_fd_18(self): self.op_illegal_1(); self.op_op_18()
    def op_fd_19(self): self.add16(self.m_iy, self.m_de)
    def op_fd_1a(self): self.op_illegal_1(); self.op_op_1a()
    def op_fd_1b(self): self.op_illegal_1(); self.op_op_1b()
    def op_fd_1c(self): self.op_illegal_1(); self.op_op_1c()
    def op_fd_1d(self): self.op_illegal_1(); self.op_op_1d()
    def op_fd_1e(self): self.op_illegal_1(); self.op_op_1e()
    def op_fd_1f(self): self.op_illegal_1(); self.op_op_1f()

    def op_fd_20(self): self.op_illegal_1(); self.op_op_20()
    def op_fd_21(self): self.IY = self.arg16()
    def op_fd_22(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_iy); self.WZ = self.m_ea + 1
    def op_fd_23(self): self.nomreq_ir(2); self.IY += 1
    def op_fd_24(self): self.HY = self.inc(self.HY)
    def op_fd_25(self): self.HY = self.dec(self.HY)
    def op_fd_26(self): self.HY = self.arg()
    def op_fd_27(self): self.op_illegal_1(); self.op_op_27()

    def op_fd_28(self): self.op_illegal_1(); self.op_op_28()
    def op_fd_29(self): self.add16(self.m_iy, self.m_iy)
    def op_fd_2a(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_iy); self.WZ = self.m_ea + 1
    def op_fd_2b(self): self.nomreq_ir(2); self.IY -= 1
    def op_fd_2c(self): self.LY = self.inc(self.LY)
    def op_fd_2d(self): self.LY = self.dec(self.LY)
    def op_fd_2e(self): self.LY = self.arg()
    def op_fd_2f(self): self.op_illegal_1(); self.op_op_2f()

    def op_fd_30(self): self.op_illegal_1(); self.op_op_30()
    def op_fd_31(self): self.op_illegal_1(); self.op_op_31()
    def op_fd_32(self): self.op_illegal_1(); self.op_op_32()
    def op_fd_33(self): self.op_illegal_1(); self.op_op_33()
    def op_fd_34(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.inc(self.rm_reg(self.m_ea)))
    def op_fd_35(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.dec(self.rm_reg(self.m_ea)))
    def op_fd_36(self): self.eay(); a = self.arg(); self.nomreq_addr(self.PC - 1, 2); self.wm(self.m_ea, a)
    def op_fd_37(self): self.op_illegal_1(); self.op_op_37()

    def op_fd_38(self): self.op_illegal_1(); self.op_op_38()
    def op_fd_39(self): self.add16(self.m_iy, self.m_sp)
    def op_fd_3a(self): self.op_illegal_1(); self.op_op_3a()
    def op_fd_3b(self): self.op_illegal_1(); self.op_op_3b()
    def op_fd_3c(self): self.op_illegal_1(); self.op_op_3c()
    def op_fd_3d(self): self.op_illegal_1(); self.op_op_3d()
    def op_fd_3e(self): self.op_illegal_1(); self.op_op_3e()
    def op_fd_3f(self): self.op_illegal_1(); self.op_op_3f()

    def op_fd_40(self): self.op_illegal_1(); self.op_op_40()
    def op_fd_41(self): self.op_illegal_1(); self.op_op_41()
    def op_fd_42(self): self.op_illegal_1(); self.op_op_42()
    def op_fd_43(self): self.op_illegal_1(); self.op_op_43()
    def op_fd_44(self): self.B = self.HY
    def op_fd_45(self): self.B = self.LY
    def op_fd_46(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.B = self.rm(self.m_ea)
    def op_fd_47(self): self.op_illegal_1(); self.op_op_47()

    def op_fd_48(self): self.op_illegal_1(); self.op_op_48()
    def op_fd_49(self): self.op_illegal_1(); self.op_op_49()
    def op_fd_4a(self): self.op_illegal_1(); self.op_op_4a()
    def op_fd_4b(self): self.op_illegal_1(); self.op_op_4b()
    def op_fd_4c(self): self.C = self.HY
    def op_fd_4d(self): self.C = self.LY
    def op_fd_4e(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.C = self.rm(self.m_ea)
    def op_fd_4f(self): self.op_illegal_1(); self.op_op_4f()

    def op_fd_50(self): self.op_illegal_1(); self.op_op_50()
    def op_fd_51(self): self.op_illegal_1(); self.op_op_51()
    def op_fd_52(self): self.op_illegal_1(); self.op_op_52()
    def op_fd_53(self): self.op_illegal_1(); self.op_op_53()
    def op_fd_54(self): self.D = self.HY
    def op_fd_55(self): self.D = self.LY
    def op_fd_56(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.D = self.rm(self.m_ea)
    def op_fd_57(self): self.op_illegal_1(); self.op_op_57()

    def op_fd_58(self): self.op_illegal_1(); self.op_op_58()
    def op_fd_59(self): self.op_illegal_1(); self.op_op_59()
    def op_fd_5a(self): self.op_illegal_1(); self.op_op_5a()
    def op_fd_5b(self): self.op_illegal_1(); self.op_op_5b()
    def op_fd_5c(self): self.E = self.HY
    def op_fd_5d(self): self.E = self.LY
    def op_fd_5e(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.E = self.rm(self.m_ea)
    def op_fd_5f(self): self.op_illegal_1(); self.op_op_5f()

    def op_fd_60(self): self.HY = self.B
    def op_fd_61(self): self.HY = self.C
    def op_fd_62(self): self.HY = self.D
    def op_fd_63(self): self.HY = self.E
    def op_fd_64(self): pass
    def op_fd_65(self): self.HY = self.LY
    def op_fd_66(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.H = self.rm(self.m_ea)
    def op_fd_67(self): self.HY = self.A

    def op_fd_68(self): self.LY = self.B
    def op_fd_69(self): self.LY = self.C
    def op_fd_6a(self): self.LY = self.D
    def op_fd_6b(self): self.LY = self.E
    def op_fd_6c(self): self.LY = self.HY
    def op_fd_6d(self): pass
    def op_fd_6e(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.L = self.rm(self.m_ea)
    def op_fd_6f(self): self.LY = self.A

    def op_fd_70(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.B)
    def op_fd_71(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.C)
    def op_fd_72(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.D)
    def op_fd_73(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.E)
    def op_fd_74(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.H)
    def op_fd_75(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.L)
    def op_fd_76(self): self.op_illegal_1(); self.op_op_76()
    def op_fd_77(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.wm(self.m_ea, self.A)

    def op_fd_78(self): self.op_illegal_1(); self.op_op_78()
    def op_fd_79(self): self.op_illegal_1(); self.op_op_79()
    def op_fd_7a(self): self.op_illegal_1(); self.op_op_7a()
    def op_fd_7b(self): self.op_illegal_1(); self.op_op_7b()
    def op_fd_7c(self): self.A = self.HY
    def op_fd_7d(self): self.A = self.LY
    def op_fd_7e(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.A = self.rm(self.m_ea)
    def op_fd_7f(self): self.op_illegal_1(); self.op_op_7f()

    def op_fd_80(self): self.op_illegal_1(); self.op_op_80()
    def op_fd_81(self): self.op_illegal_1(); self.op_op_81()
    def op_fd_82(self): self.op_illegal_1(); self.op_op_82()
    def op_fd_83(self): self.op_illegal_1(); self.op_op_83()
    def op_fd_84(self): self.add_a(self.HY)
    def op_fd_85(self): self.add_a(self.LY)
    def op_fd_86(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.add_a(self.rm(self.m_ea))
    def op_fd_87(self): self.op_illegal_1(); self.op_op_87()

    def op_fd_88(self): self.op_illegal_1(); self.op_op_88()
    def op_fd_89(self): self.op_illegal_1(); self.op_op_89()
    def op_fd_8a(self): self.op_illegal_1(); self.op_op_8a()
    def op_fd_8b(self): self.op_illegal_1(); self.op_op_8b()
    def op_fd_8c(self): self.adc_a(self.HY)
    def op_fd_8d(self): self.adc_a(self.LY)
    def op_fd_8e(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.adc_a(self.rm(self.m_ea))
    def op_fd_8f(self): self.op_illegal_1(); self.op_op_8f()

    def op_fd_90(self): self.op_illegal_1(); self.op_op_90()
    def op_fd_91(self): self.op_illegal_1(); self.op_op_91()
    def op_fd_92(self): self.op_illegal_1(); self.op_op_92()
    def op_fd_93(self): self.op_illegal_1(); self.op_op_93()
    def op_fd_94(self): self.sub(self.HY)
    def op_fd_95(self): self.sub(self.LY)
    def op_fd_96(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.sub(self.rm(self.m_ea))
    def op_fd_97(self): self.op_illegal_1(); self.op_op_97()

    def op_fd_98(self): self.op_illegal_1(); self.op_op_98()
    def op_fd_99(self): self.op_illegal_1(); self.op_op_99()
    def op_fd_9a(self): self.op_illegal_1(); self.op_op_9a()
    def op_fd_9b(self): self.op_illegal_1(); self.op_op_9b()
    def op_fd_9c(self): self.sbc_a(self.HY)
    def op_fd_9d(self): self.sbc_a(self.LY)
    def op_fd_9e(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.sbc_a(self.rm(self.m_ea))
    def op_fd_9f(self): self.op_illegal_1(); self.op_op_9f()

    def op_fd_a0(self): self.op_illegal_1(); self.op_op_a0()
    def op_fd_a1(self): self.op_illegal_1(); self.op_op_a1()
    def op_fd_a2(self): self.op_illegal_1(); self.op_op_a2()
    def op_fd_a3(self): self.op_illegal_1(); self.op_op_a3()
    def op_fd_a4(self): self.and_a(self.HY)
    def op_fd_a5(self): self.and_a(self.LY)
    def op_fd_a6(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.and_a(self.rm(self.m_ea))
    def op_fd_a7(self): self.op_illegal_1(); self.op_op_a7()

    def op_fd_a8(self): self.op_illegal_1(); self.op_op_a8()
    def op_fd_a9(self): self.op_illegal_1(); self.op_op_a9()
    def op_fd_aa(self): self.op_illegal_1(); self.op_op_aa()
    def op_fd_ab(self): self.op_illegal_1(); self.op_op_ab()
    def op_fd_ac(self): self.xor_a(self.HY)
    def op_fd_ad(self): self.xor_a(self.LY)
    def op_fd_ae(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.xor_a(self.rm(self.m_ea))
    def op_fd_af(self): self.op_illegal_1(); self.op_op_af()

    def op_fd_b0(self): self.op_illegal_1(); self.op_op_b0()
    def op_fd_b1(self): self.op_illegal_1(); self.op_op_b1()
    def op_fd_b2(self): self.op_illegal_1(); self.op_op_b2()
    def op_fd_b3(self): self.op_illegal_1(); self.op_op_b3()
    def op_fd_b4(self): self.or_a(self.HY)
    def op_fd_b5(self): self.or_a(self.LY)
    def op_fd_b6(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.or_a(self.rm(self.m_ea))
    def op_fd_b7(self): self.op_illegal_1(); self.op_op_b7()

    def op_fd_b8(self): self.op_illegal_1(); self.op_op_b8()
    def op_fd_b9(self): self.op_illegal_1(); self.op_op_b9()
    def op_fd_ba(self): self.op_illegal_1(); self.op_op_ba()
    def op_fd_bb(self): self.op_illegal_1(); self.op_op_bb()
    def op_fd_bc(self): self.cp(self.HY)
    def op_fd_bd(self): self.cp(self.LY)
    def op_fd_be(self): self.eay(); self.nomreq_addr(self.PC - 1, 5); self.cp(self.rm(self.m_ea))
    def op_fd_bf(self): self.op_illegal_1(); self.op_op_bf()

    def op_fd_c0(self): self.op_illegal_1(); self.op_op_c0()
    def op_fd_c1(self): self.op_illegal_1(); self.op_op_c1()
    def op_fd_c2(self): self.op_illegal_1(); self.op_op_c2()
    def op_fd_c3(self): self.op_illegal_1(); self.op_op_c3()
    def op_fd_c4(self): self.op_illegal_1(); self.op_op_c4()
    def op_fd_c5(self): self.op_illegal_1(); self.op_op_c5()
    def op_fd_c6(self): self.op_illegal_1(); self.op_op_c6()
    def op_fd_c7(self): self.op_illegal_1(); self.op_op_c7()

    def op_fd_c8(self): self.op_illegal_1(); self.op_op_c8()
    def op_fd_c9(self): self.op_illegal_1(); self.op_op_c9()
    def op_fd_ca(self): self.op_illegal_1(); self.op_op_ca()
    def op_fd_cb(self): self.eay(); a = self.arg(); self.nomreq_addr(self.PC - 1, 2); self.EXEC(Z80.cc_xycb, self.op_xycb, a)
    def op_fd_cc(self): self.op_illegal_1(); self.op_op_cc()
    def op_fd_cd(self): self.op_illegal_1(); self.op_op_cd()
    def op_fd_ce(self): self.op_illegal_1(); self.op_op_ce()
    def op_fd_cf(self): self.op_illegal_1(); self.op_op_cf()

    def op_fd_d0(self): self.op_illegal_1(); self.op_op_d0()
    def op_fd_d1(self): self.op_illegal_1(); self.op_op_d1()
    def op_fd_d2(self): self.op_illegal_1(); self.op_op_d2()
    def op_fd_d3(self): self.op_illegal_1(); self.op_op_d3()
    def op_fd_d4(self): self.op_illegal_1(); self.op_op_d4()
    def op_fd_d5(self): self.op_illegal_1(); self.op_op_d5()
    def op_fd_d6(self): self.op_illegal_1(); self.op_op_d6()
    def op_fd_d7(self): self.op_illegal_1(); self.op_op_d7()

    def op_fd_d8(self): self.op_illegal_1(); self.op_op_d8()
    def op_fd_d9(self): self.op_illegal_1(); self.op_op_d9()
    def op_fd_da(self): self.op_illegal_1(); self.op_op_da()
    def op_fd_db(self): self.op_illegal_1(); self.op_op_db()
    def op_fd_dc(self): self.op_illegal_1(); self.op_op_dc()
    def op_fd_dd(self): self.op_illegal_1(); self.op_op_fd()
    def op_fd_de(self): self.op_illegal_1(); self.op_op_de()
    def op_fd_df(self): self.op_illegal_1(); self.op_op_df()

    def op_fd_e0(self): self.op_illegal_1(); self.op_op_e0()
    def op_fd_e1(self): self.pop(self.m_iy)
    def op_fd_e2(self): self.op_illegal_1(); self.op_op_e2()
    def op_fd_e3(self): self.ex_sp(self.m_iy)
    def op_fd_e4(self): self.op_illegal_1(); self.op_op_e4()
    def op_fd_e5(self): self.push(self.m_iy)
    def op_fd_e6(self): self.op_illegal_1(); self.op_op_e6()
    def op_fd_e7(self): self.op_illegal_1(); self.op_op_e7()

    def op_fd_e8(self): self.op_illegal_1(); self.op_op_e8()
    def op_fd_e9(self): self.PC = self.IY
    def op_fd_ea(self): self.op_illegal_1(); self.op_op_ea()
    def op_fd_eb(self): self.op_illegal_1(); self.op_op_eb()
    def op_fd_ec(self): self.op_illegal_1(); self.op_op_ec()
    def op_fd_ed(self): self.op_illegal_1(); self.op_op_ed()
    def op_fd_ee(self): self.op_illegal_1(); self.op_op_ee()
    def op_fd_ef(self): self.op_illegal_1(); self.op_op_ef()

    def op_fd_f0(self): self.op_illegal_1(); self.op_op_f0()
    def op_fd_f1(self): self.op_illegal_1(); self.op_op_f1()
    def op_fd_f2(self): self.op_illegal_1(); self.op_op_f2()
    def op_fd_f3(self): self.op_illegal_1(); self.op_op_f3()
    def op_fd_f4(self): self.op_illegal_1(); self.op_op_f4()
    def op_fd_f5(self): self.op_illegal_1(); self.op_op_f5()
    def op_fd_f6(self): self.op_illegal_1(); self.op_op_f6()
    def op_fd_f7(self): self.op_illegal_1(); self.op_op_f7()

    def op_fd_f8(self): self.op_illegal_1(); self.op_op_f8()
    def op_fd_f9(self): self.nomreq_ir(2); self.SP = self.IY
    def op_fd_fa(self): self.op_illegal_1(); self.op_op_fa()
    def op_fd_fb(self): self.op_illegal_1(); self.op_op_fb()
    def op_fd_fc(self): self.op_illegal_1(); self.op_op_fc()
    def op_fd_fd(self): self.op_illegal_1(); self.op_op_fd()
    def op_fd_fe(self): self.op_illegal_1(); self.op_op_fe()
    def op_fd_ff(self): self.op_illegal_1(); self.op_op_ff()

    def op_illegal_2(self):
        self.log("Z80 ill. opcode $ed ${:02x} (${:04x})".format(
            self.m_opcodes.read(self.PC-1),
            self.PC-2))

    # special opcodes (ED prefix)
    def op_ed_00(self): self.op_illegal_2()
    def op_ed_01(self): self.op_illegal_2()
    def op_ed_02(self): self.op_illegal_2()
    def op_ed_03(self): self.op_illegal_2()
    def op_ed_04(self): self.op_illegal_2()
    def op_ed_05(self): self.op_illegal_2()
    def op_ed_06(self): self.op_illegal_2()
    def op_ed_07(self): self.op_illegal_2()

    def op_ed_08(self): self.op_illegal_2()
    def op_ed_09(self): self.op_illegal_2()
    def op_ed_0a(self): self.op_illegal_2()
    def op_ed_0b(self): self.op_illegal_2()
    def op_ed_0c(self): self.op_illegal_2()
    def op_ed_0d(self): self.op_illegal_2()
    def op_ed_0e(self): self.op_illegal_2()
    def op_ed_0f(self): self.op_illegal_2()

    def op_ed_10(self): self.op_illegal_2()
    def op_ed_11(self): self.op_illegal_2()
    def op_ed_12(self): self.op_illegal_2()
    def op_ed_13(self): self.op_illegal_2()
    def op_ed_14(self): self.op_illegal_2()
    def op_ed_15(self): self.op_illegal_2()
    def op_ed_16(self): self.op_illegal_2()
    def op_ed_17(self): self.op_illegal_2()

    def op_ed_18(self): self.op_illegal_2()
    def op_ed_19(self): self.op_illegal_2()
    def op_ed_1a(self): self.op_illegal_2()
    def op_ed_1b(self): self.op_illegal_2()
    def op_ed_1c(self): self.op_illegal_2()
    def op_ed_1d(self): self.op_illegal_2()
    def op_ed_1e(self): self.op_illegal_2()
    def op_ed_1f(self): self.op_illegal_2()

    def op_ed_20(self): self.op_illegal_2()
    def op_ed_21(self): self.op_illegal_2()
    def op_ed_22(self): self.op_illegal_2()
    def op_ed_23(self): self.op_illegal_2()
    def op_ed_24(self): self.op_illegal_2()
    def op_ed_25(self): self.op_illegal_2()
    def op_ed_26(self): self.op_illegal_2()
    def op_ed_27(self): self.op_illegal_2()

    def op_ed_28(self): self.op_illegal_2()
    def op_ed_29(self): self.op_illegal_2()
    def op_ed_2a(self): self.op_illegal_2()
    def op_ed_2b(self): self.op_illegal_2()
    def op_ed_2c(self): self.op_illegal_2()
    def op_ed_2d(self): self.op_illegal_2()
    def op_ed_2e(self): self.op_illegal_2()
    def op_ed_2f(self): self.op_illegal_2()

    def op_ed_30(self): self.op_illegal_2()
    def op_ed_31(self): self.op_illegal_2()
    def op_ed_32(self): self.op_illegal_2()
    def op_ed_33(self): self.op_illegal_2()
    def op_ed_34(self): self.op_illegal_2()
    def op_ed_35(self): self.op_illegal_2()
    def op_ed_36(self): self.op_illegal_2()
    def op_ed_37(self): self.op_illegal_2()

    def op_ed_38(self): self.op_illegal_2()
    def op_ed_39(self): self.op_illegal_2()
    def op_ed_3a(self): self.op_illegal_2()
    def op_ed_3b(self): self.op_illegal_2()
    def op_ed_3c(self): self.op_illegal_2()
    def op_ed_3d(self): self.op_illegal_2()
    def op_ed_3e(self): self.op_illegal_2()
    def op_ed_3f(self): self.op_illegal_2()

    def op_ed_40(self): self.B = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.B]
    def op_ed_41(self): self.out(self.BC, self.B)
    def op_ed_42(self): self.sbc_hl(self.m_bc)
    def op_ed_43(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_bc); self.WZ = self.m_ea + 1
    def op_ed_44(self): self.neg()
    def op_ed_45(self): self.retn()
    def op_ed_46(self): self.m_im = 0
    def op_ed_47(self): self.ld_i_a()

    def op_ed_48(self): self.C = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.C]
    def op_ed_49(self): self.out(self.BC, self.C)
    def op_ed_4a(self): self.adc_hl(self.m_bc)
    def op_ed_4b(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_bc); self.WZ = self.m_ea + 1
    def op_ed_4c(self): self.neg()
    def op_ed_4d(self): self.reti()
    def op_ed_4e(self): self.m_im = 0
    def op_ed_4f(self): self.ld_r_a()

    def op_ed_50(self): self.D = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.D]
    def op_ed_51(self): self.out(self.BC, self.D)
    def op_ed_52(self): self.sbc_hl(self.m_de)
    def op_ed_53(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_de); self.WZ = self.m_ea + 1
    def op_ed_54(self): self.neg()
    def op_ed_55(self): self.retn()
    def op_ed_56(self): self.m_im = 1
    def op_ed_57(self): self.ld_a_i()

    def op_ed_58(self): self.E = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.E]
    def op_ed_59(self): self.out(self.BC, self.E)
    def op_ed_5a(self): self.adc_hl(self.m_de)
    def op_ed_5b(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_de); self.WZ = self.m_ea + 1
    def op_ed_5c(self): self.neg()
    def op_ed_5d(self): self.reti()
    def op_ed_5e(self): self.m_im = 2
    def op_ed_5f(self): self.ld_a_r()

    def op_ed_60(self): self.H = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.H]
    def op_ed_61(self): self.out(self.BC, self.H)
    def op_ed_62(self): self.sbc_hl(self.m_hl)
    def op_ed_63(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_hl); self.WZ = self.m_ea + 1
    def op_ed_64(self): self.neg()
    def op_ed_65(self): self.retn()
    def op_ed_66(self): self.m_im = 0
    def op_ed_67(self): self.rrd()

    def op_ed_68(self): self.L = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.L]
    def op_ed_69(self): self.out(self.BC, self.L)
    def op_ed_6a(self): self.adc_hl(self.m_hl)
    def op_ed_6b(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_hl); self.WZ = self.m_ea + 1
    def op_ed_6c(self): self.neg()
    def op_ed_6d(self): self.reti()
    def op_ed_6e(self): self.m_im = 0
    def op_ed_6f(self): self.rld()

    def op_ed_70(self): res = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[res]
    def op_ed_71(self): self.out(self.BC, 0)
    def op_ed_72(self): self.sbc_hl(self.m_sp)
    def op_ed_73(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_sp); self.WZ = self.m_ea + 1
    def op_ed_74(self): self.neg()
    def op_ed_75(self): self.retn()
    def op_ed_76(self): self.m_im = 1
    def op_ed_77(self): self.op_illegal_2()

    def op_ed_78(self): self.A = self.inp(self.BC); self.F = (self.F & Z80.CF) | Z80.SZP[self.A]; self.WZ = self.BC + 1
    def op_ed_79(self): self.out(self.BC, self.A); self.WZ = self.BC + 1
    def op_ed_7a(self): self.adc_hl(self.m_sp)
    def op_ed_7b(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_sp); self.WZ = self.m_ea + 1
    def op_ed_7c(self): self.neg()
    def op_ed_7d(self): self.reti()
    def op_ed_7e(self): self.m_im = 2
    def op_ed_7f(self): self.op_illegal_2()

    def op_ed_80(self): self.op_illegal_2()
    def op_ed_81(self): self.op_illegal_2()
    def op_ed_82(self): self.op_illegal_2()
    def op_ed_83(self): self.op_illegal_2()
    def op_ed_84(self): self.op_illegal_2()
    def op_ed_85(self): self.op_illegal_2()
    def op_ed_86(self): self.op_illegal_2()
    def op_ed_87(self): self.op_illegal_2()

    def op_ed_88(self): self.op_illegal_2()
    def op_ed_89(self): self.op_illegal_2()
    def op_ed_8a(self): self.op_illegal_2()
    def op_ed_8b(self): self.op_illegal_2()
    def op_ed_8c(self): self.op_illegal_2()
    def op_ed_8d(self): self.op_illegal_2()
    def op_ed_8e(self): self.op_illegal_2()
    def op_ed_8f(self): self.op_illegal_2()

    def op_ed_90(self): self.op_illegal_2()
    def op_ed_91(self): self.op_illegal_2()
    def op_ed_92(self): self.op_illegal_2()
    def op_ed_93(self): self.op_illegal_2()
    def op_ed_94(self): self.op_illegal_2()
    def op_ed_95(self): self.op_illegal_2()
    def op_ed_96(self): self.op_illegal_2()
    def op_ed_97(self): self.op_illegal_2()

    def op_ed_98(self): self.op_illegal_2()
    def op_ed_99(self): self.op_illegal_2()
    def op_ed_9a(self): self.op_illegal_2()
    def op_ed_9b(self): self.op_illegal_2()
    def op_ed_9c(self): self.op_illegal_2()
    def op_ed_9d(self): self.op_illegal_2()
    def op_ed_9e(self): self.op_illegal_2()
    def op_ed_9f(self): self.op_illegal_2()

    def op_ed_a0(self): self.ldi()
    def op_ed_a1(self): self.cpi()
    def op_ed_a2(self): self.ini()
    def op_ed_a3(self): self.outi()
    def op_ed_a4(self): self.op_illegal_2()
    def op_ed_a5(self): self.op_illegal_2()
    def op_ed_a6(self): self.op_illegal_2()
    def op_ed_a7(self): self.op_illegal_2()

    def op_ed_a8(self): self.ldd()
    def op_ed_a9(self): self.cpd()
    def op_ed_aa(self): self.ind()
    def op_ed_ab(self): self.outd()
    def op_ed_ac(self): self.op_illegal_2()
    def op_ed_ad(self): self.op_illegal_2()
    def op_ed_ae(self): self.op_illegal_2()
    def op_ed_af(self): self.op_illegal_2()

    def op_ed_b0(self): self.ldir()
    def op_ed_b1(self): self.cpir()
    def op_ed_b2(self): self.inir()
    def op_ed_b3(self): self.otir()
    def op_ed_b4(self): self.op_illegal_2()
    def op_ed_b5(self): self.op_illegal_2()
    def op_ed_b6(self): self.op_illegal_2()
    def op_ed_b7(self): self.op_illegal_2()

    def op_ed_b8(self): self.lddr()
    def op_ed_b9(self): self.cpdr()
    def op_ed_ba(self): self.indr()
    def op_ed_bb(self): self.otdr()
    def op_ed_bc(self): self.op_illegal_2()
    def op_ed_bd(self): self.op_illegal_2()
    def op_ed_be(self): self.op_illegal_2()
    def op_ed_bf(self): self.op_illegal_2()

    def op_ed_c0(self): self.op_illegal_2()
    def op_ed_c1(self): self.op_illegal_2()
    def op_ed_c2(self): self.op_illegal_2()
    def op_ed_c3(self): self.op_illegal_2()
    def op_ed_c4(self): self.op_illegal_2()
    def op_ed_c5(self): self.op_illegal_2()
    def op_ed_c6(self): self.op_illegal_2()
    def op_ed_c7(self): self.op_illegal_2()

    def op_ed_c8(self): self.op_illegal_2()
    def op_ed_c9(self): self.op_illegal_2()
    def op_ed_ca(self): self.op_illegal_2()
    def op_ed_cb(self): self.op_illegal_2()
    def op_ed_cc(self): self.op_illegal_2()
    def op_ed_cd(self): self.op_illegal_2()
    def op_ed_ce(self): self.op_illegal_2()
    def op_ed_cf(self): self.op_illegal_2()

    def op_ed_d0(self): self.op_illegal_2()
    def op_ed_d1(self): self.op_illegal_2()
    def op_ed_d2(self): self.op_illegal_2()
    def op_ed_d3(self): self.op_illegal_2()
    def op_ed_d4(self): self.op_illegal_2()
    def op_ed_d5(self): self.op_illegal_2()
    def op_ed_d6(self): self.op_illegal_2()
    def op_ed_d7(self): self.op_illegal_2()

    def op_ed_d8(self): self.op_illegal_2()
    def op_ed_d9(self): self.op_illegal_2()
    def op_ed_da(self): self.op_illegal_2()
    def op_ed_db(self): self.op_illegal_2()
    def op_ed_dc(self): self.op_illegal_2()
    def op_ed_dd(self): self.op_illegal_2()
    def op_ed_de(self): self.op_illegal_2()
    def op_ed_df(self): self.op_illegal_2()

    def op_ed_e0(self): self.op_illegal_2()
    def op_ed_e1(self): self.op_illegal_2()
    def op_ed_e2(self): self.op_illegal_2()
    def op_ed_e3(self): self.op_illegal_2()
    def op_ed_e4(self): self.op_illegal_2()
    def op_ed_e5(self): self.op_illegal_2()
    def op_ed_e6(self): self.op_illegal_2()
    def op_ed_e7(self): self.op_illegal_2()

    def op_ed_e8(self): self.op_illegal_2()
    def op_ed_e9(self): self.op_illegal_2()
    def op_ed_ea(self): self.op_illegal_2()
    def op_ed_eb(self): self.op_illegal_2()
    def op_ed_ec(self): self.op_illegal_2()
    def op_ed_ed(self): self.op_illegal_2()
    def op_ed_ee(self): self.op_illegal_2()
    def op_ed_ef(self): self.op_illegal_2()

    def op_ed_f0(self): self.op_illegal_2()
    def op_ed_f1(self): self.op_illegal_2()
    def op_ed_f2(self): self.op_illegal_2()
    def op_ed_f3(self): self.op_illegal_2()
    def op_ed_f4(self): self.op_illegal_2()
    def op_ed_f5(self): self.op_illegal_2()
    def op_ed_f6(self): self.op_illegal_2()
    def op_ed_f7(self): self.op_illegal_2()

    def op_ed_f8(self): self.op_illegal_2()
    def op_ed_f9(self): self.op_illegal_2()
    def op_ed_fa(self): self.op_illegal_2()
    def op_ed_fb(self): self.op_illegal_2()
    def op_ed_fc(self): self.op_illegal_2()
    def op_ed_fd(self): self.op_illegal_2()
    def op_ed_fe(self): self.op_illegal_2()
    def op_ed_ff(self): self.op_illegal_2()

    # main opcodes
    def op_op_00(self): pass
    def op_op_01(self): self.BC = self.arg16()
    def op_op_02(self): self.wm(self.BC, self.A); self.WZ_L = (self.BC + 1) & 0xff; self.WZ_H = self.A
    def op_op_03(self): self.nomreq_ir(2); self.BC += 1
    def op_op_04(self): self.B = self.inc(self.B)
    def op_op_05(self): self.B = self.dec(self.B)
    def op_op_06(self): self.B = self.arg()
    def op_op_07(self): self.rlca()

    def op_op_08(self): self.ex_af()
    def op_op_09(self): self.add16(self.m_hl, self.m_bc)
    def op_op_0a(self): self.A = self.rm(self.BC); self.WZ = self.BC + 1
    def op_op_0b(self): self.nomreq_ir(2); self.BC -= 1
    def op_op_0c(self): self.C = self.inc(self.C)
    def op_op_0d(self): self.C = self.dec(self.C)
    def op_op_0e(self): self.C = self.arg()
    def op_op_0f(self): self.rrca()

    def op_op_10(self): self.nomreq_ir(1); self.B -= 1; self.jr_cond(self.B, 0x10)
    def op_op_11(self): self.DE = self.arg16()
    def op_op_12(self): self.wm(self.DE, self.A); self.WZ_L = (self.DE + 1) & 0xff; self.WZ_H = self.A
    def op_op_13(self): self.nomreq_ir(2); self.DE += 1
    def op_op_14(self): self.D = self.inc(self.D)
    def op_op_15(self): self.D = self.dec(self.D)
    def op_op_16(self): self.D = self.arg()
    def op_op_17(self): self.rla()

    def op_op_18(self): self.jr()
    def op_op_19(self): self.add16(self.m_hl, self.m_de)
    def op_op_1a(self): self.A = self.rm(self.DE); self.WZ = self.DE + 1
    def op_op_1b(self): self.nomreq_ir(2); self.DE -= 1
    def op_op_1c(self): self.E = self.inc(self.E)
    def op_op_1d(self): self.E = self.dec(self.E)
    def op_op_1e(self): self.E = self.arg()
    def op_op_1f(self): self.rra()

    def op_op_20(self): self.jr_cond(not self.F & Z80.ZF, 0x20)
    def op_op_21(self): self.HL = self.arg16()
    def op_op_22(self): self.m_ea = self.arg16(); self.wm16(self.m_ea, self.m_hl); self.WZ = self.m_ea + 1
    def op_op_23(self): self.nomreq_ir(2); self.HL += 1
    def op_op_24(self): self.H = self.inc(self.H)
    def op_op_25(self): self.H = self.dec(self.H)
    def op_op_26(self): self.H = self.arg()
    def op_op_27(self): self.daa()

    def op_op_28(self): self.jr_cond(self.F & Z80.ZF, 0x28)
    def op_op_29(self): self.add16(self.m_hl, self.m_hl)
    def op_op_2a(self): self.m_ea = self.arg16(); self.rm16(self.m_ea, self.m_hl); self.WZ = self.m_ea + 1
    def op_op_2b(self): self.nomreq_ir(2); self.HL -= 1
    def op_op_2c(self): self.L = self.inc(self.L)
    def op_op_2d(self): self.L = self.dec(self.L)
    def op_op_2e(self): self.L = self.arg()
    def op_op_2f(self): self.A ^= 0xff; self.F = (self.F & (Z80.SF | Z80.ZF | Z80.PF | Z80.CF)) | Z80.HF | Z80.NF | (self.A & (Z80.YF | Z80.XF))

    def op_op_30(self): self.jr_cond(not self.F & Z80.CF, 0x30)
    def op_op_31(self): self.SP = self.arg16()
    def op_op_32(self): self.m_ea = self.arg16(); self.wm(self.m_ea, self.A); self.WZ_L = (self.m_ea + 1) & 0xff; self.WZ_H = self.A
    def op_op_33(self): self.nomreq_ir(2); self.SP += 1
    def op_op_34(self): self.wm(self.HL, self.inc(self.rm_reg(self.HL)))
    def op_op_35(self): self.wm(self.HL, self.dec(self.rm_reg(self.HL)))
    def op_op_36(self): self.wm(self.HL, self.arg())
    def op_op_37(self): self.F = (self.F & (Z80.SF | Z80.ZF | Z80.YF | Z80.XF | Z80.PF)) | Z80.CF | (self.A & (Z80.YF | Z80.XF))

    def op_op_38(self): self.jr_cond(self.F & Z80.CF, 0x38)
    def op_op_39(self): self.add16(self.m_hl, self.m_sp)
    def op_op_3a(self): self.m_ea = self.arg16(); self.A = self.rm(self.m_ea); self.WZ = self.m_ea + 1
    def op_op_3b(self): self.nomreq_ir(2); self.SP -= 1
    def op_op_3c(self): self.A = self.inc(self.A)
    def op_op_3d(self): self.A = self.dec(self.A)
    def op_op_3e(self): self.A = self.arg()
    def op_op_3f(self): self.F = ((self.F & (Z80.SF | Z80.ZF | Z80.YF | Z80.XF | Z80.PF | Z80.CF)) | ((self.F & Z80.CF) << 4) | (self.A & (Z80.YF | Z80.XF))) ^ Z80.CF

    def op_op_40(self): pass
    def op_op_41(self): self.B = self.C
    def op_op_42(self): self.B = self.D
    def op_op_43(self): self.B = self.E
    def op_op_44(self): self.B = self.H
    def op_op_45(self): self.B = self.L
    def op_op_46(self): self.B = self.rm(self.HL)
    def op_op_47(self): self.B = self.A

    def op_op_48(self): self.C = self.B
    def op_op_49(self): pass
    def op_op_4a(self): self.C = self.D
    def op_op_4b(self): self.C = self.E
    def op_op_4c(self): self.C = self.H
    def op_op_4d(self): self.C = self.L
    def op_op_4e(self): self.C = self.rm(self.HL)
    def op_op_4f(self): self.C = self.A

    def op_op_50(self): self.D = self.B
    def op_op_51(self): self.D = self.C
    def op_op_52(self): pass
    def op_op_53(self): self.D = self.E
    def op_op_54(self): self.D = self.H
    def op_op_55(self): self.D = self.L
    def op_op_56(self): self.D = self.rm(self.HL)
    def op_op_57(self): self.D = self.A

    def op_op_58(self): self.E = self.B
    def op_op_59(self): self.E = self.C
    def op_op_5a(self): self.E = self.D
    def op_op_5b(self): pass
    def op_op_5c(self): self.E = self.H
    def op_op_5d(self): self.E = self.L
    def op_op_5e(self): self.E = self.rm(self.HL)
    def op_op_5f(self): self.E = self.A

    def op_op_60(self): self.H = self.B
    def op_op_61(self): self.H = self.C
    def op_op_62(self): self.H = self.D
    def op_op_63(self): self.H = self.E
    def op_op_64(self): pass
    def op_op_65(self): self.H = self.L
    def op_op_66(self): self.H = self.rm(self.HL)
    def op_op_67(self): self.H = self.A

    def op_op_68(self): self.L = self.B
    def op_op_69(self): self.L = self.C
    def op_op_6a(self): self.L = self.D
    def op_op_6b(self): self.L = self.E
    def op_op_6c(self): self.L = self.H
    def op_op_6d(self): pass
    def op_op_6e(self): self.L = self.rm(self.HL)
    def op_op_6f(self): self.L = self.A

    def op_op_70(self): self.wm(self.HL, self.B)
    def op_op_71(self): self.wm(self.HL, self.C)
    def op_op_72(self): self.wm(self.HL, self.D)
    def op_op_73(self): self.wm(self.HL, self.E)
    def op_op_74(self): self.wm(self.HL, self.H)
    def op_op_75(self): self.wm(self.HL, self.L)
    def op_op_76(self): self.halt()
    def op_op_77(self): self.wm(self.HL, self.A)

    def op_op_78(self): self.A = self.B
    def op_op_79(self): self.A = self.C
    def op_op_7a(self): self.A = self.D
    def op_op_7b(self): self.A = self.E
    def op_op_7c(self): self.A = self.H
    def op_op_7d(self): self.A = self.L
    def op_op_7e(self): self.A = self.rm(self.HL)
    def op_op_7f(self): pass

    def op_op_80(self): self.add_a(self.B)
    def op_op_81(self): self.add_a(self.C)
    def op_op_82(self): self.add_a(self.D)
    def op_op_83(self): self.add_a(self.E)
    def op_op_84(self): self.add_a(self.H)
    def op_op_85(self): self.add_a(self.L)
    def op_op_86(self): self.add_a(self.rm(self.HL))
    def op_op_87(self): self.add_a(self.A)

    def op_op_88(self): self.adc_a(self.B)
    def op_op_89(self): self.adc_a(self.C)
    def op_op_8a(self): self.adc_a(self.D)
    def op_op_8b(self): self.adc_a(self.E)
    def op_op_8c(self): self.adc_a(self.H)
    def op_op_8d(self): self.adc_a(self.L)
    def op_op_8e(self): self.adc_a(self.rm(self.HL))
    def op_op_8f(self): self.adc_a(self.A)

    def op_op_90(self): self.sub(self.B)
    def op_op_91(self): self.sub(self.C)
    def op_op_92(self): self.sub(self.D)
    def op_op_93(self): self.sub(self.E)
    def op_op_94(self): self.sub(self.H)
    def op_op_95(self): self.sub(self.L)
    def op_op_96(self): self.sub(self.rm(self.HL))
    def op_op_97(self): self.sub(self.A)

    def op_op_98(self): self.sbc_a(self.B)
    def op_op_99(self): self.sbc_a(self.C)
    def op_op_9a(self): self.sbc_a(self.D)
    def op_op_9b(self): self.sbc_a(self.E)
    def op_op_9c(self): self.sbc_a(self.H)
    def op_op_9d(self): self.sbc_a(self.L)
    def op_op_9e(self): self.sbc_a(self.rm(self.HL))
    def op_op_9f(self): self.sbc_a(self.A)

    def op_op_a0(self): self.and_a(self.B)
    def op_op_a1(self): self.and_a(self.C)
    def op_op_a2(self): self.and_a(self.D)
    def op_op_a3(self): self.and_a(self.E)
    def op_op_a4(self): self.and_a(self.H)
    def op_op_a5(self): self.and_a(self.L)
    def op_op_a6(self): self.and_a(self.rm(self.HL))
    def op_op_a7(self): self.and_a(self.A)

    def op_op_a8(self): self.xor_a(self.B)
    def op_op_a9(self): self.xor_a(self.C)
    def op_op_aa(self): self.xor_a(self.D)
    def op_op_ab(self): self.xor_a(self.E)
    def op_op_ac(self): self.xor_a(self.H)
    def op_op_ad(self): self.xor_a(self.L)
    def op_op_ae(self): self.xor_a(self.rm(self.HL))
    def op_op_af(self): self.xor_a(self.A)

    def op_op_b0(self): self.or_a(self.B)
    def op_op_b1(self): self.or_a(self.C)
    def op_op_b2(self): self.or_a(self.D)
    def op_op_b3(self): self.or_a(self.E)
    def op_op_b4(self): self.or_a(self.H)
    def op_op_b5(self): self.or_a(self.L)
    def op_op_b6(self): self.or_a(self.rm(self.HL))
    def op_op_b7(self): self.or_a(self.A)

    def op_op_b8(self): self.cp(self.B)
    def op_op_b9(self): self.cp(self.C)
    def op_op_ba(self): self.cp(self.D)
    def op_op_bb(self): self.cp(self.E)
    def op_op_bc(self): self.cp(self.H)
    def op_op_bd(self): self.cp(self.L)
    def op_op_be(self): self.cp(self.rm(self.HL))
    def op_op_bf(self): self.cp(self.A)

    def op_op_c0(self): self.ret_cond(not (self.F & Z80.ZF), 0xc0)
    def op_op_c1(self): self.pop(self.m_bc)
    def op_op_c2(self): self.jp_cond(not (self.F & Z80.ZF))
    def op_op_c3(self): self.jp()
    def op_op_c4(self): self.call_cond(not (self.F & Z80.ZF), 0xc4)
    def op_op_c5(self): self.push(self.m_bc)
    def op_op_c6(self): self.add_a(self.arg())
    def op_op_c7(self): self.rst(0x00)

    def op_op_c8(self): self.ret_cond(self.F & Z80.ZF, 0xc8)
    def op_op_c9(self): self.pop(self.m_pc); self.WZ = self.PC
    def op_op_ca(self): self.jp_cond(self.F & Z80.ZF)
    def op_op_cb(self): self.EXEC(Z80.cc_cb, self.op_cb, self.rop())
    def op_op_cc(self): self.call_cond(self.F & Z80.ZF, 0xcc)
    def op_op_cd(self): self.call()
    def op_op_ce(self): self.adc_a(self.arg())
    def op_op_cf(self): self.rst(0x08)

    def op_op_d0(self): self.ret_cond(not (self.F & Z80.CF), 0xd0)
    def op_op_d1(self): self.pop(self.m_de)
    def op_op_d2(self): self.jp_cond(not (self.F & Z80.CF))
    def op_op_d3(self): n = self.arg() | (self.A << 8); self.out(n, self.A); self.WZ_L = ((n & 0xff) + 1) & 0xff; self.WZ_H = self.A
    def op_op_d4(self): self.call_cond(not (self.F & Z80.CF), 0xd4)
    def op_op_d5(self): self.push(self.m_de)
    def op_op_d6(self): self.sub(self.arg())
    def op_op_d7(self): self.rst(0x10)

    def op_op_d8(self): self.ret_cond(self.F & Z80.CF, 0xd8)
    def op_op_d9(self): self.exx()
    def op_op_da(self): self.jp_cond(self.F & Z80.CF)
    def op_op_db(self): n = self.arg() | (self.A << 8); self.A = self.inp(n); self.WZ = n + 1
    def op_op_dc(self): self.call_cond(self.F & Z80.CF, 0xdc)
    def op_op_dd(self): self.EXEC(Z80.cc_dd, self.op_dd, self.rop())
    def op_op_de(self): self.sbc_a(self.arg())
    def op_op_df(self): self.rst(0x18)

    def op_op_e0(self): self.ret_cond(not (self.F & Z80.PF), 0xe0)
    def op_op_e1(self): self.pop(self.m_hl)
    def op_op_e2(self): self.jp_cond(not (self.F & Z80.PF))
    def op_op_e3(self): self.ex_sp(self.m_hl)
    def op_op_e4(self): self.call_cond(not (self.F & Z80.PF), 0xe4)
    def op_op_e5(self): self.push(self.m_hl)
    def op_op_e6(self): self.and_a(self.arg())
    def op_op_e7(self): self.rst(0x20)

    def op_op_e8(self): self.ret_cond(self.F & Z80.PF, 0xe8)
    def op_op_e9(self): self.PC = self.HL
    def op_op_ea(self): self.jp_cond(self.F & Z80.PF)
    def op_op_eb(self): self.ex_de_hl()
    def op_op_ec(self): self.call_cond(self.F & Z80.PF, 0xec)
    def op_op_ed(self): self.EXEC(Z80.cc_ed, self.op_ed, self.rop())
    def op_op_ee(self): self.xor_a(self.arg())
    def op_op_ef(self): self.rst(0x28)

    def op_op_f0(self): self.ret_cond(not (self.F & Z80.SF), 0xf0)
    def op_op_f1(self): self.pop(self.m_af)
    def op_op_f2(self): self.jp_cond(not (self.F & Z80.SF))
    def op_op_f3(self): self.m_iff1 = self.m_iff2 = 0
    def op_op_f4(self): self.call_cond(not (self.F & Z80.SF), 0xf4)
    def op_op_f5(self): self.push(self.m_af)
    def op_op_f6(self): self.or_a(self.arg())
    def op_op_f7(self): self.rst(0x30)

    def op_op_f8(self): self.ret_cond(self.F & Z80.SF, 0xf8)
    def op_op_f9(self): self.nomreq_ir(2); self.SP = self.HL
    def op_op_fa(self): self.jp_cond(self.F & Z80.SF)
    def op_op_fb(self): self.ei()
    def op_op_fc(self): self.call_cond(self.F & Z80.SF, 0xfc)
    def op_op_fd(self): self.EXEC(Z80.cc_fd, self.op_fd, self.rop())
    def op_op_fe(self): self.cp(self.arg())
    def op_op_ff(self): self.rst(0x38)

    def initialize_tables(self):
        if not Z80.tables_initialized:
            add = Z80.SZHVC_add
            sub = Z80.SZHVC_sub

            for oldval in range(256):
                for newval in range(256):
                    idx = oldval * 256 + newval
                    idxc = 256 * 256 + oldval * 256 + newval

                    # add or adc w/o carry set
                    val = newval - oldval
                    f = (Z80.SF if newval & 0x80 else 0) if newval else Z80.ZF
                    f |= newval & (Z80.YF | Z80.XF) # undocumented flag bits 5+3
                    if (newval & 0x0f) < (oldval & 0x0f): f |= Z80.HF
                    if newval < oldval: f |= Z80.CF
                    if (val^oldval^0x80) & (val^newval) & 0x80: f |= Z80.VF
                    add[idx] = f

                    # add or adc with carry set
                    val = newval - oldval - 1
                    f = (Z80.SF if newval & 0x80 else 0) if newval else Z80.ZF
                    f |= newval & (Z80.YF | Z80.XF) # undocumented flag bits 5+3
                    if (newval & 0x0f) <= (oldval & 0x0f): f |= Z80.HF
                    if newval <= oldval: f |= Z80.CF
                    if (val^oldval^0x80) & (val^newval) & 0x80: f |= Z80.VF
                    add[idxc] = f

                    # cp, sub or sbc w/o carry set
                    val = oldval - newval;
                    f = Z80.NF | ((Z80.SF if newval & 0x80 else 0) if newval else Z80.ZF)
                    f |= newval & (Z80.YF | Z80.XF) # undocumented flag bits 5+3
                    if (newval & 0x0f) > (oldval & 0x0f): f |= Z80.HF
                    if newval > oldval: f |= Z80.CF
                    if (val^oldval) & (oldval^newval) & 0x80: f |= Z80.VF
                    sub[idx] = f

                    # sbc with carry set
                    val = oldval - newval - 1
                    f = Z80.NF | ((Z80.SF if newval & 0x80 else 0) if newval else Z80.ZF)
                    f |= newval & (Z80.YF | Z80.XF) # undocumented flag bits 5+3
                    if (newval & 0x0f) >= (oldval & 0x0f): f |= Z80.HF
                    if newval >= oldval: f |= Z80.CF
                    if (val^oldval) & (oldval^newval) & 0x80: f |= Z80.VF
                    sub[idxc] = f

            for i in range(256):
                p = 0
                if i & 0x01: p += 1
                if i & 0x02: p += 1
                if i & 0x04: p += 1
                if i & 0x08: p += 1
                if i & 0x10: p += 1
                if i & 0x20: p += 1
                if i & 0x40: p += 1
                if i & 0x80: p += 1
                Z80.SZ[i] = (i & Z80.SF) if i else Z80.ZF
                Z80.SZ[i] |= (i & (Z80.YF | Z80.XF))        # undocumented flag bits 5+3
                Z80.SZ_BIT[i] = (i & Z80.SF) if i else (Z80.ZF | Z80.PF)
                Z80.SZ_BIT[i] |= (i & (Z80.YF | Z80.XF))    # undocumented flag bits 5+3
                Z80.SZP[i] = Z80.SZ[i] | (0 if (p & 1) else Z80.PF)
                Z80.SZHV_inc[i] = Z80.SZ[i]
                if i == 0x80: Z80.SZHV_inc[i] |= Z80.VF
                if (i & 0x0f) == 0x00: Z80.SZHV_inc[i] |= Z80.HF
                Z80.SZHV_dec[i] = Z80.SZ[i] | Z80.NF
                if i == 0x7f: Z80.SZHV_dec[i] |= Z80.VF
                if (i & 0x0f) == 0x0f: Z80.SZHV_dec[i] |= Z80.HF

            for i in range(0x100):
                value = -(i & 0b10000000) | (i & 0b01111111)
                Z80.S8[i] = value

            for i in range(0x10000):
                value = -(value & 0b1000000000000000) | (value & 0b0111111111111111)
                Z80.S16[i] = value

            Z80.tables_initialized = True

        self.op_cb = [
            self.op_cb_00, self.op_cb_01, self.op_cb_02, self.op_cb_03,
            self.op_cb_04, self.op_cb_05, self.op_cb_06, self.op_cb_07,
            self.op_cb_08, self.op_cb_09, self.op_cb_0a, self.op_cb_0b,
            self.op_cb_0c, self.op_cb_0d, self.op_cb_0e, self.op_cb_0f,
            self.op_cb_10, self.op_cb_11, self.op_cb_12, self.op_cb_13,
            self.op_cb_14, self.op_cb_15, self.op_cb_16, self.op_cb_17,
            self.op_cb_18, self.op_cb_19, self.op_cb_1a, self.op_cb_1b,
            self.op_cb_1c, self.op_cb_1d, self.op_cb_1e, self.op_cb_1f,
            self.op_cb_20, self.op_cb_21, self.op_cb_22, self.op_cb_23,
            self.op_cb_24, self.op_cb_25, self.op_cb_26, self.op_cb_27,
            self.op_cb_28, self.op_cb_29, self.op_cb_2a, self.op_cb_2b,
            self.op_cb_2c, self.op_cb_2d, self.op_cb_2e, self.op_cb_2f,
            self.op_cb_30, self.op_cb_31, self.op_cb_32, self.op_cb_33,
            self.op_cb_34, self.op_cb_35, self.op_cb_36, self.op_cb_37,
            self.op_cb_38, self.op_cb_39, self.op_cb_3a, self.op_cb_3b,
            self.op_cb_3c, self.op_cb_3d, self.op_cb_3e, self.op_cb_3f,
            self.op_cb_40, self.op_cb_41, self.op_cb_42, self.op_cb_43,
            self.op_cb_44, self.op_cb_45, self.op_cb_46, self.op_cb_47,
            self.op_cb_48, self.op_cb_49, self.op_cb_4a, self.op_cb_4b,
            self.op_cb_4c, self.op_cb_4d, self.op_cb_4e, self.op_cb_4f,
            self.op_cb_50, self.op_cb_51, self.op_cb_52, self.op_cb_53,
            self.op_cb_54, self.op_cb_55, self.op_cb_56, self.op_cb_57,
            self.op_cb_58, self.op_cb_59, self.op_cb_5a, self.op_cb_5b,
            self.op_cb_5c, self.op_cb_5d, self.op_cb_5e, self.op_cb_5f,
            self.op_cb_60, self.op_cb_61, self.op_cb_62, self.op_cb_63,
            self.op_cb_64, self.op_cb_65, self.op_cb_66, self.op_cb_67,
            self.op_cb_68, self.op_cb_69, self.op_cb_6a, self.op_cb_6b,
            self.op_cb_6c, self.op_cb_6d, self.op_cb_6e, self.op_cb_6f,
            self.op_cb_70, self.op_cb_71, self.op_cb_72, self.op_cb_73,
            self.op_cb_74, self.op_cb_75, self.op_cb_76, self.op_cb_77,
            self.op_cb_78, self.op_cb_79, self.op_cb_7a, self.op_cb_7b,
            self.op_cb_7c, self.op_cb_7d, self.op_cb_7e, self.op_cb_7f,
            self.op_cb_80, self.op_cb_81, self.op_cb_82, self.op_cb_83,
            self.op_cb_84, self.op_cb_85, self.op_cb_86, self.op_cb_87,
            self.op_cb_88, self.op_cb_89, self.op_cb_8a, self.op_cb_8b,
            self.op_cb_8c, self.op_cb_8d, self.op_cb_8e, self.op_cb_8f,
            self.op_cb_90, self.op_cb_91, self.op_cb_92, self.op_cb_93,
            self.op_cb_94, self.op_cb_95, self.op_cb_96, self.op_cb_97,
            self.op_cb_98, self.op_cb_99, self.op_cb_9a, self.op_cb_9b,
            self.op_cb_9c, self.op_cb_9d, self.op_cb_9e, self.op_cb_9f,
            self.op_cb_a0, self.op_cb_a1, self.op_cb_a2, self.op_cb_a3,
            self.op_cb_a4, self.op_cb_a5, self.op_cb_a6, self.op_cb_a7,
            self.op_cb_a8, self.op_cb_a9, self.op_cb_aa, self.op_cb_ab,
            self.op_cb_ac, self.op_cb_ad, self.op_cb_ae, self.op_cb_af,
            self.op_cb_b0, self.op_cb_b1, self.op_cb_b2, self.op_cb_b3,
            self.op_cb_b4, self.op_cb_b5, self.op_cb_b6, self.op_cb_b7,
            self.op_cb_b8, self.op_cb_b9, self.op_cb_ba, self.op_cb_bb,
            self.op_cb_bc, self.op_cb_bd, self.op_cb_be, self.op_cb_bf,
            self.op_cb_c0, self.op_cb_c1, self.op_cb_c2, self.op_cb_c3,
            self.op_cb_c4, self.op_cb_c5, self.op_cb_c6, self.op_cb_c7,
            self.op_cb_c8, self.op_cb_c9, self.op_cb_ca, self.op_cb_cb,
            self.op_cb_cc, self.op_cb_cd, self.op_cb_ce, self.op_cb_cf,
            self.op_cb_d0, self.op_cb_d1, self.op_cb_d2, self.op_cb_d3,
            self.op_cb_d4, self.op_cb_d5, self.op_cb_d6, self.op_cb_d7,
            self.op_cb_d8, self.op_cb_d9, self.op_cb_da, self.op_cb_db,
            self.op_cb_dc, self.op_cb_dd, self.op_cb_de, self.op_cb_df,
            self.op_cb_e0, self.op_cb_e1, self.op_cb_e2, self.op_cb_e3,
            self.op_cb_e4, self.op_cb_e5, self.op_cb_e6, self.op_cb_e7,
            self.op_cb_e8, self.op_cb_e9, self.op_cb_ea, self.op_cb_eb,
            self.op_cb_ec, self.op_cb_ed, self.op_cb_ee, self.op_cb_ef,
            self.op_cb_f0, self.op_cb_f1, self.op_cb_f2, self.op_cb_f3,
            self.op_cb_f4, self.op_cb_f5, self.op_cb_f6, self.op_cb_f7,
            self.op_cb_f8, self.op_cb_f9, self.op_cb_fa, self.op_cb_fb,
            self.op_cb_fc, self.op_cb_fd, self.op_cb_fe, self.op_cb_ff,
        ]
        self.op_xycb = [
            self.op_xycb_00, self.op_xycb_01, self.op_xycb_02, self.op_xycb_03,
            self.op_xycb_04, self.op_xycb_05, self.op_xycb_06, self.op_xycb_07,
            self.op_xycb_08, self.op_xycb_09, self.op_xycb_0a, self.op_xycb_0b,
            self.op_xycb_0c, self.op_xycb_0d, self.op_xycb_0e, self.op_xycb_0f,
            self.op_xycb_10, self.op_xycb_11, self.op_xycb_12, self.op_xycb_13,
            self.op_xycb_14, self.op_xycb_15, self.op_xycb_16, self.op_xycb_17,
            self.op_xycb_18, self.op_xycb_19, self.op_xycb_1a, self.op_xycb_1b,
            self.op_xycb_1c, self.op_xycb_1d, self.op_xycb_1e, self.op_xycb_1f,
            self.op_xycb_20, self.op_xycb_21, self.op_xycb_22, self.op_xycb_23,
            self.op_xycb_24, self.op_xycb_25, self.op_xycb_26, self.op_xycb_27,
            self.op_xycb_28, self.op_xycb_29, self.op_xycb_2a, self.op_xycb_2b,
            self.op_xycb_2c, self.op_xycb_2d, self.op_xycb_2e, self.op_xycb_2f,
            self.op_xycb_30, self.op_xycb_31, self.op_xycb_32, self.op_xycb_33,
            self.op_xycb_34, self.op_xycb_35, self.op_xycb_36, self.op_xycb_37,
            self.op_xycb_38, self.op_xycb_39, self.op_xycb_3a, self.op_xycb_3b,
            self.op_xycb_3c, self.op_xycb_3d, self.op_xycb_3e, self.op_xycb_3f,
            self.op_xycb_40, self.op_xycb_41, self.op_xycb_42, self.op_xycb_43,
            self.op_xycb_44, self.op_xycb_45, self.op_xycb_46, self.op_xycb_47,
            self.op_xycb_48, self.op_xycb_49, self.op_xycb_4a, self.op_xycb_4b,
            self.op_xycb_4c, self.op_xycb_4d, self.op_xycb_4e, self.op_xycb_4f,
            self.op_xycb_50, self.op_xycb_51, self.op_xycb_52, self.op_xycb_53,
            self.op_xycb_54, self.op_xycb_55, self.op_xycb_56, self.op_xycb_57,
            self.op_xycb_58, self.op_xycb_59, self.op_xycb_5a, self.op_xycb_5b,
            self.op_xycb_5c, self.op_xycb_5d, self.op_xycb_5e, self.op_xycb_5f,
            self.op_xycb_60, self.op_xycb_61, self.op_xycb_62, self.op_xycb_63,
            self.op_xycb_64, self.op_xycb_65, self.op_xycb_66, self.op_xycb_67,
            self.op_xycb_68, self.op_xycb_69, self.op_xycb_6a, self.op_xycb_6b,
            self.op_xycb_6c, self.op_xycb_6d, self.op_xycb_6e, self.op_xycb_6f,
            self.op_xycb_70, self.op_xycb_71, self.op_xycb_72, self.op_xycb_73,
            self.op_xycb_74, self.op_xycb_75, self.op_xycb_76, self.op_xycb_77,
            self.op_xycb_78, self.op_xycb_79, self.op_xycb_7a, self.op_xycb_7b,
            self.op_xycb_7c, self.op_xycb_7d, self.op_xycb_7e, self.op_xycb_7f,
            self.op_xycb_80, self.op_xycb_81, self.op_xycb_82, self.op_xycb_83,
            self.op_xycb_84, self.op_xycb_85, self.op_xycb_86, self.op_xycb_87,
            self.op_xycb_88, self.op_xycb_89, self.op_xycb_8a, self.op_xycb_8b,
            self.op_xycb_8c, self.op_xycb_8d, self.op_xycb_8e, self.op_xycb_8f,
            self.op_xycb_90, self.op_xycb_91, self.op_xycb_92, self.op_xycb_93,
            self.op_xycb_94, self.op_xycb_95, self.op_xycb_96, self.op_xycb_97,
            self.op_xycb_98, self.op_xycb_99, self.op_xycb_9a, self.op_xycb_9b,
            self.op_xycb_9c, self.op_xycb_9d, self.op_xycb_9e, self.op_xycb_9f,
            self.op_xycb_a0, self.op_xycb_a1, self.op_xycb_a2, self.op_xycb_a3,
            self.op_xycb_a4, self.op_xycb_a5, self.op_xycb_a6, self.op_xycb_a7,
            self.op_xycb_a8, self.op_xycb_a9, self.op_xycb_aa, self.op_xycb_ab,
            self.op_xycb_ac, self.op_xycb_ad, self.op_xycb_ae, self.op_xycb_af,
            self.op_xycb_b0, self.op_xycb_b1, self.op_xycb_b2, self.op_xycb_b3,
            self.op_xycb_b4, self.op_xycb_b5, self.op_xycb_b6, self.op_xycb_b7,
            self.op_xycb_b8, self.op_xycb_b9, self.op_xycb_ba, self.op_xycb_bb,
            self.op_xycb_bc, self.op_xycb_bd, self.op_xycb_be, self.op_xycb_bf,
            self.op_xycb_c0, self.op_xycb_c1, self.op_xycb_c2, self.op_xycb_c3,
            self.op_xycb_c4, self.op_xycb_c5, self.op_xycb_c6, self.op_xycb_c7,
            self.op_xycb_c8, self.op_xycb_c9, self.op_xycb_ca, self.op_xycb_cb,
            self.op_xycb_cc, self.op_xycb_cd, self.op_xycb_ce, self.op_xycb_cf,
            self.op_xycb_d0, self.op_xycb_d1, self.op_xycb_d2, self.op_xycb_d3,
            self.op_xycb_d4, self.op_xycb_d5, self.op_xycb_d6, self.op_xycb_d7,
            self.op_xycb_d8, self.op_xycb_d9, self.op_xycb_da, self.op_xycb_db,
            self.op_xycb_dc, self.op_xycb_dd, self.op_xycb_de, self.op_xycb_df,
            self.op_xycb_e0, self.op_xycb_e1, self.op_xycb_e2, self.op_xycb_e3,
            self.op_xycb_e4, self.op_xycb_e5, self.op_xycb_e6, self.op_xycb_e7,
            self.op_xycb_e8, self.op_xycb_e9, self.op_xycb_ea, self.op_xycb_eb,
            self.op_xycb_ec, self.op_xycb_ed, self.op_xycb_ee, self.op_xycb_ef,
            self.op_xycb_f0, self.op_xycb_f1, self.op_xycb_f2, self.op_xycb_f3,
            self.op_xycb_f4, self.op_xycb_f5, self.op_xycb_f6, self.op_xycb_f7,
            self.op_xycb_f8, self.op_xycb_f9, self.op_xycb_fa, self.op_xycb_fb,
            self.op_xycb_fc, self.op_xycb_fd, self.op_xycb_fe, self.op_xycb_ff,
        ]
        self.op_dd = [
            self.op_dd_00, self.op_dd_01, self.op_dd_02, self.op_dd_03,
            self.op_dd_04, self.op_dd_05, self.op_dd_06, self.op_dd_07,
            self.op_dd_08, self.op_dd_09, self.op_dd_0a, self.op_dd_0b,
            self.op_dd_0c, self.op_dd_0d, self.op_dd_0e, self.op_dd_0f,
            self.op_dd_10, self.op_dd_11, self.op_dd_12, self.op_dd_13,
            self.op_dd_14, self.op_dd_15, self.op_dd_16, self.op_dd_17,
            self.op_dd_18, self.op_dd_19, self.op_dd_1a, self.op_dd_1b,
            self.op_dd_1c, self.op_dd_1d, self.op_dd_1e, self.op_dd_1f,
            self.op_dd_20, self.op_dd_21, self.op_dd_22, self.op_dd_23,
            self.op_dd_24, self.op_dd_25, self.op_dd_26, self.op_dd_27,
            self.op_dd_28, self.op_dd_29, self.op_dd_2a, self.op_dd_2b,
            self.op_dd_2c, self.op_dd_2d, self.op_dd_2e, self.op_dd_2f,
            self.op_dd_30, self.op_dd_31, self.op_dd_32, self.op_dd_33,
            self.op_dd_34, self.op_dd_35, self.op_dd_36, self.op_dd_37,
            self.op_dd_38, self.op_dd_39, self.op_dd_3a, self.op_dd_3b,
            self.op_dd_3c, self.op_dd_3d, self.op_dd_3e, self.op_dd_3f,
            self.op_dd_40, self.op_dd_41, self.op_dd_42, self.op_dd_43,
            self.op_dd_44, self.op_dd_45, self.op_dd_46, self.op_dd_47,
            self.op_dd_48, self.op_dd_49, self.op_dd_4a, self.op_dd_4b,
            self.op_dd_4c, self.op_dd_4d, self.op_dd_4e, self.op_dd_4f,
            self.op_dd_50, self.op_dd_51, self.op_dd_52, self.op_dd_53,
            self.op_dd_54, self.op_dd_55, self.op_dd_56, self.op_dd_57,
            self.op_dd_58, self.op_dd_59, self.op_dd_5a, self.op_dd_5b,
            self.op_dd_5c, self.op_dd_5d, self.op_dd_5e, self.op_dd_5f,
            self.op_dd_60, self.op_dd_61, self.op_dd_62, self.op_dd_63,
            self.op_dd_64, self.op_dd_65, self.op_dd_66, self.op_dd_67,
            self.op_dd_68, self.op_dd_69, self.op_dd_6a, self.op_dd_6b,
            self.op_dd_6c, self.op_dd_6d, self.op_dd_6e, self.op_dd_6f,
            self.op_dd_70, self.op_dd_71, self.op_dd_72, self.op_dd_73,
            self.op_dd_74, self.op_dd_75, self.op_dd_76, self.op_dd_77,
            self.op_dd_78, self.op_dd_79, self.op_dd_7a, self.op_dd_7b,
            self.op_dd_7c, self.op_dd_7d, self.op_dd_7e, self.op_dd_7f,
            self.op_dd_80, self.op_dd_81, self.op_dd_82, self.op_dd_83,
            self.op_dd_84, self.op_dd_85, self.op_dd_86, self.op_dd_87,
            self.op_dd_88, self.op_dd_89, self.op_dd_8a, self.op_dd_8b,
            self.op_dd_8c, self.op_dd_8d, self.op_dd_8e, self.op_dd_8f,
            self.op_dd_90, self.op_dd_91, self.op_dd_92, self.op_dd_93,
            self.op_dd_94, self.op_dd_95, self.op_dd_96, self.op_dd_97,
            self.op_dd_98, self.op_dd_99, self.op_dd_9a, self.op_dd_9b,
            self.op_dd_9c, self.op_dd_9d, self.op_dd_9e, self.op_dd_9f,
            self.op_dd_a0, self.op_dd_a1, self.op_dd_a2, self.op_dd_a3,
            self.op_dd_a4, self.op_dd_a5, self.op_dd_a6, self.op_dd_a7,
            self.op_dd_a8, self.op_dd_a9, self.op_dd_aa, self.op_dd_ab,
            self.op_dd_ac, self.op_dd_ad, self.op_dd_ae, self.op_dd_af,
            self.op_dd_b0, self.op_dd_b1, self.op_dd_b2, self.op_dd_b3,
            self.op_dd_b4, self.op_dd_b5, self.op_dd_b6, self.op_dd_b7,
            self.op_dd_b8, self.op_dd_b9, self.op_dd_ba, self.op_dd_bb,
            self.op_dd_bc, self.op_dd_bd, self.op_dd_be, self.op_dd_bf,
            self.op_dd_c0, self.op_dd_c1, self.op_dd_c2, self.op_dd_c3,
            self.op_dd_c4, self.op_dd_c5, self.op_dd_c6, self.op_dd_c7,
            self.op_dd_c8, self.op_dd_c9, self.op_dd_ca, self.op_dd_cb,
            self.op_dd_cc, self.op_dd_cd, self.op_dd_ce, self.op_dd_cf,
            self.op_dd_d0, self.op_dd_d1, self.op_dd_d2, self.op_dd_d3,
            self.op_dd_d4, self.op_dd_d5, self.op_dd_d6, self.op_dd_d7,
            self.op_dd_d8, self.op_dd_d9, self.op_dd_da, self.op_dd_db,
            self.op_dd_dc, self.op_dd_dd, self.op_dd_de, self.op_dd_df,
            self.op_dd_e0, self.op_dd_e1, self.op_dd_e2, self.op_dd_e3,
            self.op_dd_e4, self.op_dd_e5, self.op_dd_e6, self.op_dd_e7,
            self.op_dd_e8, self.op_dd_e9, self.op_dd_ea, self.op_dd_eb,
            self.op_dd_ec, self.op_dd_ed, self.op_dd_ee, self.op_dd_ef,
            self.op_dd_f0, self.op_dd_f1, self.op_dd_f2, self.op_dd_f3,
            self.op_dd_f4, self.op_dd_f5, self.op_dd_f6, self.op_dd_f7,
            self.op_dd_f8, self.op_dd_f9, self.op_dd_fa, self.op_dd_fb,
            self.op_dd_fc, self.op_dd_fd, self.op_dd_fe, self.op_dd_ff,
        ]
        self.op_fd = [
            self.op_fd_00, self.op_fd_01, self.op_fd_02, self.op_fd_03,
            self.op_fd_04, self.op_fd_05, self.op_fd_06, self.op_fd_07,
            self.op_fd_08, self.op_fd_09, self.op_fd_0a, self.op_fd_0b,
            self.op_fd_0c, self.op_fd_0d, self.op_fd_0e, self.op_fd_0f,
            self.op_fd_10, self.op_fd_11, self.op_fd_12, self.op_fd_13,
            self.op_fd_14, self.op_fd_15, self.op_fd_16, self.op_fd_17,
            self.op_fd_18, self.op_fd_19, self.op_fd_1a, self.op_fd_1b,
            self.op_fd_1c, self.op_fd_1d, self.op_fd_1e, self.op_fd_1f,
            self.op_fd_20, self.op_fd_21, self.op_fd_22, self.op_fd_23,
            self.op_fd_24, self.op_fd_25, self.op_fd_26, self.op_fd_27,
            self.op_fd_28, self.op_fd_29, self.op_fd_2a, self.op_fd_2b,
            self.op_fd_2c, self.op_fd_2d, self.op_fd_2e, self.op_fd_2f,
            self.op_fd_30, self.op_fd_31, self.op_fd_32, self.op_fd_33,
            self.op_fd_34, self.op_fd_35, self.op_fd_36, self.op_fd_37,
            self.op_fd_38, self.op_fd_39, self.op_fd_3a, self.op_fd_3b,
            self.op_fd_3c, self.op_fd_3d, self.op_fd_3e, self.op_fd_3f,
            self.op_fd_40, self.op_fd_41, self.op_fd_42, self.op_fd_43,
            self.op_fd_44, self.op_fd_45, self.op_fd_46, self.op_fd_47,
            self.op_fd_48, self.op_fd_49, self.op_fd_4a, self.op_fd_4b,
            self.op_fd_4c, self.op_fd_4d, self.op_fd_4e, self.op_fd_4f,
            self.op_fd_50, self.op_fd_51, self.op_fd_52, self.op_fd_53,
            self.op_fd_54, self.op_fd_55, self.op_fd_56, self.op_fd_57,
            self.op_fd_58, self.op_fd_59, self.op_fd_5a, self.op_fd_5b,
            self.op_fd_5c, self.op_fd_5d, self.op_fd_5e, self.op_fd_5f,
            self.op_fd_60, self.op_fd_61, self.op_fd_62, self.op_fd_63,
            self.op_fd_64, self.op_fd_65, self.op_fd_66, self.op_fd_67,
            self.op_fd_68, self.op_fd_69, self.op_fd_6a, self.op_fd_6b,
            self.op_fd_6c, self.op_fd_6d, self.op_fd_6e, self.op_fd_6f,
            self.op_fd_70, self.op_fd_71, self.op_fd_72, self.op_fd_73,
            self.op_fd_74, self.op_fd_75, self.op_fd_76, self.op_fd_77,
            self.op_fd_78, self.op_fd_79, self.op_fd_7a, self.op_fd_7b,
            self.op_fd_7c, self.op_fd_7d, self.op_fd_7e, self.op_fd_7f,
            self.op_fd_80, self.op_fd_81, self.op_fd_82, self.op_fd_83,
            self.op_fd_84, self.op_fd_85, self.op_fd_86, self.op_fd_87,
            self.op_fd_88, self.op_fd_89, self.op_fd_8a, self.op_fd_8b,
            self.op_fd_8c, self.op_fd_8d, self.op_fd_8e, self.op_fd_8f,
            self.op_fd_90, self.op_fd_91, self.op_fd_92, self.op_fd_93,
            self.op_fd_94, self.op_fd_95, self.op_fd_96, self.op_fd_97,
            self.op_fd_98, self.op_fd_99, self.op_fd_9a, self.op_fd_9b,
            self.op_fd_9c, self.op_fd_9d, self.op_fd_9e, self.op_fd_9f,
            self.op_fd_a0, self.op_fd_a1, self.op_fd_a2, self.op_fd_a3,
            self.op_fd_a4, self.op_fd_a5, self.op_fd_a6, self.op_fd_a7,
            self.op_fd_a8, self.op_fd_a9, self.op_fd_aa, self.op_fd_ab,
            self.op_fd_ac, self.op_fd_ad, self.op_fd_ae, self.op_fd_af,
            self.op_fd_b0, self.op_fd_b1, self.op_fd_b2, self.op_fd_b3,
            self.op_fd_b4, self.op_fd_b5, self.op_fd_b6, self.op_fd_b7,
            self.op_fd_b8, self.op_fd_b9, self.op_fd_ba, self.op_fd_bb,
            self.op_fd_bc, self.op_fd_bd, self.op_fd_be, self.op_fd_bf,
            self.op_fd_c0, self.op_fd_c1, self.op_fd_c2, self.op_fd_c3,
            self.op_fd_c4, self.op_fd_c5, self.op_fd_c6, self.op_fd_c7,
            self.op_fd_c8, self.op_fd_c9, self.op_fd_ca, self.op_fd_cb,
            self.op_fd_cc, self.op_fd_cd, self.op_fd_ce, self.op_fd_cf,
            self.op_fd_d0, self.op_fd_d1, self.op_fd_d2, self.op_fd_d3,
            self.op_fd_d4, self.op_fd_d5, self.op_fd_d6, self.op_fd_d7,
            self.op_fd_d8, self.op_fd_d9, self.op_fd_da, self.op_fd_db,
            self.op_fd_dc, self.op_fd_dd, self.op_fd_de, self.op_fd_df,
            self.op_fd_e0, self.op_fd_e1, self.op_fd_e2, self.op_fd_e3,
            self.op_fd_e4, self.op_fd_e5, self.op_fd_e6, self.op_fd_e7,
            self.op_fd_e8, self.op_fd_e9, self.op_fd_ea, self.op_fd_eb,
            self.op_fd_ec, self.op_fd_ed, self.op_fd_ee, self.op_fd_ef,
            self.op_fd_f0, self.op_fd_f1, self.op_fd_f2, self.op_fd_f3,
            self.op_fd_f4, self.op_fd_f5, self.op_fd_f6, self.op_fd_f7,
            self.op_fd_f8, self.op_fd_f9, self.op_fd_fa, self.op_fd_fb,
            self.op_fd_fc, self.op_fd_fd, self.op_fd_fe, self.op_fd_ff,
        ]
        self.op_ed = [
            self.op_ed_00, self.op_ed_01, self.op_ed_02, self.op_ed_03,
            self.op_ed_04, self.op_ed_05, self.op_ed_06, self.op_ed_07,
            self.op_ed_08, self.op_ed_09, self.op_ed_0a, self.op_ed_0b,
            self.op_ed_0c, self.op_ed_0d, self.op_ed_0e, self.op_ed_0f,
            self.op_ed_10, self.op_ed_11, self.op_ed_12, self.op_ed_13,
            self.op_ed_14, self.op_ed_15, self.op_ed_16, self.op_ed_17,
            self.op_ed_18, self.op_ed_19, self.op_ed_1a, self.op_ed_1b,
            self.op_ed_1c, self.op_ed_1d, self.op_ed_1e, self.op_ed_1f,
            self.op_ed_20, self.op_ed_21, self.op_ed_22, self.op_ed_23,
            self.op_ed_24, self.op_ed_25, self.op_ed_26, self.op_ed_27,
            self.op_ed_28, self.op_ed_29, self.op_ed_2a, self.op_ed_2b,
            self.op_ed_2c, self.op_ed_2d, self.op_ed_2e, self.op_ed_2f,
            self.op_ed_30, self.op_ed_31, self.op_ed_32, self.op_ed_33,
            self.op_ed_34, self.op_ed_35, self.op_ed_36, self.op_ed_37,
            self.op_ed_38, self.op_ed_39, self.op_ed_3a, self.op_ed_3b,
            self.op_ed_3c, self.op_ed_3d, self.op_ed_3e, self.op_ed_3f,
            self.op_ed_40, self.op_ed_41, self.op_ed_42, self.op_ed_43,
            self.op_ed_44, self.op_ed_45, self.op_ed_46, self.op_ed_47,
            self.op_ed_48, self.op_ed_49, self.op_ed_4a, self.op_ed_4b,
            self.op_ed_4c, self.op_ed_4d, self.op_ed_4e, self.op_ed_4f,
            self.op_ed_50, self.op_ed_51, self.op_ed_52, self.op_ed_53,
            self.op_ed_54, self.op_ed_55, self.op_ed_56, self.op_ed_57,
            self.op_ed_58, self.op_ed_59, self.op_ed_5a, self.op_ed_5b,
            self.op_ed_5c, self.op_ed_5d, self.op_ed_5e, self.op_ed_5f,
            self.op_ed_60, self.op_ed_61, self.op_ed_62, self.op_ed_63,
            self.op_ed_64, self.op_ed_65, self.op_ed_66, self.op_ed_67,
            self.op_ed_68, self.op_ed_69, self.op_ed_6a, self.op_ed_6b,
            self.op_ed_6c, self.op_ed_6d, self.op_ed_6e, self.op_ed_6f,
            self.op_ed_70, self.op_ed_71, self.op_ed_72, self.op_ed_73,
            self.op_ed_74, self.op_ed_75, self.op_ed_76, self.op_ed_77,
            self.op_ed_78, self.op_ed_79, self.op_ed_7a, self.op_ed_7b,
            self.op_ed_7c, self.op_ed_7d, self.op_ed_7e, self.op_ed_7f,
            self.op_ed_80, self.op_ed_81, self.op_ed_82, self.op_ed_83,
            self.op_ed_84, self.op_ed_85, self.op_ed_86, self.op_ed_87,
            self.op_ed_88, self.op_ed_89, self.op_ed_8a, self.op_ed_8b,
            self.op_ed_8c, self.op_ed_8d, self.op_ed_8e, self.op_ed_8f,
            self.op_ed_90, self.op_ed_91, self.op_ed_92, self.op_ed_93,
            self.op_ed_94, self.op_ed_95, self.op_ed_96, self.op_ed_97,
            self.op_ed_98, self.op_ed_99, self.op_ed_9a, self.op_ed_9b,
            self.op_ed_9c, self.op_ed_9d, self.op_ed_9e, self.op_ed_9f,
            self.op_ed_a0, self.op_ed_a1, self.op_ed_a2, self.op_ed_a3,
            self.op_ed_a4, self.op_ed_a5, self.op_ed_a6, self.op_ed_a7,
            self.op_ed_a8, self.op_ed_a9, self.op_ed_aa, self.op_ed_ab,
            self.op_ed_ac, self.op_ed_ad, self.op_ed_ae, self.op_ed_af,
            self.op_ed_b0, self.op_ed_b1, self.op_ed_b2, self.op_ed_b3,
            self.op_ed_b4, self.op_ed_b5, self.op_ed_b6, self.op_ed_b7,
            self.op_ed_b8, self.op_ed_b9, self.op_ed_ba, self.op_ed_bb,
            self.op_ed_bc, self.op_ed_bd, self.op_ed_be, self.op_ed_bf,
            self.op_ed_c0, self.op_ed_c1, self.op_ed_c2, self.op_ed_c3,
            self.op_ed_c4, self.op_ed_c5, self.op_ed_c6, self.op_ed_c7,
            self.op_ed_c8, self.op_ed_c9, self.op_ed_ca, self.op_ed_cb,
            self.op_ed_cc, self.op_ed_cd, self.op_ed_ce, self.op_ed_cf,
            self.op_ed_d0, self.op_ed_d1, self.op_ed_d2, self.op_ed_d3,
            self.op_ed_d4, self.op_ed_d5, self.op_ed_d6, self.op_ed_d7,
            self.op_ed_d8, self.op_ed_d9, self.op_ed_da, self.op_ed_db,
            self.op_ed_dc, self.op_ed_dd, self.op_ed_de, self.op_ed_df,
            self.op_ed_e0, self.op_ed_e1, self.op_ed_e2, self.op_ed_e3,
            self.op_ed_e4, self.op_ed_e5, self.op_ed_e6, self.op_ed_e7,
            self.op_ed_e8, self.op_ed_e9, self.op_ed_ea, self.op_ed_eb,
            self.op_ed_ec, self.op_ed_ed, self.op_ed_ee, self.op_ed_ef,
            self.op_ed_f0, self.op_ed_f1, self.op_ed_f2, self.op_ed_f3,
            self.op_ed_f4, self.op_ed_f5, self.op_ed_f6, self.op_ed_f7,
            self.op_ed_f8, self.op_ed_f9, self.op_ed_fa, self.op_ed_fb,
            self.op_ed_fc, self.op_ed_fd, self.op_ed_fe, self.op_ed_ff,
        ]
        self.op_op = [
            self.op_op_00, self.op_op_01, self.op_op_02, self.op_op_03,
            self.op_op_04, self.op_op_05, self.op_op_06, self.op_op_07,
            self.op_op_08, self.op_op_09, self.op_op_0a, self.op_op_0b,
            self.op_op_0c, self.op_op_0d, self.op_op_0e, self.op_op_0f,
            self.op_op_10, self.op_op_11, self.op_op_12, self.op_op_13,
            self.op_op_14, self.op_op_15, self.op_op_16, self.op_op_17,
            self.op_op_18, self.op_op_19, self.op_op_1a, self.op_op_1b,
            self.op_op_1c, self.op_op_1d, self.op_op_1e, self.op_op_1f,
            self.op_op_20, self.op_op_21, self.op_op_22, self.op_op_23,
            self.op_op_24, self.op_op_25, self.op_op_26, self.op_op_27,
            self.op_op_28, self.op_op_29, self.op_op_2a, self.op_op_2b,
            self.op_op_2c, self.op_op_2d, self.op_op_2e, self.op_op_2f,
            self.op_op_30, self.op_op_31, self.op_op_32, self.op_op_33,
            self.op_op_34, self.op_op_35, self.op_op_36, self.op_op_37,
            self.op_op_38, self.op_op_39, self.op_op_3a, self.op_op_3b,
            self.op_op_3c, self.op_op_3d, self.op_op_3e, self.op_op_3f,
            self.op_op_40, self.op_op_41, self.op_op_42, self.op_op_43,
            self.op_op_44, self.op_op_45, self.op_op_46, self.op_op_47,
            self.op_op_48, self.op_op_49, self.op_op_4a, self.op_op_4b,
            self.op_op_4c, self.op_op_4d, self.op_op_4e, self.op_op_4f,
            self.op_op_50, self.op_op_51, self.op_op_52, self.op_op_53,
            self.op_op_54, self.op_op_55, self.op_op_56, self.op_op_57,
            self.op_op_58, self.op_op_59, self.op_op_5a, self.op_op_5b,
            self.op_op_5c, self.op_op_5d, self.op_op_5e, self.op_op_5f,
            self.op_op_60, self.op_op_61, self.op_op_62, self.op_op_63,
            self.op_op_64, self.op_op_65, self.op_op_66, self.op_op_67,
            self.op_op_68, self.op_op_69, self.op_op_6a, self.op_op_6b,
            self.op_op_6c, self.op_op_6d, self.op_op_6e, self.op_op_6f,
            self.op_op_70, self.op_op_71, self.op_op_72, self.op_op_73,
            self.op_op_74, self.op_op_75, self.op_op_76, self.op_op_77,
            self.op_op_78, self.op_op_79, self.op_op_7a, self.op_op_7b,
            self.op_op_7c, self.op_op_7d, self.op_op_7e, self.op_op_7f,
            self.op_op_80, self.op_op_81, self.op_op_82, self.op_op_83,
            self.op_op_84, self.op_op_85, self.op_op_86, self.op_op_87,
            self.op_op_88, self.op_op_89, self.op_op_8a, self.op_op_8b,
            self.op_op_8c, self.op_op_8d, self.op_op_8e, self.op_op_8f,
            self.op_op_90, self.op_op_91, self.op_op_92, self.op_op_93,
            self.op_op_94, self.op_op_95, self.op_op_96, self.op_op_97,
            self.op_op_98, self.op_op_99, self.op_op_9a, self.op_op_9b,
            self.op_op_9c, self.op_op_9d, self.op_op_9e, self.op_op_9f,
            self.op_op_a0, self.op_op_a1, self.op_op_a2, self.op_op_a3,
            self.op_op_a4, self.op_op_a5, self.op_op_a6, self.op_op_a7,
            self.op_op_a8, self.op_op_a9, self.op_op_aa, self.op_op_ab,
            self.op_op_ac, self.op_op_ad, self.op_op_ae, self.op_op_af,
            self.op_op_b0, self.op_op_b1, self.op_op_b2, self.op_op_b3,
            self.op_op_b4, self.op_op_b5, self.op_op_b6, self.op_op_b7,
            self.op_op_b8, self.op_op_b9, self.op_op_ba, self.op_op_bb,
            self.op_op_bc, self.op_op_bd, self.op_op_be, self.op_op_bf,
            self.op_op_c0, self.op_op_c1, self.op_op_c2, self.op_op_c3,
            self.op_op_c4, self.op_op_c5, self.op_op_c6, self.op_op_c7,
            self.op_op_c8, self.op_op_c9, self.op_op_ca, self.op_op_cb,
            self.op_op_cc, self.op_op_cd, self.op_op_ce, self.op_op_cf,
            self.op_op_d0, self.op_op_d1, self.op_op_d2, self.op_op_d3,
            self.op_op_d4, self.op_op_d5, self.op_op_d6, self.op_op_d7,
            self.op_op_d8, self.op_op_d9, self.op_op_da, self.op_op_db,
            self.op_op_dc, self.op_op_dd, self.op_op_de, self.op_op_df,
            self.op_op_e0, self.op_op_e1, self.op_op_e2, self.op_op_e3,
            self.op_op_e4, self.op_op_e5, self.op_op_e6, self.op_op_e7,
            self.op_op_e8, self.op_op_e9, self.op_op_ea, self.op_op_eb,
            self.op_op_ec, self.op_op_ed, self.op_op_ee, self.op_op_ef,
            self.op_op_f0, self.op_op_f1, self.op_op_f2, self.op_op_f3,
            self.op_op_f4, self.op_op_f5, self.op_op_f6, self.op_op_f7,
            self.op_op_f8, self.op_op_f9, self.op_op_fa, self.op_op_fb,
            self.op_op_fc, self.op_op_fd, self.op_op_fe, self.op_op_ff,
        ]

    def take_nmi(self):
        # Check if processor was halted
        self.leave_halt()

        self.m_iff1 = 0
        self.m_r += 1

        self.m_icount_executing = 11
        self.T(self.m_icount_executing - self.MTM * 2)
        self.wm16_sp(self.m_pc)
        self.PC = 0x0066
        self.WZ = self.PC
        self.m_nmi_pending = False

    def take_interrupt(self):
        # check if processor was halted
        self.leave_halt()

        # clear both interrupt flip flops
        self.m_iff1 = self.m_iff2 = 0

        # say hi
        # Not precise in all cases. z80 must finish current instruction (NOP) to reach this state - in such case frame timings are shifter from cb event if calulated based on it.
        # self.m_irqack_cb(True)
        self.m_r += 1

        # fetch the IRQ vector
        irq_vector = self.irq_vector()

        # 'interrupt latency' cycles
        self.m_icount_executing = 0
        self.CC(Z80.cc_op, 0xff)
        self.T(self.m_icount_executing)

        # Interrupt mode 2. Call [i:databyte]
        if self.m_im == 2:
            # Zilog's datasheet claims that "the least-significant bit must be a zero."
            # However, experiments have confirmed that IM 2 vectors do not have to be
            # even, and all 8 bits will be used; even $FF is handled normally.
            # CALL opcode timing
            self.CC(Z80.cc_op, 0xcd) # 17+2=19
            self.T(self.m_icount_executing - self.MTM * 4)
            self.m_icount_executing -= self.MTM * 2 # save for rm16
            self.wm16_sp(self.m_pc)
            self.m_icount_executing -= self.MTM * 2
            irq_vector = (irq_vector & 0xff) | (self.m_i << 8)
            self.rm16(irq_vector, self.m_pc)

        # Interrupt mode 1. RST 38h
        elif self.m_im == 1:
            # RST $38
            self.CC(Z80.cc_op, 0xff) # 11+2 = 13
            self.T(self.m_icount_executing - self.MTM * 4)
            self.wm16_sp(self.m_pc)
            self.PC = 0x0038
        else:
            # Interrupt mode 0. We check for CALL and JP instructions,
            # if neither of these were found we assume a 1 byte opcode
            # was placed on the databus

            # check for nop
            if irq_vector != 0x00:
                v = irq_vector & 0xff0000
                if v == 0xcd0000: # call
                    # CALL $xxxx cycles
                    self.CC(Z80.cc_op, 0xcd)
                    self.T(self.m_icount_executing - self.MTM * 2)
                    self.wm16_sp(self.m_pc)
                    self.PC = irq_vector & 0xffff
                if v == 0xc30000: # jump
                    # JP $xxxx cycles
                    self.CC(Z80.cc_op, 0xc3)
                    self.T(self.m_icount_executing)
                    self.PC = irq_vector & 0xffff
                else: # rst (or other opcodes?)
                    # RST $xx cycles
                    self.CC(Z80.cc_op, 0xff)
                    self.T(self.m_icount_executing - self.MTM * 2)
                    self.wm16_sp(self.m_pc)
                    self.PC = irq_vector & 0x0038

        self.WZ = self.PC


    def irq_vector(self):
        vector = 0
        if not self.m_irq_vector is None:
            vector = self.m_irq_vector()
        return vector
    
    def set_irq_vector(self, vector):
        self.m_irq_vector = vector

    def nomreq_ir(self, cycles):
        self.nomreq_addr((self.m_i << 8) | (self.m_r2 & 0x80) | (self.m_r & 0x7f), cycles)

    def nomreq_addr(self, addr, cycles):
        self.T(cycles)

    def execute_min_cycles(self):
        return 2


    def execute_run(self):
        """Execute 'cycles' T-states.
        """
        while True:
            if self.m_wait_state:
                # stalled
                self.m_icount = 0
                return

            # check for interrupts before each instruction
            self.check_interrupts()
            self.m_icount_executing = 0

            self.m_after_ei = False
            self.m_after_ldair = False

            opcode = self.rop()

            # when in HALT state, the fetched opcode is not dispatched (aka a NOP)
            if self.m_halt:
                self.PC -= 1
                opcode = 0

            self.EXEC(Z80.cc_op, self.op_op, opcode)

            #self.dump()

            if self.m_icount < 0:
                break

    def check_interrupts(self):
        if (self.m_nmi_pending):
            self.take_nmi()
        elif ((self.m_irq_state != Z80.CLEAR_LINE) and self.m_iff1 and not self.m_after_ei):
            self.take_interrupt()

    def execute_set_input(self, inputnum, state):
        if inputnum == Z80.INPUT_LINE_BUSRQ:
            self.m_busrq_state = state
        elif inputnum == Z80.INPUT_LINE_NMI:
            # mark an NMI pending on the rising edge
            if (self.m_nmi_state == Z80.CLEAR_LINE) and (state != Z80.CLEAR_LINE):
                self.m_nmi_pending = True
            self.m_nmi_state = state
        elif inputnum == Z80.INPUT_LINE_IRQ0:
            # update the IRQ state via the daisy chain
            self.m_irq_state = state
            # the main execute loop will take the interrupt
        elif inputnum == Z80.INPUT_LINE_WAIT:
            self.m_wait_state = state

    def log(self, msg):
        if self.m_enable_debug:
            print(msg, flush=True)

    def dump(self):
        print("--------------------------------")
        print("PC:{:04x} SP:{:04x}".format(self.PC, self.SP))
        print("AF:{:04x} BC:{:04x} DE:{:04x} HL:{:04x}".format(self.AF, self.BC, self.DE, self.HL))
        print("   {:04x}    {:04x}    {:04x}    {:04x}".format(self.m_af2.w, self.m_bc2.w, self.m_de2.w, self.m_hl2.w))
        print("IX:{:04x} IY:{:04x}".format(self.IX, self.IY))
        print(" S:{:d}".format(1 if self.F & Z80.SF else 0), end='')
        print(" Z:{:d}".format(1 if self.F & Z80.ZF else 0), end='')
        print(" Y:{:d}".format(1 if self.F & Z80.YF else 0), end='')
        print(" H:{:d}".format(1 if self.F & Z80.HF else 0), end='')
        print(" X:{:d}".format(1 if self.F & Z80.XF else 0), end='')
        print(" P:{:d}".format(1 if self.F & Z80.PF else 0), end='')
        print(" N:{:d}".format(1 if self.F & Z80.NF else 0), end='')
        print(" C:{:d}".format(1 if self.F & Z80.CF else 0), end='')
        print("")
        print("--------------------------------")
