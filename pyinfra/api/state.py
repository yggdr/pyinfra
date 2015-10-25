# pyinfra
# File: pyinfra/api/state.py
# Desc: class that represents the current pyinfra.state

import sys

from gevent.pool import Pool

from .config import Config


class DefaultState(object):
    '''Represents a default/blank internal pyinfra state.'''
    inventory = None # a pyinfra.api.Inventory which stores all our pyinfra.api.Host's
    config = None # a pyinfra.api.Config

    pool = None # main gevent pool

    in_op = False # whether we are in an @operation (so inner ops aren't wrapped)
    current_op_sudo = None # current @operation args tuple (sudo, sudo_user) for use w/facts

    pre_run = False

    deploy_dir = None

    def __init__(self):
        self.op_order = [] # list of operation hashes
        self.op_meta = {} # maps operation hash -> names/etc
        self.ops_run = set() # list of ops which have been started/run
        self.ops = {} # maps hostnames ->  operation hashes -> operation

        self.meta = {}
        self.results = {}

        self.ssh_connections = {}
        self.sftp_connections = {}


class State(DefaultState):
    '''Create a new state based on the default state.'''
    def __init__(self, inventory, config=None):
        super(State, self).__init__()

        if config is None:
            config = Config()

        # Assign inventory/config
        self.inventory = inventory
        self.config = config

        # Assign self to inventory & config
        inventory.state = config.state = self

        # Setup greenlet pool
        self.pool = Pool(len(inventory))

        hostnames = [host.ssh_hostname for host in inventory]

        self.ops = {
            hostname: {}
            for hostname in hostnames
        }
        self.ops = {
            hostname: {}
            for hostname in hostnames
        }

        self.meta = {
            hostname: {
                'ops': 0, # one function call in a deploy file
                'commands': 0 # actual # of commands to run
            }
            for hostname in hostnames
        }

        self.results = {
            hostname: {
                'ops': 0, # success_ops + failed ops w/ignore_errors
                'success_ops': 0,
                'error_ops': 0,
                'commands': 0
            }
            for hostname in hostnames
        }


class StateModule(object):
    '''
    A classmodule which binds to ``pyinfra.pseudo_state``. Used in CLI deploys as deploy
    files can't access the state themselves (state generated by bin executable).
    '''
    _state = None

    def __getattr__(self, key):
        return getattr(self._state, key)

    def __setattr__(self, key, value):
        if key == '_state':
            return object.__setattr__(self, key, value)

        setattr(self._state, key, value)

    def set(self, state):
        '''
        Bind a new state object.

        Args:
            state (``pyinfra.api.State`` obj): state object to bind to
        '''
        self._state = state


import pyinfra
sys.modules['pyinfra.pseudo_state'] = pyinfra.pseudo_state = StateModule()
