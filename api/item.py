'''
item.py
A module to hold all the api stuff related to items
'''
class Inventory:
    def __init__(self):
        self.items = []

    @staticmethod
    def getFromBytes(byte):
        return Inventory()

    def encode(self):
        return b''
