#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# OpenBCI - framework for Brain-Computer Interfaces based on EEG signal
# Project was initiated by Magdalena Michalska and Krzysztof Kulewski
# as part of their MSc theses at the University of Warsaw.
# Copyright (C) 2008-2009 Krzysztof Kulewski and Magdalena Michalska
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author:
#     Mateusz Kruszyński <mateusz.kruszynski@gmail.com>
#

import os
import time
import state_machine
import speller_graphics_manager as sgm
MAGIC = 8



class LogicSpellerEngine(object):
    """The most important class in logic module. It impelements a real logic.
    Important objects stored on slots are:
    - _state_machine - an object responsible for maintaining states traverse
    operations and storing/updating config data from config file.
    - _server - an object that transfers data to and from other obci modules.
    """
    def __init__(self, p_server):
        """Set instance variables, send to ugm current gui.
        p_server is an object to communicate with ugm and other modules.
        """
        self._server = p_server
        self._state_machine = state_machine.StateMachine() 
        #TODO - here above we could pass config_file_name

        #self.num_of_freq = int(self._server.get_message(
        #        {'message':'NumOfFreq',
        #         'type':'dict_get_request_message'}))
        #TODO - shouldn`t WE set numOfFreq in hashtable here?
        self._menu_state = [0, 0, 0]
        self._paradigm = 0
        # for now: 0: ssvep, 1: p300
        self._message = ''
        self._pause = 0
        self._pause_point = time.time()
        self._server.send_message({'value':' ', 'type':'switch_mode'})
        self._update_global_gui()

    # --------------------------------------------------------------------------
    # ---------------- public interface for self._server -----------------------

        
    def handle_decision(self, p_decision_object):
        """A public method for self._server, so the only way 'the world' sends
        to us some messages.
        The method is fired when a decision has been made by the user.
        """
        l_decision = p_decision_object.decision 
        if (p_decision_object.type == self._paradigm): 
            if self._pause != 1:
                self._pause_point = time.time()
                # Update dynamic main menu state if current state is initial state.      
                if self._state_machine.get_current_state() == 0:
                    self._update_main_menu(l_decision)
                
                self._update_message(l_decision)
                    
                # Fire an action for current state and current decision
                l_action = self._compute_current_actions()[l_decision]
                if l_action: #if l_action is not an empty string
                    eval("".join(["self.", l_action]))
                    
                # Go to next state...
                self._state_machine.set_next_state(l_decision)
                
                # Send updated gui info to ugm...
                self._update_global_gui()

                if (l_decision == MAGIC):
                    self._update_global_paradigm()
                self._server.send_message({'value':' ', 
                                           'type': 'switch_mode'}) 
                #TODO - why do we need this above?
            elif (time.time() - self._pause_point > 4):
                self._pause = 0


    # --------------------------------------------------------------------------
    # ------------------ actions available in config ---------------------------
    def run_ext(self, p_program_string):
        """Run external program p_program_string."""
        os.system(p_program_string)

    def backspace(self):
        """Run backspace action -> truncate self._message.
        A place where this action is defined to be fired
        is speller config file.
        """
        self._message = self._message[:len(self._message) - 1]

    def say(self):
        """Run say action -> run external program with self._message
        as a paramtere.
        A place where this action is defined to be fired
        is speller config file.
        """
        #run_ext('milena '+self._message)
        pass
    
    def solve_menu(self, p_menu_id):
        """For given main menu id p_menu_id (this is the menu in state 0)
        return an index of graphics to be displayed in ugm.
        """
        return self._menu_state[p_menu_id]

    # ------------------ actions available in config ---------------------------
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # ---------- methods that use self._server to perform some updates ---------
    def _update_global_gui(self):
        """Sent to self._server current logic data:
        - current message,
        - current gui graphics
        """
        self._server.send_message({'value':self._message,
                                   'key':'Message',
                                   'type':'dict_set_message'})
        # Get a collection of strings representing current state`s graphics.
        l_graphics = self._compute_current_graphics()
        # Pack it to string ...
        l_graphics_string = sgm.SpellerGraphicsManager().pack(l_graphics)
        self._server.send_message({
                'value':l_graphics_string,
                'key':'Panel',
                'type':'dict_set_message'})

    def _update_global_paradigm(self):
        """Update locally stored paradigm code and send 
        updated paradigm to self._server.
        """
        if self._paradigm == 0:
            self._paradigm = (-1) * (self._paradigm - 1)
        l_value = ''
        if self._paradigm == 0:
            l_value = "SSVEP"
        else:
            l_value = "P300"
        self._server.send_message({'value':l_value,
                                   'key':'BlinkingMode',
                                   'type':'dict_set_message'})



    # ---------- methods that use self._server to perform some updates ---------
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # ---------- methods for config updates and other updates  -----------------

    def _update_main_menu(self, p_decision):
        """Update locally stored menu_state. The method is fired
        when we are in 0 state and p_decision has been made by the user.
        """
        try:
            self._menu_state[p_decision] = (self._menu_state[p_decision] + 1) % 2
        except IndexError:
            # In case p_decision is not about dynamic main menu, eg.
            # we have some other actions available from state 0 that are
            # not dynamic like main menu.
            pass

    def _update_message(self, p_decision):
        """Update stored message considering:
        - current system state,
        - p_decistion - a decision made by the user
        """
        l_sign = self._state_machine.get_current_state_param('signs')[p_decision]
        ''.join([self._message, l_sign])

    def _compute_current_actions(self):
        """Return collection of strings representing current`s state actions. 
        See _compute_current_param for details.
        """
        return self._compute_current_param('actions', 'actions_solver')
    def _compute_current_graphics(self):    
        """Return collection of strings representing current`s state graphics. 
        See _compute_current_param for details.
        """
        return self._compute_current_param('graphics', 'graphics_solver')
    def _compute_current_param(self, p_param, p_param_solver):
        """Return a collection of strings representing ... someting ...
        depending on p_param.
        The method is used by two methods:
        - _compute_current_graphics
        - _compute_current_actions.
        The point is that we have p_param in config as a collection of objects.
        By now two situations might occur:
        1) all elements in config are strings
        2) some elements in config are collections.
        If we have string it`s cool - we just return strings.
        If we have collection, a string to be returned must be computed.
        We use p_param_solver config parameter to get what we want.
        p_param_solver is a collection of string representing methods
        that allow to decide which element from p_param`s collection
        is now CURRENT.
        """
        l_config_param = self._state_machine.get_current_state_param(p_param)
        l_current_param = [""]*len(l_config_param)
        #Above a collection to be filled from l_config_param and returned.
        l_curr_state = self._state_machine.get_current_state()
        for i_index, i_elem in enumerate(l_config_param):
            # Below a tricky (= FAST) method to test if an object
            # is a collection or string. More often it`ll be string
            # so we 'try' to test it as it were string.
            try:
                i_elem + '' #test if i_gr_elem is a string
            except TypeError: #i_gr_elem is a sequence
                # Get a collection of strings representing methods
                # that resolve current state`s param
                l_solvers = self._state_machine.get_state_param(l_curr_state, p_param_solver)
                # Set current param to a chosen element from config
                l_str_method = "".join(["self.", l_solvers[i_index]])
                l_current_param[i_index] = l_config_param[i_index][eval(l_str_method)]
            else: # We have string in config so just copy it ...
                l_current_param[i_index] = l_config_param[i_index]
        return l_current_param
        
    # ---------- methods for config updates and other updates  -----------------
    # --------------------------------------------------------------------------


#TODO 
# - napisac testy

#kto ustawia numOfFreq?
#ocb z tym pausepoint?