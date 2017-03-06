#!/usr/bin/python

# This file is used as a global config file while PCBmodE is running.
# DO NOT EDIT THIS FILE

cfg = {} # PCBmodE configuration
brd = {} # board data
stl = {} # style data
pth = {} # path database
msg = {} # message database
stk = {} # stackup data
rte = {} # routing data
tmp = {} # temporary data

import pcbmode.utils.messages
import pcbmode.utils.json
import os
from pkg_resources import resource_exists, resource_filename

DEFAULT_CONFIG_FILENAME = 'pcbmode_config.json'

class Config(object):

    def __init__(self, defaults={}, clean=False):
        global cfg, brd, stl, pth, msg, stk, rte, tmp
        if clean:
            cfg = defaults.get('cfg', {})
            brd = defaults.get('brd', {})
            stl = defaults.get('stl', {})
            pth = defaults.get('pth', {})
            msg = defaults.get('msg', {})
            stk = defaults.get('stk', {})
            rte = defaults.get('rte', {})
            tmp = defaults.get('tmp', {})

    @property
    def cfg(self):
        global cfg
        return cfg

    @property
    def brd(self):
        global brd
        return brd

    @property
    def stl(self):
        global stl
        return stl

    @property
    def pth(self):
        global pth
        return pth

    @property
    def msg(self):
        global msg
        return msg

    @property
    def stk(self):
        global stk
        return stk

    @property
    def rte(self):
        global rte
        return rte

    @property
    def tmp(self):
        global tmp
        return tmp

    def get(self, *path_parts):

        if len(path_parts) == 0:
            raise KeyError('no top-level config key in path')

        top, path_parts = path_parts[0], path_parts[1:]

        if not hasattr(self, top):
            raise KeyError('invalid top-level config path supplied')

        top_dict = getattr(self, top)
        return self._get_config(top_dict, *path_parts)

    def _get_config(self, top_dict, *path_parts):

        if len(path_parts) == 0:
            return top_dict

        try:
            next_dict = top_dict[path_parts[0]]
        except KeyError:
            return None
        except IndexError:
            return None

        if len(path_parts) == 1:
            return next_dict

        return self._get_config(next_dict, *path_parts[1:])

    @property
    def _default_config_filename(self):
        return DEFAULT_CONFIG_FILENAME

    @property
    def global_config_path(self):
        return resource_filename('pcbmode', self._default_config_filename)

    def load_defaults(self, filename=None):
        global cfg
        if filename is None:
            filename = self._default_config_filename

        config_file_paths = [
            # config file in current directory
            os.path.join(os.getcwd(), filename),
            # global config file
            self.global_config_path,
        ]

        # now find first of those files which actually exists
        for config_file_path in config_file_paths:
            if os.path.isfile(config_file_path):
                cfg = pcbmode.utils.json.dictFromJsonFile(config_file_path)
                break
        else:
            pretty_config_file_paths = ''.join(['\n  {}'.format(p) for p in config_file_paths])
            pcbmode.utils.messages.error("Couldn't open PCBmodE's configuration file {}. Looked for it here:{}".format(filename, pretty_config_file_paths))

        # at this point, config.cfg exists

    def path_in_location(self, location, *filenames, absolute=False):
        base_dir = self.get('cfg', 'base-dir')
        if base_dir is None:
            raise Exception('cannot determine paths until base-dir has been set')

        location_dir = self.get('cfg', 'locations', location)
        if location_dir is None:
            raise Exception('cannot determine path for unknown location')

        path = os.path.join(base_dir, location_dir, *filenames)

        if absolute:
            return os.path.abspath(path)
        else:
            return path
