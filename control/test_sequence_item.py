from .logger import TestLogger

class TestSequenceItem_t:
    def __init__(self, logger:TestLogger, ignore="n", testCaseName = "NoName", testItemName = "", testStepName = "",
                equalValues ="", lowValue ="0", highValue ="0", pythonMethod = "pass", methodArg1 = "", methodArg2 = "",
                methodTimeOut = "0", retryTime = "1", runIf = "", tag = "", failStop = "n", requirements = "", softwarePath = ""):
        self.logger = logger
        self.ignore = ignore
        self.testCaseName = testCaseName
        self.test_itemName = testItemName
        self.test_step_name = testStepName
        self.equalValues = equalValues
        self.lowValue = lowValue
        self.highValue = highValue
        self.pythonMethod = pythonMethod
        self.methodArg1 = methodArg1
        self.methodArg2 = methodArg2
        self.methodTimeOut = methodTimeOut
        self.retryTime = retryTime
        self.runIf = runIf
        self.tag = tag
        self.failStop = failStop
        self.requirements = requirements
        self.softwarePath = softwarePath
        self.testResult = False
        self.errorMessage = []
        '''
        Data return after test is executed
        '''
        self.testReturnData = []

    def LogInfo(self,logData):
       self.logger.info(logData)

    def LogWarning(self,logData):
        self.logger.warning(logData)

    def LogError(self,logData):
        self.logger.error(logData)

    def LogCritical(self,logData):
        self.logger.critical(logData)

    def LogDebug(self,logData):
        self.logger.debug(logData)

    def GetJsonData(self):
        return {
            'ignore' : self.ignore,
            'testCaseName' : self.testCaseName,
            'testItemName' : self.test_itemName,
            'testStepName' : self.test_step_name,
            'equalValues' : self.equalValues,
            'lowValue' : self.lowValue,
            'highValue' : self.highValue,
            'pythonMethod' : self.pythonMethod,
            'methodArg1' : self.methodArg1,
            'methodArg2' : self.methodArg2,
            'methodTimeOut' : self.methodTimeOut,
            'retryTime' : self.retryTime,
            'runIf' : self.runIf,
            'tag' : self.tag,
            'failStop' : self.failStop,
            'requirements' : self.requirements,
            'softwarePath' : self.softwarePath,
            'testResult' : self.testResult,
            'errorMessage' : self.errorMessage,
            'testReturnData' : self.testReturnData,
        }