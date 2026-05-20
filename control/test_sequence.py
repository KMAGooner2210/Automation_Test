from .test_sequence_item import TestSequenceItem_t
from .logger import TestLogger

class TestSequence_t:
    '''
    TestSequence_t Is data load from a sequence excel.
    '''

    def __init__(self, logger:TestLogger = None):
        self.version = "not set"
        self.test_name = "not set"
        self.specVersion = "not set"
        self.logger = logger
        self.TestSequence:TestSequenceItem_t = []

    def SetVersion(self, version):
        self.version = version

    def SetTestName(self, test_name):
        self.test_name = test_name

    def SetSpecVersion(self, spec_version):
        self.specVersion = spec_version

    def addSequence(self, sequence: TestSequenceItem_t):
        self.TestSequence.append(sequence)

    def ClearSequence(self):
        if self.TestSequence:
            self.TestSequence.clear()

    def getJsonData(self):
        testSeq = []
        for t in self.TestSequence:
            testSeq.append(t.GetJsonData())
        return {
            'version' : self.version,
            'test_name' : self.test_name,
            'specVersion' : self.specVersion,
            'TestSequence' : testSeq
        }