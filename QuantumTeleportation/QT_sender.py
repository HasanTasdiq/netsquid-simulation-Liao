
from netsquid.components.qprogram import QuantumProgram
from netsquid.protocols import NodeProtocol
from netsquid.components.instructions import INSTR_CNOT,INSTR_H,INSTR_Z,INSTR_X,INSTR_MEASURE,INSTR_MEASURE_BELL
from netsquid.qubits import measure , reduced_dm, create_qubits,operate
import numpy as np
from netsquid.qubits.operators import X,H,CNOT
from random import randint
import time
import math

import sys
scriptpath = "../lib/"
sys.path.append(scriptpath)
from functions import ProgramFail , MeasureByProb, AssignStatesBydm,MeasureProb


key_len = 10

class TP_SenderTeleport(QuantumProgram):
    
    def __init__(self , idx):
        super().__init__()
        self.idx = idx
        
        
    def program(self):
        # self.apply(INSTR_MEASURE_BELL,qubit_indices=[0,1], output_key='2',physical=True) # measure BSm



        # EPR-like       
         
        if True:
            self.apply(INSTR_CNOT, [0, 1])
            self.apply(INSTR_H, 0) 
            
            self.apply(INSTR_MEASURE,qubit_indices=0, output_key='0',physical=True) # measure the origin state
            self.apply(INSTR_MEASURE,qubit_indices=1, output_key='1',physical=True) # measure the epr1
        # else:
        #     self.apply(INSTR_CNOT, [0, 1])
        #     self.apply(INSTR_MEASURE,qubit_indices=1, output_key='2',physical=True) # measure the origin state

            # if self.retry:
            #     self.apply(INSTR_MEASURE,qubit_indices=0, output_key='2',physical=True) # measure the origin state
            # else:
            #     self.apply(INSTR_MEASURE,qubit_indices=1, output_key='2',physical=True) # measure the origin state

            # self.apply(INSTR_MEASURE,qubit_indices=0, output_key='3',physical=True) # measure the origin state



        yield self.run(parallel=False)



class TP_ResetTeleport(QuantumProgram):
    
    def __init__(self  , res):
        super().__init__()
        self.res = res
        
    def program(self):
        # EPR-like       
        if self.res[0] == 1:
            self.apply(INSTR_Z, 0)
        if self.res[1] == 1:
            self.apply(INSTR_X, 0)


        yield self.run(parallel=False)


class TP_ResetQubit(QuantumProgram):
    
    def __init__(self , idx, retry = False):
        super().__init__()
        self.idx = idx
        self.retry = retry
        
    def program(self):

        self.apply(INSTR_CNOT, [0, 1])
        self.apply(INSTR_MEASURE,qubit_indices=1, output_key='2',physical=True) # measure the origin state


        yield self.run(parallel=False)






