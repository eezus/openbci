#!/usr/bin/env python
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
#      ukasz Polak <l.polak@gmail.com>
#      Joanna Tustanowska <asia.tustanowska@gmail.com>
#
"""Holds Experiment_manager class:
This class is responsible for managing UGM experiments. It loads and holds configs
of those experiments and makes it possible to run them"""

from ugm.ugm_config_manager import UgmConfigManager
from experiment_builder.config.config import USE_MULTIPLEXER 

import ConfigParser
import random
import time
import sys
import os.path
from openbci.tags import tagger

TAGGER = tagger.get_tagger()

# We must check if we are running this script directly, and if we do,
# then perhaps command-line option overriden config
print (len(sys.argv), sys.argv)
config_file_name = None
if len(sys.argv) >= 2 and sys.argv[0].find('experiment_manager.py') >= 0 :
    if sys.argv[1] == 'mx-on':
        USE_MULTIPLEXER = True
    elif sys.argv[1] == 'mx-off':
        USE_MULTIPLEXER = False
    if len(sys.argv) >= 3:
        config_file_name = sys.argv[2]

if USE_MULTIPLEXER:
    from multiplexer.multiplexer_constants import peers, types
    from multiplexer.clients import connect_client
    import variables_pb2
    from data_storage import signal_saver_control

import experiment_logging
LOGGER = experiment_logging.get_logger('experiment_manager', 'debug')

