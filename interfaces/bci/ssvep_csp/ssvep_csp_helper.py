#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:
#     Mateusz Kruszyński <mateusz.kruszynski@gmail.com>
#
import pickle
import numpy as np

from interfaces import interfaces_logging as logger
LOGGER = logger.get_logger("ssvep_csp_helper")

from acquisition import acquisition_helper


def get_csp_config(path, name):
    file_name = acquisition_helper.get_file_path(path, name)
    csp_file = file_name+'.csp'
    f = open(csp_file, 'r')
    d = pickle.load(f)
    f.close()
    LOGGER.info("Got csp config:")
    LOGGER.info(str(d))
    return d



def get_montage_matrix(all_channels, use_channels, montage, montage_channels):
    """Return montage matrix.

    >>> m = get_montage_matrix(['a', 'b', 'c', 'd'], ['a', 'b'], 'ears', ['c', 'd'])

    >>> np.dot([1, 2, 3, 5], m)
    array([-3., -2.])

    
    >>> m = get_montage_matrix(['a', 'b', 'c', 'd'], ['a', 'd'], 'ears', ['b', 'c'])

    >>> np.dot([1, 3, 5, 2], m)
    array([-3., -2.])

    
    >>> m = get_montage_matrix(['a', 'b', 'c', 'd'], ['a', 'b'], 'ident', [])

    >>> np.dot([1, 2, 3, 5], m)
    array([ 1.,  2.])


    >>> m = get_montage_matrix(['a', 'b', 'c', 'd'], ['a', 'b', 'd'], 'diff', ['c'])

    >>> np.dot([1, 2, 3, 5], m)
    array([-2., -1.,  2.])


    """

    m = np.zeros((len(all_channels), len(use_channels)))
    for i, ch in enumerate(use_channels):
        ch_ind = all_channels.index(ch)
        m[ch_ind, i] = 1.0

    if montage == 'ident':
        return m
    elif montage == 'ears':
        e1 = all_channels.index(montage_channels[0])
        e2 = all_channels.index(montage_channels[1])
        for i in range(len(use_channels)):
            m[e1, i] = -0.5
            m[e2, i] = -0.5
    elif montage == 'diff':
        d = all_channels.index(montage_channels[0])
        for i in range(len(use_channels)):
            m[d, i] = -1.0

    return m

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print("If no errors - tests SUCCEDED!!!")
