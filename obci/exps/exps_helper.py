#!/usr/bin/env python
#
# Author:
#      Mateusz Kruszynski <mateusz.kruszynski@titanis.pl>
#
import inspect, os, time
from obci.control.peer.configured_client import ConfiguredClient
from obci.configs import settings
from multiplexer.multiplexer_constants import types, peers

from obci.utils import tags_helper
from obci.acquisition import acquisition_helper


class ExpsHelper(ConfiguredClient):
    def __init__(self, addresses=settings.MULTIPLEXER_ADDRESSES, config_module=None):
        if config_module is not None:
            config_file = os.path.abspath(inspect.getfile(config_module))
        else:
            config_file = None
        super(ExpsHelper, self).__init__(addresses=addresses, type=peers.CLIENT, external_config_file=config_file)
        self.ready()
        
    def send_tag(self, p_start_timestamp, p_end_timestamp, 
                 p_tag_name, p_tag_desc={}, p_tag_channels=""):
        tags_helper.send_tag(self.conn, p_start_timestamp, p_end_timestamp, 
                             p_tag_name, p_tag_desc, p_tag_channels)

    def finish_saving(self, wait=True):
        if wait:
            acquisition_helper.finish_saving()
        else:
            acquisition_helper.send_finish_saving(self.tagger.conn)

if __name__ == '__main__':
    helper = ExpsHelper()
    time.sleep(100000)