class Experiment_manager(object):
    """This class is responsible for managing UGM experiments. It loads and holds configs
    of those experiments and makes it possible to run them"""
    def __init__(self, p_config_name=None):
        super(Experiment_manager, self).__init__()
        self.config_file = self.read_experiment_config(p_config_name)
        print self.config_file
        self.screens = self.config_file['screens']
        self.sc_configs = []
        self.repeats = self.config_file['repeats']
        self.readable_names = self.config_file['readable_names']
        self.programme = self.config_file['file_to_run'] 

        # set up screens configuration - pair screens with diode freqs
        if not self.config_file.get('USE_DEFAULT_FREQS'):
            self.freq_sets = self.config_file['freqs']
	    print "UWAGA"
	    print ""
	    print ""
	    print self.screens
	    print len(self.screens)
	    print self.freq_sets
	    print len(self.freq_sets)
            assert(len(self.screens) == len(self.freq_sets))
            self.sc_configs = [zip(scr, fre) for scr, fre in zip(self.screens,
                self.freq_sets)]
        else:
            def_freqs = self.config_file['DEFAULT_FREQS']
            assert(def_freqs != None)
            self.sc_configs = [zip(scr, def_freqs) for scr in self.screens]

        LOGGER.info("screens and freqs: \n" + \
                str(self.sc_configs))

        self._prepare_screens(self.sc_configs)

        LOGGER.debug("SHUFFLED screens and freqs: \n" + \
                str(self.sc_configs))

        self._delay = self.config_file['delay']
        self._last_delay = None
        try:
            self._delay + 0
            # No error, delay is not random, just a number
            self._rand_delay = False
        except TypeError:
            self._rand_delay = True

        self.config_manager = UgmConfigManager()
        self._connection = None
        self._screen_sounds = self.config_file.get('sounds', None)
        self._field_look_nums = self.config_file.get('field_look_nums',None)

        if self._field_look_nums != None:
            self._sc_look_index = 0
        else:
            self._screen_look_num = 0

        if self._screen_sounds:
            import pygame
            import settings
            pygame.init()
            for i, s in enumerate(self._screen_sounds):
                self._screen_sounds[i] = os.path.join(
                    settings.module_abs_path(), 
                    self._screen_sounds[i])
        

    def _prepare_screens(self, p_sc_set):
        """ Shuffle screens in each pack """
        for i_nr in range(len(p_sc_set)):
            l_original_screens = p_sc_set[i_nr]
            if not self.config_file.get('shuffle', True):
                l_current_screens = l_original_screens*self.repeats
            elif len(l_original_screens) > 2:
                l_current_screens = []
                l_last_screen = None
                for i_iterations in range(self.repeats):
                    random.shuffle(l_original_screens)
                    if l_original_screens[0] == l_last_screen:
                        l_tmp = l_original_screens[0]
                        l_original_screens[0] = l_original_screens[1]
                        l_original_screens[1] = l_tmp
                    l_last_screen = l_original_screens[-1]
                    l_current_screens += l_original_screens
            else:
                l_current_screens = p_sc_set[i_nr] * self.repeats
                random.shuffle(l_current_screens)
            p_sc_set[i_nr] = l_current_screens
        if self.config_file.get('shuffle', True):
            # shuffle screen packs
            random.shuffle(p_sc_set)
            


    def run(self):
        self.send_hi_screen()
        
        if USE_MULTIPLEXER:
            l_saver_control = signal_saver_control.SignalSaverControl()
            l_saver_control.start_saving()
        
        l_time = time.time()
        TAGGER.send_tag(l_time, l_time, "experiment_start",
                {
                    "exp_config" : self.config_file
                    })

        for i_screens_pack in self.sc_configs:
            # a pack is a list of tuples (screen + [diode freqs])
            self._pre_screen_package(i_screens_pack)
            LOGGER.debug("PACK: \n" + str(i_screens_pack))
            for i_screen_conf in i_screens_pack:
                l_delay = self._get_delay()
                self._pre_screen(i_screen_conf)
		# perform some action, like executing other stimuli than visual
                if self.programme != '':
		    os.system("python " + self.programme)
                # let ugm read config for new screen...
                self.config_manager.update_from_file(i_screen_conf[0], True)
                # ...then update itself
                self.send_to_ugm()
                # change diode frequencies 
                self.update_diode_freqs(i_screen_conf[1])

                time.sleep(l_delay)
                self._post_screen(i_screen_conf)

            self._post_screen_package(i_screens_pack)


        self.send_bye_screen()
        l_time = time.time()
        TAGGER.send_tag(l_time, l_time, "experiment_end", {})

        if USE_MULTIPLEXER:
            l_saver_control.finish_saving()

    def send_hi_screen(self):
        l_sc = self.config_file['hi_screen']
        l_sc_del = self.config_file['hi_screen_delay']
        if l_sc:
            self._send_simple_screen(l_sc, 'experiment_hi', l_sc_del)
            time.sleep(l_sc_del)

    def send_bye_screen(self):
        l_sc = self.config_file['bye_screen']
        l_sc_del = self.config_file.get('bye_screen_delay',0)
        if l_sc:
            self._send_simple_screen(l_sc, 'experiment_bye', l_sc_del)
            time.sleep(l_sc_del)
    
    def _send_simple_screen(self, p_screen, p_tag_name, p_delay):
        self.config_manager.update_from_file(p_screen, True)
        self.send_to_ugm()
        l_time = time.time()
        TAGGER.send_tag(l_time, l_time, p_tag_name, 
                        {
                "delay" : p_delay
                })

    def send_to_ugm(self):
        if USE_MULTIPLEXER:
            l_type = 0
            l_msg = variables_pb2.UgmUpdate()
            l_msg.type = int(l_type)
            l_msg.value = self.config_manager.config_to_message()
          	      
            # Everything done :) All that is left is to establish connection if needed...
            if not self._connection:
                self._connection = connect_client(type = peers.LOGIC)
            # ...and send message to UGM
            self._connection.send_message(
                message = l_msg.SerializeToString(), 
                type=types.UGM_UPDATE_MESSAGE, flush=True)
        else:
            self.config_manager.update_to_file('ugm_config', True)

    def update_diode_freqs(self, p_freqs):
        l_freq_str = p_freqs
        if not isinstance(p_freqs, basestring):
            l_freq_str = " ".join(['%s' % i for i in p_freqs])

        if USE_MULTIPLEXER:
            l_msg = variables_pb2.Variable()
            l_msg.key = "Freqs"
            l_msg.value = l_freq_str

            # Everything done :) All that is left is to establish connection if needed...
            if not self._connection:
                self._connection = connect_client(type = peers.LOGIC)
            # ...and send message to diode control
            self._connection.send_message(
                message = l_msg.SerializeToString(), 
                type=types.DIODE_UPDATE_MESSAGE, flush=True)
    
    def _get_delay(self):
        ret = None
        if self._rand_delay:
            ret = self._delay[0] + random.random()*(self._delay[1]-self._delay[0])
        else:
            ret = self._delay
        self._last_delay = ret
        LOGGER.debug("Computed stimulus delay: "+str(ret))
        return ret

    def _pre_screen_package(self, p_screen_package):
        print('New screen package: ' + str(p_screen_package))
        if self._field_look_nums != None:
            self._sc_look_index = 0
        else:
            self._screen_look_num = 0
        
    def _post_screen_package(self, p_screen_package):
        if self.config_file['make_package_breaks']:
            self.update_diode_freqs(self.config_file['break_package_freqs'])
            l_delay = self.config_file['break_package_len']
            self._send_simple_screen(self.config_file['break_package_screen'],
                                     'experiment_package_break', l_delay)
            time.sleep(l_delay)
    
    def _pre_screen(self, p_screen_config):
        print('New screen: ' + str(p_screen_config[0]))
        # TODO: wybieranie pola do koncentracji, dzwiek oznajmiajacy o tym, zapis do tagu
        self._play_sound()
        if self._screen_sounds != None:
            self._screen_look_num = (self._screen_look_num + 1) % \
                    len(self._screen_sounds)
        elif self._field_look_nums != None:
            self._screen_look_num = self._field_look_nums[self._sc_look_index]
            

        l_screen_config_name = p_screen_config[0]

        if l_screen_config_name in self.readable_names:
            l_screen_name = self.readable_names[l_screen_config_name]
        else:
            l_screen_name = l_screen_config_name
        
        l_time = time.time()
        TAGGER.send_tag(l_time, l_time, "experiment_update", 
                        {
                            "concentrating_on_field" : self._screen_look_num,
                            "screen" : l_screen_name,
                            "Freqs" : p_screen_config[1],
                            "delay" : self._last_delay 
                        }) 
        LOGGER.info('screen ' + str(p_screen_config[0]) + '  freqs: ' +\
                        str(p_screen_config[1]) + ' delay: '+ str(self._last_delay))

    
    def _post_screen(self, p_screen_config):
        # Make after-screen beak if defined in config
        if self.config_file['make_screen_breaks']:
            self.update_diode_freqs(self.config_file['break_screen_freqs'])
            l_delay = self.config_file['break_screen_len']
            self._send_simple_screen(self.config_file['break_screen_screen'],
                                     'experiment__screen_break', l_delay)
            time.sleep(l_delay)
        if self._field_look_nums != None:
            self._sc_look_index = (self._sc_look_index + 1) % \
                    len(self._field_look_nums)
            LOGGER.info("look:  " + str(self._sc_look_index))



    def _play_sound(self):
        if not self._screen_sounds:
            return 
        import pygame
        p_wave_file = self._screen_sounds[self._screen_look_num]
        pygame.mixer.Sound(p_wave_file).play()


    def read_experiment_config(self, p_config_name):
        CONFIG = {}
        Config = ConfigParser.ConfigParser()
        if p_config_name == None:
            import inspect
            path = inspect.getsourcefile(self.__class__)
            p_config_name = os.path.dirname(path) + "/config/config_file.ini"
        print "------CONFIG NAME: ", p_config_name
        Config.readfp(open(p_config_name))
        for section in Config.sections():
                print section
                for option in Config.options(section):
                        print Config.get(section, option)
			CONFIG[option] = eval(Config.get(section, option))
	#CONFIG['screens'] = eval(CONFIG['screens'])
	#CONFIG['freqs'] = eval(CONFIG['freq_sets'])
	
        return CONFIG 


def main():
    l_experiment_manager = Experiment_manager(config_file_name)
    l_experiment_manager.run()

if __name__ == '__main__':
    main()
