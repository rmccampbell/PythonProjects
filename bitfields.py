class bitfield:
    def __init__(self, field, off, size):
        self.field = field
        self.off = off
        self.size = size
    def __get__(self, inst, owner=None):
        if inst is not None:
            mask = ~(-1 << self.size)
            val = getattr(inst, self.field)
            return val >> self.off & mask
        return self
    def __set__(self, inst, value):
        mask = ~(-1 << self.size)
        value &= mask
        val = getattr(inst, self.field)
        val = val & ~(mask << self.off) | value << self.off
        setattr(inst, self.field, val)

class Instruction:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return 'Instruction({:#018b})'.format(self.value)
    a = bitfield('value', 0, 4)
    b = bitfield('value', 4, 4)
    c = bitfield('value', 8, 8)
