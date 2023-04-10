
from netsquid.components.qprogram import QuantumProgram
from netsquid.protocols import NodeProtocol
from netsquid.components.instructions import INSTR_CNOT,INSTR_H,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits import measure , reduced_dm, create_qubits,operate
import numpy as np
from netsquid.qubits.operators import X,H,CNOT
from random import randint
import time

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb, AssignStatesBydm


key_len = 10

class TP_SenderTeleport(QuantumProgram):
    
    def __init__(self , idx):
        super().__init__()
        self.idx = idx
        
    def program(self):
    #    self.apply(INSTR_MEASURE_BELL,qubit_indices=[0,1], output_key='2',physical=True) # measure BSm



        # EPR-like        
        self.apply(INSTR_CNOT, [0, 1])
        self.apply(INSTR_H, 0) 
        
        self.apply(INSTR_MEASURE,qubit_indices=0, output_key='0',physical=True) # measure the origin state
        self.apply(INSTR_MEASURE,qubit_indices=1, output_key='1',physical=True) # measure the epr1
        

        yield self.run(parallel=False)





class QuantumTeleportationSender(NodeProtocol):
    
    def __init__(self,node,processor,qubits,portNames=["portC_Sender"]): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.qubits=qubits
        self.measureRes=None
        self.portNameCS1=portNames[0]

        self.cqubits = create_qubits(key_len)



        self.processor.put(self.cqubits + self.qubits)
        # self.processor.put(self.qubits + self.cqubits)

        self.key = [randint(0,1) for i in range(key_len)]
        print('------key------ ' , self.key)

        for i in range(key_len):
            self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[1 - self.key[i],1],[1,self.key[i]]])])[0]
            # self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[.4,0.5],[0.5,.6]])])[0]
        
        
        
    def run(self):

        for i in range(key_len):
            start = time.time()

        
            myTP_SenderTeleport=TP_SenderTeleport(i)
            # self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=list(range(2*key_len)))
            self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[i , i + key_len])
            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            
            yield self.await_program(processor=self.processor)
            self.measureRes = [myTP_SenderTeleport.output['0'][0] , myTP_SenderTeleport.output['1'][0]]
            # self.measureRes = [0,0]

            # output2 = myTP_SenderTeleport.output['2'][0]
            # end = time.time()

            # print('time for processing iteration ' , i , end - start , ' sec')

            # # print('out2 ' , output2)
            # # operate(oriQubit, H) # init qubit

            # if output2 == 1:
            #     self.measureRes = [0,1]
            # elif output2 == 3:
            #     self.measureRes = [1,0]
            # elif output2 == 2:
            #     self.measureRes = [1,1]
            print('sends res ' , self.measureRes)
            self.node.ports[self.portNameCS1].tx_output(self.measureRes)

            # print('from sender EPR0' , MeasureByProb(self.cqubits[i]))
            # print('from sender epr1' , MeasureByProb(self.EPR_1))



        
        