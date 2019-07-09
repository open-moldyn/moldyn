# -*-encoding: utf-8 -*-
"""
Types personnalisés utilisés pour moldyn
"""

from struct import pack

class sList(list): # liste qui se convertir en bytes gentiment
    def __bytes__(self):
        return pack("".join((str(len(self)),"i")),*self)
    def __repr__(self):
        return "".join(("sList(", super().__repr__(), ")"))
