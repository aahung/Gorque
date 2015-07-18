#! /usr/bin/env python2.7

import json
import os

GORQUE_DIR = '/etc/gorque/'
CONFIG_FILE = GORQUE_DIR + 'gorque.json'
DB_FILE = GORQUE_DIR + 'gorque.db'


class Config():

    class ConfigException(Exception):

        def __init__(self, message):
            super(Config.ConfigException, self).__init__('ConfigException: '
                                                         + message)

    # config variables
    hosts = None
    max_job_per_user = None
    # JOB_SCRIPT_DIR folder should be
    # able to be accessed by nodes
    job_script_dir = None
    job_log_dir = None
    # end

    def __init__(self):
        f = open(CONFIG_FILE, 'r')
        try:
            self.validate_and_load(json.load(f))
        except Exception, e:
            print('Config reading error: %s' % (e,))
            exit(-1)

    def validate_and_load(self, config):
        keys = config.keys()
        # check if host list is in
        if 'hosts' not in keys:
            raise Config.ConfigException('missing key "hosts"')
        if type(config['hosts']) is not list:
            raise Config.ConfigException('Invalid value of key "hosts"')
        for host in config['hosts']:
            if type(host) is not str and type(host) is not unicode:
                message = 'Invalid value of key "hosts": %s' % (str(host),)
                raise Config.ConfigException(message)
        self.hosts = config['hosts']
        # check if user_jobs is in
        if 'user_jobs' not in keys:
            raise Config.ConfigException('missing key "user_jobs"')
        if type(config['user_jobs']) is not int:
            raise Config.ConfigException('Invalid value of key "user_jobs"')
        self.max_job_per_user = config['user_jobs']
        # check if job_script_dir is in
        if 'job_script_dir' not in keys:
            raise Config.ConfigException('missing key "job_script_dir"')
        if type(config['job_script_dir']) is not unicode:
            raise Config.ConfigException('Invalid value of '
                                         'key "job_script_dir"')
        if not os.path.isdir(self.job_script_dir):
            raise Config.ConfigException('%s is not a directory'
                                         % (self.job_script_dir,))
        self.job_script_dir = config['job_script_dir']
        # check if job_log_dir is in
        if 'job_log_dir' not in keys:
            raise Config.ConfigException('missing key "job_log_dir"')
        if type(config['job_log_dir']) is not unicode:
            raise Config.ConfigException('Invalid value of '
                                         'key "job_log_dir"')
        self.job_log_dir = config['job_log_dir']
        if not os.path.isdir(self.job_log_dir):
            raise Config.ConfigException('%s is not a directory'
                                         % (self.job_log_dir,))
        if not self.job_log_dir.endswith('/'):
            self.job_log_dir = self.job_log_dir + '/'
