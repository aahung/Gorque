#! /usr/bin/python -u

import json

GORQUE_DIR = '/etc/gorque/'
CONFIG_FILE = GORQUE_DIR + 'gorque.json'
DB_FILE = GORQUE_DIR + 'gorque.db'


class Config(object):

    class ConfigException(Exception):

        def __init__(self, message):
            self.message = 'ConfigException: ' + message

    # config variables
    hosts = []
    max_job_per_user = 0
    # end

    def __init__(self):
        f = open(CONFIG_FILE, 'r')
        try:
            self.validate_and_load(json.load(f))
        except Exception, e:
            print(e.message)
            exit(-1)

    def validate_and_load(self, config):
        keys = config.keys()
        # check if host list is in
        if 'hosts' not in keys:
            raise Config.ConfigException('missing key "hosts"')
        if type(config['hosts']) is not list:
            raise Config.ConfigException('Invalid value of key "hosts"')
        for host in config['hosts']:
            if type(host) is not str:
                message = 'Invalid value of key "hosts": %s' % (str(host),)
                raise Config.ConfigException(message)
        self.hosts = config['hosts']
        # check if user_jobs is in
        if 'user_jobs' not in keys:
            raise Config.ConfigException('missing key "user_jobs"')
        if type(config['user_jobs']) is not int:
            raise Config.ConfigException('Invalid value of key "user_jobs"')
        self.max_job_per_user = config['user_jobs']
