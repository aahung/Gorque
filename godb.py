#! /usr/bin/python -u

import sqlite3

# [Table] queue
#   user Text
#   script Binary
#   priority Int
#   submit_time Int
#   start_time Int
#   end_time Int
#   mode Text
#   node Text
#   name Text
#   pid Int
#   cpus Int number of cpu cores supporsed to use
#   torque_pid Int


class DB():

    class Job():
        # user = None
        # script = None
        # priority = 1
        # submit_time = int()
        # start_time = int()
        # end_time = int()
        # mode = str()
        # node = str()
        # name = str()
        # pid = int()
        # cpus = int()
        # torque_pid = int()

        rowid = None
        dict = {}

        def __init__(self, dict=None):
            for key in DB.Job.static_keys():
                    self.dict[key] = None
            if dict:
                for key, value in zip(dict.keys(), dict.values()):
                    if key in DB.Job.static_keys():
                        self.dict[key] = value

        @staticmethod
        def static_key_value_type():
            return {'user': str,
                    'script': str,
                    'priority': int,
                    'submit_time': int,
                    'start_time': int,
                    'end_time': int,
                    'mode': str,
                    'node': str,
                    'name': str,
                    'pid': int,
                    'cpus': int,
                    'torque_pid': int}

        @staticmethod
        def static_keys():
            return DB.Job.static_key_value_type().keys()

        def keys(self):
            return self.dict.keys()

        def values(self):
            return self.dict.values()

        def get(self, name):
            if name not in DB.Job.static_keys():
                raise Exception('no such key' % (name,))
            return self.dict[name]

        def set(self, name, value):
            if name not in DB.Job.static_keys():
                raise Exception('no such key' % (name,))
            self.dict[name] = value

    path = ''

    def __init__(self, path):
        self.path = path
        self.initialize_tables()

    def initialize_tables(self):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute('''SELECT name FROM SQLITE_MASTER
                  WHERE type = 'table' ''')
        if c.fetchone() is None:
            print 'creating database'
            c.execute('''CREATE TABLE queue
                (user TEXT, script BLOB, priority INTEGER,
                    submit_time INTEGER, start_time INTEGER,
                    end_time INTEGER,
                    mode TEXT, node TEXT, name TEXT, pid INTEGER,
                    cpus INTEGER, torque_pid INTEGER)''')
            conn.commit()
        conn.close()

    def fetch(self, desc=False, max=-1):
        '''
            desc means sort by rowid from largest to smallest
            max == -1: fetch all records
        '''
        columns = DB.Job.static_keys()
        columns.append('ROWID')
        command = '''SELECT %s FROM queue''' % (str.join(', ', columns),)
        if desc:
            command = command + ''' ORDER BY ROWID DESC'''
        jobs = []
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command)
        rows = c.fetchall()
        for row in rows:
            job = DB.Job()
            job.rowid = int(row[-1])
            for key, value in zip(columns[:-1], row[:-1]):
                job.set(key, value)
            jobs.append(job)
        conn.close()
        return jobs

    def fetch_by_id(self, rowid):
        columns = DB.Job.static_keys()
        command = '''SELECT %s FROM queue
                     WHERE ROWID = ?''' % (str.join(', ', columns),)
        job = DB.Job()
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command, rowid)
        row = c.fetchone()
        if not row:
            return None
        conn.close()
        job.rowid = rowid
        for key, value in zip(columns, row):
            job.set(key, DB.Job.static_key_value_type()[key](value))
        return job

    def fetch_waiting(self):
        columns = DB.Job.static_keys()
        columns.append('ROWID')
        command = '''SELECT %s FROM queue
                     WHERE mode = 'Q'
                     ORDER BY priority DESC''' % (str.join(', ', columns),)
        jobs = []
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command)
        rows = c.fetchall()
        for row in rows:
            job = DB.Job()
            job.rowid = int(row[-1])
            for key, value in zip(columns[:-1], row[:-1]):
                job.set(key, value)
            jobs.append(job)
        conn.close()
        return jobs

    def fetch_running(self):
        columns = DB.Job.static_keys()
        columns.append('ROWID')
        command = '''SELECT %s FROM queue
                     WHERE mode = 'R'
                     ORDER BY priority DESC''' % (str.join(', ', columns),)
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command)
        jobs = []
        rows = c.fetchall()
        for row in rows:
            job = DB.Job()
            job.rowid = int(row[-1])
            for key, value in zip(columns[:-1], row[:-1]):
                job.set(key, value)
            jobs.append(job)
        conn.close()
        return jobs

    def insert(self, job):
        key_str = str.join(', ', job.keys())
        question_str = str.join(', ', ['?'] * len(job.keys()))
        command = '''INSERT INTO queue (%s)
            VALUES (%s)''' % (key_str, question_str)
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command, tuple(job.values()))
        conn.commit()
        c.execute('''SELECT ROWID FROM queue
                     ORDER BY ROWID DESC LIMIT 1''')
        rowid = tuple(c.fetchone())[0]
        conn.close()
        return rowid

    def update(self, job):
        terms = []
        for key in job.keys():
            terms.append('%s = ?', (key,))
        command = '''UPDATE queue SET %s
                     WHERE ROWID = ?''' % (str.join(', ', terms),)
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command, tuple(job.values() + [job.rowid]))
        conn.commit()
        conn.close()

    def set(self, rowid, key, value):
        command = '''UPDATE queue SET %s = ?
                     WHERE ROWID = ?''' % (key,)
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute(command, (DB.static_key_value_type()[key](value), rowid))
        conn.commit()
        conn.close()

    def prioritize(self, rowid, priority):
        self.set(rowid, 'priority', priority)
