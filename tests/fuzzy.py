from factory.fuzzy import BaseFuzzyAttribute
from factory.random import randgen as factory_randgen


class FuzzyBytes(BaseFuzzyAttribute):
    def __init__(self):
        self.length = factory_randgen.randint(64, 1024)
        super().__init__()

    def fuzz(self):
        return factory_randgen.randbytes(self.length)
