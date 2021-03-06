# -*- coding: utf-8 -*-
#!/usr/bin/env python
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
#     Anna Chabuda <anna.chabuda@gmail.com>
#

import os.path, thread, time

from maze_logic import MazeLogic
from maze_wii_logic import MazeWiiLogic
from tags.tagger import Tagger

from obci.exps.ventures.data import data_manager
from obci.exps.ventures import logic_queue

class MazeGame(logic_queue.LogicQueue):
    def __init__(self, user_id, session_type='experiment', session_duration=30*60, motor_min_level=-20.0, motor_max_level=-10.0, time_board_display=5, 
                 time_left_out=30, tag_name='', tag_dir='./'): #motor_step=5, motor_initial=-3,
        super(MazeGame, self).__init__()
        self.user_id = user_id
        self.session_number = data_manager.session_number_get(self.user_id)
        self.session_condition = data_manager.session_type_get(self.user_id)
        self.session_type = session_type
        self.session_duration = session_duration
        self.time_board_display = time_board_display
        #self.wii_level_param = {'motor_step':motor_step, 'motor_initial':motor_initial}
        self.wii_level_param = {'motor_min_level':motor_min_level, 'motor_max_level':motor_max_level}
        self.time_left_out = time_left_out
        self.tagger_init(tag_name, tag_dir)

    def tagger_init(self, tag_name, tag_dir):
        if  self.session_type == 'experiment':#'ventures_game':
            self.tagger = Tagger(tag_name, tag_dir, status='ON')
        else:#should be ventures_game_training
            self.tagger = Tagger(tag_name, tag_dir, status='OFF')

    def _get_start_info(self, user_name):
        return self.user_data_parser.get_user_trening_data(user_name)

    def _get_wii_levels_params(self):
        data = data_manager.calibration_2_get_last(self.user_id)
        wii_level_param = {direction:int(value) for direction, value in zip(['up', 'right', 'down', 'left'], data)}
        #wii_level_param['session_number'] = self.session_number
        self.wii_level_param.update(wii_level_param)
        return self.wii_level_param

    def run(self):
        if self.session_type == 'experiment':
            level = data_manager.maze_current_level_get_last(self.user_id)
        else:
            level = 1

        if self.session_condition in ['cognitive', 'key_motor']:
            game = MazeLogic(level, 
                             self.session_number, 
                             self.session_duration, 
                             self.time_board_display, 
                             self.time_left_out, 
                             self.tagger, 
                             self.session_type,
                             self.session_condition,
                             )

        elif self.session_condition == 'motor':
            game = MazeWiiLogic(level,
                                self._get_wii_levels_params(),
                                self.session_number, 
                                self.session_duration, 
                                self.time_board_display, 
                                self.time_left_out, 
                                self.tagger, 
                                self.session_type, 
                                self.session_condition,
                                self)

        elif self.session_condition == 'cognitive_motor':
            game = MazeWiiLogic(level,
                                self._get_wii_levels_params(),
                                self.session_number, 
                                self.session_duration, 
                                self.time_board_display, 
                                self.time_left_out, 
                                self.tagger, 
                                self.session_type, 
                                self.session_condition,
                                self)
        game.main()
        if self.session_type=='experiment':
            if self.session_condition in ['cognitive_motor', 'motor']:
                data_manager.wii_current_level_set(self.user_id, *game.get_current_wii_levels())
            data_manager.maze_current_level_set(self.user_id, game.get_current_level())

def test_maze():
    a = MazeGame('1')
    thread.start_new_thread(a.run, ())
    x = 0
    while True:
        a.handle_message((2, x%100))
        x += 1
        for i in range(10000):
            i
	if x % 5 == 0:
	    for i in range(5):
		a.get_message()

def run_maze():
    a = MazeGame('test_cognitive')
    a.run()
    
if __name__ == '__main__':
    run_maze()