class QuantumTeleportationSender(NodeProtocol):
    
    def __init__(self,node,processor,portNames=["portC_Sender"]): 
        super().__init__()
        self.node=node
        self.processor=processor
        self.qubits=self.gen_qubits()
        self.measureRes=None
        self.portNameQS1='portQ_Sender'
        self.portNameQS2='portQ_Sender2'

        self.portNameCS1=portNames[0]
        self.portNameCS2=portNames[1]

        self.cqubits = create_qubits(key_len)



        self.processor.put(self.cqubits + self.qubits)
        # self.processor.put(self.qubits + self.cqubits)

        self.key = [randint(0,1) for i in range(key_len)]
        # self.key = [0,1,0,1 , 0 , 1]
        print('------key------ ' , self.key)

        
        p = .5
        q = .5
        for i in range(key_len):
            a = .6
            b = .4
            if self.key[i] == 1:
                a = .4
                b = .6

            self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[a,1],[1,b]])])[0]

            # if i % 2 == 1:
            #     operate(self.cqubits[i] , H)
            #     # self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[p,1],[1,q]])])[0]

            # p = a
            # q = b

            # if i %2 == 0:
            #     # operate(self.cqubits[i] , H)

            #     self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[1 - self.key[i],1],[1,self.key[i]]])])[0]
            # else:
            #     # operate(self.cqubits[i] , H)
            #     # self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[1 - self.key[i],1],[1,self.key[i]]])])[0]

            #     self.cqubits[i] = AssignStatesBydm([self.cqubits[i]] , [np.array([[.4,0.5],[0.5,.6]])])[0]
        
        
        
    def run(self):
        self.send_qbit()
        mem_flip = False


        for i in range(key_len):
            print("===============================================")
            print("=======================" , i ,"=====================")
            print("===============================================")

            # if i ==1:
            #     break


            start = time.time()
            count = 1
            # print('self.processor.peek(i) before program ' , i , MeasureProb(self.processor.peek(i)) , 'flip:',mem_flip)

            qk_bit = create_qubits(1)
            a = .6
            b = .4
            if self.key[i] == 1:
                a ,b = b , a

            qk_bit = AssignStatesBydm([qk_bit] , [np.array([[a,1],[1,b]])])[0]
            self.processor.put(qk_bit ,  2 * key_len)

            print('sending.................. i:' , i , MeasureProb(self.processor.peek(2*key_len)))
                


            myTP_SenderTeleport=TP_SenderTeleport(i)
            if mem_flip:
                self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[2* key_len , i])
            else:
                self.processor.execute_program(myTP_SenderTeleport,qubit_mapping=[2 * key_len , i + key_len])

            self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
            yield self.await_program(processor=self.processor)


            if True:

                self.measureRes = [myTP_SenderTeleport.output['0'][0] , myTP_SenderTeleport.output['1'][0]]
                print('send res:' , self.measureRes , i)
                time.sleep(.1)
                self.node.ports[self.portNameCS1].tx_output(self.measureRes)
                # print('before reset teleport i:',i , 'mem_flip:' , mem_flip)
                # self.print_qubits( i , count)
                for j in range(i +1 , key_len ):
                    myTP_ResetTeleport=TP_ResetTeleport(self.measureRes)
                    # if j ==i and mem_flip:
                    #     self.processor.execute_program(myTP_ResetTeleport,qubit_mapping=[j])
                    # else:
                    self.processor.execute_program(myTP_ResetTeleport,qubit_mapping=[j + key_len])
                    self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                    yield self.await_program(processor=self.processor)

                
                # print('+++++++ before reset')

                i = i+1

                time.sleep(.1)


                if i < key_len:
                
                    # print('======= in reset')
                    self.prepare_reset_qubit(i)

                    myTP_ResetQubit=TP_ResetQubit(i)
                    self.processor.execute_program(myTP_ResetQubit,qubit_mapping=[i , i + key_len])
                    self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                    yield self.await_program(processor=self.processor)
                    meas = myTP_ResetQubit.output['2'][0]
                    # print('meas at attmpt: ' , count , meas)

                    flip = True    
                    p , q = MeasureProb(self.processor.peek(2 *key_len - 1))
                    print('while p != q and i < key_len' , i)
                    while p != q :


                        if meas == 1:
                            if flip:
                                operate(self.processor.peek(i), X)
                            else:
                                operate(self.processor.peek(i + key_len), X)
                        self.prepare_reset_qubit(i ,not flip , count)


                        myTP_ResetQubit=TP_ResetQubit(i, flip)
                        if flip:
                            self.processor.execute_program(myTP_ResetQubit,qubit_mapping=[i + key_len, i])
                        else:
                            self.processor.execute_program(myTP_ResetQubit,qubit_mapping=[i, i + key_len])

                        self.processor.set_program_fail_callback(ProgramFail,info=self.processor.name,once=True)
                        yield self.await_program(processor=self.processor)
                        meas = myTP_ResetQubit.output['2'][0]
                        p , q = MeasureProb(self.processor.peek(i))
                        if flip:
                            p , q = MeasureProb(self.processor.peek(i + key_len))

                        print('MeasureProb(self.processor.peek(2 *key_len - 1)' , p , q)
                        print('in loop meas at attmpt: ' , count + 1 , meas)

                        flip = not flip

                        count = count +1
                        # if count > 5:
                        #     break
                        # time.sleep(1)
                    if meas == 1:
                        if flip:
                            operate(self.processor.peek(i), X)
                        else:
                            operate(self.processor.peek(i + key_len), X)
                    mem_flip = flip
                    time.sleep(.2)
                    self.node.ports[self.portNameCS1].tx_output('check')
                    print('rrrrrrrrrrrreset at attempt: ' , count)
                i = i-1
                # print('+++++++ after reset mem_flip:',mem_flip)
                # self.print_qubits( i , count)


        # time.sleep(2)
        print('sent key ' , self.key)

    
    
    def print_qubits(self , i , count):
        print('----------- remaining qbits ------------ i: ' , i , 'count:' , count)
        for j in range(0,key_len):
            try:
                print(j , ':' , )
                MeasureByProb(self.processor.peek(j + key_len) , do_print=True)
            except:
                print('exception')
        print('other: 2 * key_len ')
        MeasureByProb(self.processor.peek(2 * key_len) , do_print=True)
        print('other in i  : ' , i)

        MeasureByProb(self.processor.peek(i ) , do_print=True)
        print('------------------------------------')
    def gen_qubits(self):
        qubits=create_qubits(key_len + 1)
        operate(qubits[0] , H)

        for i in range(1 , key_len + 1 ):
            operate([qubits[0] , qubits[i]] , CNOT)
        
        return qubits
    def prepare_reset_qubit(self  , i , for_next = True , num_try = 1):
        
        alpha, beta = MeasureProb(self.processor.peek(i +  (key_len if for_next else 0)))
        # a , b = alpha , beta

        b = alpha /  math.sqrt( alpha + beta)
        a = beta /  math.sqrt( alpha + beta)
        if num_try % 4 == 0:
            # b,a = a,b
            b,a = 0.5 / a , 0.5/b
        qubit=create_qubits(1)
        qubit = AssignStatesBydm([qubit] , [np.array([[a,1],[1,b]])])[0]
        if for_next:
            self.processor.put(qubit , i)
        else:
            self.processor.put(qubit , i + key_len)

    
    def reset_processor_mem(self):
        for i in range(2*key_len):
            self.processor.pop(0)
        self.processor.put(self.cqubits + self.qubits)

    def send_qbit(self):
        qubit = self.processor.pop(2* key_len )
        self.node.ports[self.portNameQS1].tx_output(qubit)

        # qubit = self.processor.pop(2* key_len )
        # self.node.ports[self.portNameQS2].tx_output(qubit)




        
        