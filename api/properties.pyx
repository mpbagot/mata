class Property:
    def __init__(self, **kwargs):
        for val in kwargs.items():
            self.__setattr__(*val)
