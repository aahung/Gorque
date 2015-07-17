#! /usr/bin/python -u

import os
import subprocess
from godb import DB
import goconfig
import time
import sys
import getopt
import json
from time import strftime


def golog(data):
    print '[' + strftime("%m/%d/%Y %H:%M:%S") + '] ' + str(data)


def load_config():
    # for future usage
    f = open('config.json')
    ls = f.readlines()
    j = ''
    for l in ls:
        if not l.strip().startswith('//'):
            j = j + l
    return json.loads(j)


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
                time_passed = humanize_time(job.get('start_time')
                                            - job.get('end_time'))
                # ignore if too long
                if not all and int(time.time()) - job.get('end_time') > 60:
                    continue
            else:
                time_passed = humanize_time(0)
            print template.format(job.rowid, crop_string(job.get('name'), 20),
                                  job.get('user'), str(job.get('priority')),
                                  time_passed, mode, job.get('node'),
                                  str(job.get('cpus')),
                                  str(job.get('torque_pid')))
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10,
                              '-' * 6, '-' * 13, '-' * 6, '-' * 13)
        print '| %s jobs running now.' % (str(job_count),)

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

    def kill_torque_job(self, rowid):
        c = self.conn.cursor()
        c.execute('''SELECT torque_pid FROM queue WHERE ROWID = ?''',
                  (str(rowid),))
        job = c.fetchone()
        torque_pid = str(job[0])
        os.system('/opt/torque/bin/qdel ' + torque_pid)

    def prioritize_job(self, rowid, priority):
        c = self.conn.cursor()
        c.execute('''UPDATE queue SET priority = ? WHERE ROWID = ?''', (int(priority), str(rowid)))
        self.conn.commit()

    def kill_job(self, rowid):
        c = self.conn.cursor()
        c.execute('''SELECT pid, mode, node FROM queue WHERE ROWID = ?''', (str(rowid),))
        job = c.fetchone()
        if job[0] is not None:
            print job[0]
            os.system('kill -9 ' + str(job[0]))
            os.system('kill -9 ' + str(job[0] + 1))
            gpu_pid = subprocess.check_output('''ssh %s 'nvidia-smi | sed "16!d" | tr -s " " | cut -d" " -f3 ' ''' % (job[2],), shell=True)
            if gpu_pid.strip() == 'running':
                # no GPU job
                pass
            else:
                # kill GPU job
                print gpu_pid
                os.system('''ssh %s 'kill -9 %s' ''' % (job[2], gpu_pid))
        self.kill_torque_job(rowid)
        c = self.conn.cursor()
        c.execute('''UPDATE queue SET mode = 'K', end_time = ?, pid = NULL WHERE ROWID = ?''', (int(time.time()), str(rowid)))
        self.conn.commit()

    def log_to_file(self, user, rowid, out, err, job_name):
        directory = '/home/' + user + '/gorque_log/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        f = open(directory + str(rowid) + '_' + str(job_name) + '.log', 'w')
        f.write(out)
        f.close()
        f = open(directory + str(rowid) + '_' + str(job_name) + '.error', 'w')
        f.write(err)
        f.close()

    def find_free_nodes(self):
        golog('checking GPU free nodes')
        free_nodes = subprocess.check_output('''for i in compute-0-2 compute-0-3 compute-0-4 compute-0-5 compute-0-6 compute-0-7 compute-0-8 compute-0-9 compute-0-10 compute-0-11 compute-0-12 compute-0-13 compute-0-14 compute-0-15 compute-0-16 ; do ssh ${i} 'mem=$(nvidia-smi | grep 4799 | cut -d"/" -f3 | cut -d"|" -f2 | sed -e "s/^[ \t]*//"); if [[ "$mem" == 10MiB* ]]; then echo $(hostname) | cut -d"." -f1; fi'; done;''', shell=True)
        free_nodes = [x for x in free_nodes.split('\n') if x != '']
        if len(free_nodes) > 0:
            golog('found GPU free node(s)')
        return free_nodes

    def get_waiting_jobs(self):
        c = self.conn.cursor()
        c.execute('''SELECT ROWID, user, cpus FROM queue WHERE mode = 'Q' ORDER BY priority DESC ''')
        waiting_jobs = c.fetchall()
        qualified_jobs = []
        for job in waiting_jobs:
            c.execute('''SELECT ROWID FROM queue WHERE mode = 'R' AND user = ?''', (job[1],))
            user_jobs = c.fetchall()
            if len(user_jobs) < self.max_job_per_user_limit:
                qualified_jobs.append(job)
        return qualified_jobs

    def check_jobs(self):
        qualified_jobs = self.get_waiting_jobs()
        if len(qualified_jobs) > 0:
            # make sure there is waiting jobs then query
            free_nodes = self.find_free_nodes()
            if len(free_nodes) > 0:
                # last use compute-0-0
                if free_nodes[0].startswith('compute-0-0'):
                    # compute0 = free_nodes[0]
                    free_nodes.remove(free_nodes[0])
                    # free_nodes.append(compute0)
                # refetch database in case already
                # executed by another cron process.
                qualified_jobs = self.get_waiting_jobs()
                if len(qualified_jobs) > 0:
                    # check user limit
                    found = False
                    job = None
                    node = None
                    for qualified_job in qualified_jobs:
                        j_free_nodes = []
                        j_cpus = qualified_job[2]
                        # check torque status find free cpu node which cpu
                        # availibility >= cpu required
                        golog('checking CPU free nodes')
                        qstat = subprocess.check_output(['/opt/torque/bin/qstat', '-n'])
                        golog('called \'gostat -n\'')
                        for free_node in free_nodes:
                            j_cpus_in_use = qstat.count(free_node + '/')
                            if j_cpus_in_use + j_cpus > 16:
                                pass
                            else:
                                j_free_nodes.append(free_node)
                        if len(j_free_nodes) > 0:
                            golog('found CPU free node(s)')
                            node = j_free_nodes[0]
                            job = qualified_job
                            found = True
                            break
                    if found:
                        golog('found a job, ready to execute')
                        self.execute_job(job[0], node, job[2])
                    else:
                        golog('no free nodes avalible')
                else:
                    golog('no free nodes avalible')
            else:
                golog('no free nodes avalible')
        else:
            golog('no qualified waiting jobs in the queue')


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
    if delete_rowid is not None:
        q = Gorque()
        q.kill_job(delete_rowid)
        sys.exit(0)

if __name__ == "__main__":
    golog('gorque called with parameters: ' + str(sys.argv[1:]))
    main(sys.argv[1:])
