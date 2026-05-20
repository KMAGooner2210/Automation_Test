from .test_sequence_item import TestSequenceItem_t
from .test_sequence import TestSequence_t
from .logger import TestLogger

import openpyxl
from openpyxl.utils.cell import get_column_letter
from openpyxl import load_workbook, Workbook
from openpyxl.utils import column_index_from_string

# Start row test sequence
START_ROW = 6

class LoadSequence(object):
    '''
    this class loads a sequence from a workbook to an OBJECT
    '''

    def __init__(self, ExcellPath = 'test_sequence/bst_test_sequence.xlsx', sheetName = None, logger:TestLogger = None) -> None:
        self.ExcellPath = ExcellPath
        #logging.info("Start load the seting data")
        if logger:
            logger.info(f'Start read excell file. {ExcellPath}')
        self.WorkBook = openpyxl.load_workbook(ExcellPath, data_only=True) #Add file name
        self.logger = logger
        logger.info(f'Start read excell file. {self.WorkBook.path}')
        if sheetName:
            self.workSheet = sheetName
        else:
            raise Exception(f'Please specify a sheet name')
        
        #logging.info(f'WORK SHEET LOAD INIT = {workSheet}')

        self.WRoutingTable = self.WorkBook[(self.workSheet)] #select the first sheet
        #ws1 = wb1.active
        mr = self.WRoutingTable.max_row
        mc = self.WRoutingTable.max_column
        #logging.info(f'Max rows = {mr}. Max Column = {mc}')
        #logging.info(f'Read excell file finish')

    def GetCellValueFromTable(self, ColumnName, RowsNumber):
        '''
        Get value of 1 cell in the table.
        
        '''
        Addr = str(ColumnName) + str(RowsNumber)

        return str(self.WRoutingTable[Addr].value) if str(self.WRoutingTable[Addr].value) != "None" else None
    
    def write_value_to_sheet(self, col_name: str, row_index: int, value):
        '''
        write value to the sheet
        '''
        col = column_index_from_string(col_name.upper())
        self.WRoutingTable.cell(row=row_index, column=col).value = value

    def save_to_excel_file(self, Sequence: TestSequence_t, destination_path):
        '''
        save the test sequence to the excel file
        '''
        i = START_ROW
        for item in Sequence.TestSequence:
            self.write_value_to_sheet('A', i, item.ignore)
            self.write_value_to_sheet('B', i, item.testCaseName)
            self.write_value_to_sheet('C', i, item.test_itemName)
            self.write_value_to_sheet('D', i, item.test_step_name)
            self.write_value_to_sheet('E', i, item.equalValues)
            self.write_value_to_sheet('F', i, item.lowValue)
            self.write_value_to_sheet('G', i, item.highValue)
            self.write_value_to_sheet("H", i, item.pythonMethod)
            self.write_value_to_sheet("I", i, item.methodArg1)
            self.write_value_to_sheet("J", i, item.methodArg2)
            self.write_value_to_sheet("K", i, item.methodTimeOut)
            self.write_value_to_sheet("L", i, item.retryTime)
            self.write_value_to_sheet("M", i, item.runIf)
            self.write_value_to_sheet("N", i, item.tag)
            self.write_value_to_sheet("O", i, item.failStop)
            self.write_value_to_sheet("P", i, item.requirements)
            if item.testResult:
                self.write_value_to_sheet("Q", i, "PASS")
            else:
                self.write_value_to_sheet("Q", i, "FAIL")
            i += 1
        
        self.WorkBook.save(destination_path)

    def LoadTestSequence(self):
        '''
        Load all data from excell file to Test Sequence object.,
        Data store to Test Sequence. go get any infor data, define it in the TestSequence Class
        '''
        return self.LoadAllExcellData()
    

    def LoadAllExcellData(self) -> TestSequence_t:
        '''
        Load all data from excell file to TestSequence,
        Data store to TestSequence. go get any infor data, define it in the TestSequence Class
        '''
        # create Routing table object
        Sequence = TestSequence_t(logger=self.logger)
        # Set sequence information
        Sequence.SetTestName(self.GetCellValueFromTable("B",1))
        Sequence.SetVersion(self.GetCellValueFromTable("B",2))
        Sequence.SetSpecVersion(self.GetCellValueFromTable("B",3))
        #

        #logging.info(f'Can1 Name: {CAN1name}. Can2 Name: {CAN2name}. Can3 Name: {CAN3name}. Can4 Name: {CAN4name}. Can5 Name: {CAN5name}. Can6 Name: {CAN6name}. Can7 Name: {CAN7name}. Can8 Name: {CAN8name} ')
        #logging.info(f'Channel {CAN1name} detail information: Channel Name = {self.CAN_channel[CAN1name]["ChannelName"]}, Channel No = {self.CAN_channel[CAN1name]["ChannelNo"]}')

        startRows = START_ROW
        endRows = self.WRoutingTable.max_row + 1
        #
        Sequence.ClearSequence()
        LastTestCaseName = ""
        LastTestItemName = ""
        #
        #
        for i in range(startRows,endRows):
            ignore = self.GetCellValueFromTable('A',i)
            testCaseName = self.GetCellValueFromTable('B',i)
            testItemName = self.GetCellValueFromTable('C',i)
            testStepName = self.GetCellValueFromTable('D',i)
            if testStepName and len(testStepName) > 0:
                equals = self.GetCellValueFromTable('E',i)
                lowValue = self.GetCellValueFromTable('F',i)
                highValue = self.GetCellValueFromTable('G',i)
                pythonMethod = self.GetCellValueFromTable("H",i)
                methodArg1 = self.GetCellValueFromTable("I",i)
                methodArg2 = self.GetCellValueFromTable("J",i)
                methodTimeOut = self.GetCellValueFromTable("K",i)
                retryTime = self.GetCellValueFromTable("L",i)
                runIf = self.GetCellValueFromTable("M",i)
                tag = self.GetCellValueFromTable("N",i)
                failStop = self.GetCellValueFromTable("O",i)
                requirements = self.GetCellValueFromTable("P",i)
                #
                if testCaseName == None or len(testCaseName) == 0:
                    if len(LastTestCaseName) > 0:
                        testCaseName = LastTestCaseName
                    else:
                        raise Exception(f'Test case name can not empty. test case name empty at line {str(i)}')
                
                if testItemName == None or len(testItemName) == 0:
                    if len(LastTestItemName) > 0:
                        testItemName = LastTestItemName
                    else:
                        raise Exception(f'Test item name can not empty. test item name empty at line {str(i)}')
                    
                if equals == None or len(equals) == 0:
                    if (lowValue == None or len(lowValue) == 0) or (highValue == None or len(highValue) == 0):
                        raise Exception(f'You must provide equal or lowValue and highValue')

                softwarePath = self.GetCellValueFromTable('D',1)    
                Sequence.addSequence(TestSequenceItem_t(logger= self.logger, ignore=ignore, testCaseName=testCaseName, 
                                                        testItemName=testItemName, testStepName=testStepName, equalValues=equals,
                                                        lowValue=lowValue, highValue=highValue, pythonMethod=pythonMethod,
                                                        methodArg1=methodArg1, methodArg2=methodArg2,methodTimeOut=methodTimeOut,
                                                        retryTime=retryTime, runIf=runIf, tag=tag, failStop=failStop, requirements=requirements,
                                                        softwarePath=softwarePath))

                LastTestCaseName = testCaseName
                LastTestItemName = testItemName

        return Sequence

    def TestExcell(self):

        # Data can be assigned directly to cells
        #logging.info(self.GetCellValueFromTable(self.ExcellMap["CAN_ID"],3205))
        pass

