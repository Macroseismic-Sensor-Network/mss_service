# -*- coding: utf-8 -*-
##############################################################################
# LICENSE
#
# This file is part of mss_service.
# 
# If you use mss_service in any program or publication, please inform and
# acknowledge its authors.
# 
# mss_service is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# mss_service is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with mss_dataserver. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2022 Stefan Mertl
##############################################################################

''' General utility function.

'''
import logging
import re


def get_logger_stream_handler(log_level = 'WARNING'):
    ''' Create a logging stream handler.

    Returns
    -------
    ch: logging.StreamHandler
        The logging filehandler.
    '''
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter("#LOG# - %(asctime)s - %(process)d - %(levelname)s - %(name)s: %(message)s")
    ch.setFormatter(formatter)
    return ch


class AttribDict(dict):
    ''' A dictionary with object like attribute access.

    '''
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)
        

class Version(object):
    ''' A version String representation.


    Parameters
    ----------
    version: str
        The version as a point-seperated string (e.g. 0.0.1).

    '''
    

    def __init__(self, version = '0.0.1'):
        ''' Initialize the instance.

        '''
        self.version = self.string_to_tuple(version)


    def __str__(self):
        ''' The string representation.
        '''
        return '.'.join([str(x) for x in self.version])


    def __eq__(self, c):
        ''' Test for equality.
        '''
        for k, cur_n in enumerate(self.version):
            if cur_n != c.version[k]:
                return False

        return True

    def __ne__(self, c):
        ''' Test for inequality.
        '''
        return not self.__eq__(c)


    def __gt__(self, c):
        ''' Test for greater than.
        '''
        for k, cur_n in enumerate(self.version):
            if cur_n > c.version[k]:
                return True
            elif cur_n != c.version[k]:
                return False

        return False


    def __lt__(self, c):
        ''' Test for less than.
        '''
        for k, cur_n in enumerate(self.version):
            if cur_n < c.version[k]:
                return True
            elif cur_n != c.version[k]:
                return False

        return False


    def __ge__(self, c):
        ''' Test for greater or equal.
        '''
        return self.__eq__(c) or self.__gt__(c)

    def __le__(self, c):
        ''' Test for less or equal.
        '''
        return self.__eq__(c) or self.__lt__(c)


    def string_to_tuple(self, vs):
        ''' Convert a version string to a tuple.

        Parameters
        ----------
        version: str
            The version as a point-seperated string (e.g. 0.0.1).

        Returns
        -------
        version_tuple: tuple
            The version string as a tuple.
        '''
        nn = vs.split('.')
        for k, x in enumerate(nn):
            if x.isdigit():
                nn[k] = int(x)
            else:
                tmp = re.split('[A-Za-z]', x)
                tmp = [x for x in tmp if x.isdigit()]
                if len(tmp) > 0:
                    nn[k] = int(tmp[0])
                else:
                    nn[k] = 0

        return tuple(nn)

