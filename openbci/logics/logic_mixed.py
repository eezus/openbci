#!/usr/bin/env python

import numpy, cPickle, os, time, sys, random, settings, time, variables_pb2
from array import array
from multiplexer.multiplexer_constants import peers, types
from multiplexer.clients import BaseMultiplexerServer, connect_client


class SpellerLogic(BaseMultiplexerServer):
    
    # states:  
    # -1: drops all messages

    def increaseChannel(self):
        self.channel += 1
        self.message = str(self.channel)

    def decreaseChannel(self):
        self.channel -= 1
        self.message = str(self.channel)

    def backspace(self):
        self.message = self.message[:len(self.message) - 1]

    def __init__(self, addresses):
        super(SpellerLogic, self).__init__(addresses=addresses, type=peers.LOGIC)
        self.numOfFreq = int(self.conn.query(message = "NumOfFreq", type = types.DICT_GET_REQUEST_MESSAGE, timeout = 1).message)
        screens = 8
        decisions = 8
        self.state = 0
        fields = 5
	self.state1 = 0
    	self.state2 = 0
    	self.state3 = 0
 

        self.menu_help1 = ["light on", "light off"]
        self.menu_help2 = ["music on", "music off"]
        self.menu_help3 = ["power on", "power off"]

	self.param_help1 = ['tahoe  "power on 1 \n\r"', 'tahoe  "power off 1 \n\r"']
        self.param_help2 = ['tahoe  "power on 2 \n\r"', 'tahoe  "power off 2 \n\r"']
        self.param_help3 = ['tahoe  "power on 3 \n\r"', 'tahoe  "power off 3 \n\r"']


        # graph of menus
        self.screen = screens * [decisions * [0]]
        #                 0  1  2  3  4  5  6  7  
        self.screen[0] = [0, 0, 0, 1, 0, 0, 0, 0]
        self.screen[1] = [1, 2, 3, 4, 5, 6, 0, 7]
        self.screen[2] = [2, 2, 2, 2, 2, 2, 2, 1]
        self.screen[3] = [3, 3, 3, 3, 3, 3, 3, 1]
        self.screen[4] = [4, 4, 4, 4, 4, 4, 4, 1]
        self.screen[5] = [5, 5, 5, 5, 5, 5, 5, 1]
        self.screen[6] = [6, 6, 6, 6, 6, 6, 6, 1]
        self.screen[7] = [7, 7, 7, 7, 7, 7, 7, 1]
        self.channel = 0

        self.action = screens * [decisions * ['']]

        # panel grphics[i] will be presented on screen in state i
        self.graphics = screens * [""]
        #self.graphics[0] = "| Light on :: | Fan on :: | on :: |  Speller :: | Light off :: | Fan off  :: | off  :: | P300 "
	self.graphics[0] = "|" + self.menu_help1[self.state1] + " :: | " + self.menu_help2[self.state2]  + " :: | " + self.menu_help3[self.state3]  + ":: |  Speller :: |  :: |   :: |  :: |  "


        self.graphics[1] = " | < :: | n i e ' ' a f :: | p r o w t l :: | c z h s y b :: | m d k j u g :: | say :: | koniec:: | main' ' ."
        self.graphics[2] = " | < :: | N :: | I :: | E :: | ' ' :: | A :: | F :: | back "
        self.graphics[3] = " | < :: | P :: | R :: | O :: | W :: | T :: | L :: | back "
        self.graphics[4] = " | < :: | C :: | Z :: | H :: | S :: | Y :: | B :: | back "
        self.graphics[5] = " | < :: | M :: | D :: | K :: | J :: | U :: | G :: | back "
        self.graphics[6] = " | < :: | say :: | V :: | W :: | X :: | Y :: | Z :: | back "
        self.graphics[7] = " | < :: | say :: | . :: | , :: | ' ' :: |  :: | :: | back "
	
	#self.graphics[0] = "| Light on :: | Fan on :: | on :: |  Speller :: | Light off :: | Fan off  :: | off  :: | P300 "

        #self.graphics[1] = " | < :: | A B C D E :: | F G H I J:: | K L M N O :: | P R S T U:: | V W X Y Z :: | main:: | ' ' ."
        #self.graphics[2] = " | < :: | say :: | A :: | B :: | C :: | D :: | E :: | back "
        #self.graphics[3] = " | < :: | say :: | F :: | G :: | H :: | I :: | J :: | back "
        #self.graphics[4] = " | K :: | L :: | M ::  | del ::  | N ::  | O ::  | say ::  | <- "
        #self.graphics[5] = " | < :: | say :: | P :: | R :: | S :: | T :: | U :: | back "
        #self.graphics[6] = " | < :: | say :: | V :: | W :: | X :: | Y :: | Z :: | back "
        #self.graphics[7] = " | < :: | say :: | . :: | , :: | ' ' :: |  :: | :: | back "
	

	
        self.signs = screens * [decisions * [""]]
        
        # string signs[i][j] will be added to message in state i when person is looking at square j
        # if you wish no sign to be added leave it empty
        self.signs[0] = ['', '', '', '', '', '', '', '']
        self.signs[1] = ['', 'N', 'I', 'E', ' ', 'A', 'F', ''] # taki smiec, ale potrzebny
        self.signs[2] = ['', 'N', 'I', 'E', ' ', 'A', 'F', '']
        self.signs[3] = ['', 'P', 'R', 'O', 'W', 'T', 'L', '']
        self.signs[4] = ['', 'C', 'Z', 'H', 'S', 'Y', 'B', '']
        self.signs[5] = ['', 'M', 'D', 'K', 'J', 'U', 'G', '']
        self.signs[6] = ['', '', '', '', '', '', '', '']
        self.signs[7] = ['', '', '', '', '', '', '', '']

	#self.signs[0] = ['', '', '', '', '', '', '', '']
        #self.signs[1] = ['', '', 'A', 'B', 'C', 'D', 'E', ''] # taki smiec, ale potrzebny
        #self.signs[2] = ['', '', 'A', 'B', 'C', 'D', 'E', '']
        #self.signs[3] = ['', '', 'F', 'G', 'H', 'I', 'J', '']
        #self.signs[4] = ['K', 'L', 'M', '', 'N', 'O', '', '']
        #self.signs[5] = ['', '', 'P', 'R', 'S', 'T', 'U', '']
        #self.signs[6] = ['', '', 'V', 'W', 'X', 'Y', 'Z', '']
        #self.signs[7] = ['', '', '.', ',', ' ',  '',  '', '']



        # action[i][j] will be performed in state i when person is looking on square j
        # if you wish no action - leave it emptyOA
        self.action = screens * [decisions * [""]]
        #self.action[0] = ['', '', '', 'python programDawida', '', '', 'python programDawida', '']
        self.action[0] = ['tahoe  "power on 1 \n\r"', ' tahoe "power on 2 \n\r"', '', '', 'tahoe "power off 1 \n\r"', ' tahoe "power off 2 \n\r"', '', '']
        self.action[1] = ['', '', '', '', '', 'milena_say', '', ''] 
        self.action[2] = ['', '', '', '', '', '', '', '']
        self.action[3] = ['', '', '', '', '', '', '', '']
        self.action[4] = ['', '', '', '', '', '', '', '']
        self.action[5] = ['', '', '', '', '', '', '', '']
        self.action[6] = ['', '', '', '', '', '', '', '']
        self.action[7] = ['', '', '', '', '', '', '', '']



        # function[i][j] : function to be dynamically called in state i when person looks at sq j

        self.function = screens * [decisions * [""]]
        #self.function[0] = ['', '', '', 'self.increaseChannel', '', '', 'self.decreaseChannel', '']
        self.function[0] = ['', '', '', '', '', '', '', '']
        self.function[1] = ['self.backspace', '', '', '', '', '', '', ''] 
        self.function[2] = ['self.backspace', '', '', '', '', '', '', '']
        self.function[3] = ['self.backspace', '', '', '', '', '', '', '']
        self.function[4] = ['self.backspace', '', '', '', '', '', '', '']
        self.function[5] = ['self.backspace', '', '', '', '', '', '', '']
        self.function[6] = ['self.backspace', '', '', '', '', '', '', '']
        self.function[7] = ['self.backspace', '', '', '', '', '', '', '']

        # params[i][j] : parameters with which action[i][j] will be called

        self.params = screens * [decisions * [""]]
        # self.params[0] = ['', '', '', 'self.channel', '', '', 'self.channel', '']
        self.params[0] = ['power on 1 \n\r', 'power on 2 \n\r', '', '', 'power off 1 \n\r', 'power off 2 \n\r', '', '']
        self.params[1] = ['', '', '', '', '', 'self.message', '', ''] 
        self.params[2] = ['', '', '', '', '', '', '', '']
        self.params[3] = ['', '', '', '', '', '', '', '']
        self.params[4] = ['', '', '', '', '', '', '', '']
        self.params[5] = ['', '', '', '', '', '', '', '']
        self.params[6] = ['', '', '', '', '', '', '', '']
        self.params[7] = ['', '', '', '', '', '', '', '']

        self.paradigm = 0
        # for now: 0: ssvep, 1: p300
        self.magic = 8 
        self.message = ''
        self.pause = 0
        self.pausePoint = time.time()
        self.panelVar = variables_pb2.Variable()
        self.messageVar = variables_pb2.Variable()
        self.conn.send_message(message = " ", type = types.SWITCH_MODE, flush = True)

    def handle_message(self, mxmsg):
        if (mxmsg.type == types.DECISION_MESSAGE):
            dec = variables_pb2.Decision()
            dec.ParseFromString(mxmsg.message)
            decision = dec.decision 
            if (dec.type == self.paradigm): 
             
                if self.pause != 1:
                    self.pausePoint = time.time()
                    #self.pause = 1
                                        
                    
		    if self.state == 0:
                        if decision == 0:
                            self.state1 = (self.state1 + 1) % 2
                        if decision == 1:
                            self.state2 = (self.state2 + 1) % 2
                        if decision == 2:
                            self.state3 = (self.state3 + 1) % 2
			self.graphics[0] = "|" + self.menu_help1[self.state1] + " :: | " + self.menu_help2[self.state2]  + " :: | " + self.menu_help3[self.state3]  + ":: |  Speller :: |  :: |   :: |  :: |  "    

			#self.action[0] = [self.param_help1[self.state1], self.param_help2[self.state2], self.param_help3[self.state3], '', '', '', '', '']

		    if (len(self.signs[self.state][decision]) > 0):
                        self.message = self.message + self.signs[self.state][decision]

                    if (len(self.function[self.state][decision]) > 0):
                        eval(self.function[self.state][decision])()
                    

                    if (len(self.action[self.state][decision]) > 0):
			#test = self.action[self.state][decision] + " " + str(eval(self.params[self.state][decision]))
			#print test
			#os.system(self.action[self.state][decision] + " " + str(eval(self.params[self.state][decision])))
			if (self.state >= 2 ):
				os.system(self.action[self.state][decision] + " " + str(eval(self.params[self.state][decision])))
			else:
        	                os.system(self.action[self.state][decision]) # + " " + str(eval(self.params[self.state][decision])))
               
                    self.action[0] = [self.param_help1[self.state1], self.param_help2[self.state2], self.param_help3[self.state3], '', '', '', '', '']


                    self.messageVar.key = "Message"
                    self.messageVar.value = self.message
                    self.conn.send_message(message = self.messageVar.SerializeToString(), type = types.DICT_SET_MESSAGE, flush=True)
                    self.state = self.screen[self.state][decision]
                    self.panelVar.key = "Panel"
                    self.panelVar.value = self.graphics[self.state]
                
                    self.conn.send_message(message = self.panelVar.SerializeToString(), type = types.DICT_SET_MESSAGE, flush = True)
                    if (decision == self.magic):
                        self.messageVar.key = "BlinkingMode"
                        if self.paradigm == 0:
                            self.paradigm = (-1) * (self.paradigm - 1)
                        if self.paradigm == 0:
                            self.messageVar.value = "SSVEP"
                        else:
                            self.messageVar.value = "P300"
                        #print "NEW MODE: " + self.messageVar.value
                        self.conn.send_message(message = self.messageVar.SerializeToString(), type = types.DICT_SET_MESSAGE, flush = True)
                        #self.conn.send_message(message = self.mode#sar.SerializeToString(), type = types.DICT_SET_MESSAGE, flush = True)
                    self.conn.send_message(message = " ", type = types.SWITCH_MODE, flush = True)
                    
                    #print "SWITCH MODE"
                    

                elif (time.time() - self.pausePoint > 4):
                    self.pause = 0
         
        self.no_response() 

if __name__ == "__main__":
        SpellerLogic(settings.MULTIPLEXER_ADDRESSES).loop()
 