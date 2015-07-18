#! /usr/bin/env python2.7

import os
import subprocess
from godb import DB
import goconfig
import time
import sys
import getopt
from golog import golog


def humanize_time(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)


def crop_string(before, length):
    after = str(before)
    if len(after) > length:
        half_length = int(length / 2) - 1
        after = after[:half_length] + '..' + after[-half_length:]
    return after


class Gorque:
    def print_queue(self, all=False):
        # print the current queue
        template = ("| {0:4} | {1:20} | {2:10} | {3:10} | "
                    "{4:10} | {5:6} | {6:13} | {7:6} | {8:13} |")
        jobs = []
        db = DB(goconfig.DB_FILE)
        if all:
            jobs = db.fetch(desc=True)
        else:
            jobs = db.fetch(max=100)
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10,
                              '-' * 6, '-' * 13, '-' * 6, '-' * 13)
        print template.format('Id', 'Name', 'User', 'Priority', 'Time Use',
                              'Status', 'Node', 'CPUs', 'torque_pid')
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10,
                              '-' * 6, '-' * 13, '-' * 6, '-' * 13)
        job_count = 0
        for job in jobs:
            mode = job.get('mode')
            time_passed = None
            if mode == 'R':
                time_passed = humanize_time(int(time.time())
                                            - job.get('start_time'))
                job_count = job_count + 1
            elif mode == 'F' or mode == 'K':
                if job.get('start_time'):
                    time_passed = humanize_time(job.get('end_time')
                                                - job.get('start_time'))
                else:
                    time_passed = humanize_time(0)
                # ignore if too long
                if not all and int(time.time()) - job.get('end_time') > 60:
                    continue
            else:
                time_passed = humanize_time(0)
            print template.format(job.rowid, crop_string(job.get('name'), 20),
                                  job.get('user'), str(job.get('priority')),
                                  time_passed, mode, job.get('node', True),
                                  str(job.get('cpus')),
                                  str(job.get('torque_pid', True)))
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10,
                              '-' * 6, '-' * 13, '-' * 6, '-' * 13)
        print '| %s jobs running now.' % (str(job_count),)
        config = goconfig.Config()
        print '| Gorque config file: %s' % (goconfig.CONFIG_FILE)
        print '| job log files under %s' % (config.job_script_dir)
        print '| max job number per user: %d' % (config.max_job_per_user)

    def insert_job(self, name, user, priority, script, cpus):
        job = DB.Job({
            'user': user,
            'script': script,
            'priority': priority,
            'submit_time': int(time.time()),
            'start_time': 0,
            'end_time': 0,
            'mode': 'Q',
            'node': None,
            'name': name,
            'cpus': cpus})
        db = DB(goconfig.DB_FILE)
        print 'job created, job id is %s' % (str(db.insert(job)),)

    def submit_job(self, user, script_path):
        # analysis file
        f = open(script_path)
        name = user + ' job'
        priority = 1
        cpus = 1
        scripts = []
        reading_script = False
        current_script = ""
        for line in f.readlines():
            content = line.strip()
            if content == '':
                continue
            elif content.startswith('name:'):
                name = content[5:].strip()
            elif content.startswith('priority:'):
                priority = int(content[9:].strip())
            elif content.startswith('cpus:'):
                cpus = int(content[5:].strip())
            elif content == '[' and not reading_script:
                reading_script = True
            elif content == ']' and reading_script:
                reading_script = False
                scripts.append(current_script)
                current_script = ''
            elif reading_script:
                current_script = current_script + '\n' + content
        if len(scripts) == 0:
            print 'no job detected in the script.'
        for script in scripts:
            self.insert_job(name, user, priority, script, cpus)

    def kill_torque_job(self, torque_pid):
        os.system('/opt/torque/bin/qdel %d' % (torque_pid,))

    def prioritize_job(self, rowid, priority):
        db = DB(goconfig.DB_FILE)
        db.set(rowid, 'priority', priority)

    def kill_job(self, user, rowid):
        db = DB(goconfig.DB_FILE)
        job = db.fetch_by_id(rowid)
        if job.user != user or user != 'root':
            print 'You do not have permission to kill the job'
            return
        if not job:
            print 'no such a job'
        if job.get('pid'):
            print 'killing process %s and %s' % (str(job.get('pid')),
                                                 str(job.get('pid') + 1))
            os.system('kill -9 ' + str(job.get('pid')))
            os.system('kill -9 ' + str(job.get('pid') + 1))
            command = ('''ssh %s 'nvidia-smi | '''
                       '''sed "16!d" | tr -s " " | '''
                       '''cut -d" " -f3 ' ''') % (job.get('node'),)
            gpu_pid = subprocess.check_output(command, shell=True)
            if gpu_pid.strip() == 'running':
                # no GPU job
                pass
            else:
                # kill GPU job
                print gpu_pid
                os.system('''ssh %s 'kill -9 %s' ''' % (job.get('node'),
                                                        gpu_pid))
        if job.get('torque_pid'):
            self.kill_torque_job(job.get('torque_pid'))
        job.set('mode', 'K')
        job.set('end_time', int(time.time()))
        db.update(job)


def main(argv):
    user = None
    script_path = None
    delete_rowid = None
    try:
        opts, args = getopt.getopt(argv, "u:s:lad:p:")
    except getopt.GetoptError:
        print 'wrong syntax, please contact admin to request how to manual.'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-u':
            user = arg
        elif opt in ("-s"):
            script_path = arg
        elif opt in ("-p"):
            job_id = arg
            priority = raw_input('input the priority: ')
            q = Gorque()
            q.prioritize_job(job_id, priority)
        elif opt in ("-l"):
            q = Gorque()
            q.print_queue()
            sys.exit(0)
        elif opt in ("-a"):
            q = Gorque()
            q.print_queue(True)
            sys.exit(0)
        elif opt in ("-d"):
            delete_rowid = arg
    if user is not None and script_path is not None:
        q = Gorque()
        q.submit_job(user, script_path)
        sys.exit(0)
    if user is not None and delete_rowid is not None:
        q = Gorque()
        q.kill_job(user, delete_rowid)
        sys.exit(0)

if __name__ == "__main__":
    golog('gorque called with parameters: ' + str(sys.argv[1:]))
    main(sys.argv[1:])
