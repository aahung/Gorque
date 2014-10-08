#! /usr/bin/python

import os
import subprocess
import sqlite3
import time
import sys
import getopt


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


class queue:
    def __init__(self):
        default_directory = '/share/apps/gorque/'
        conn = sqlite3.connect(default_directory + 'gorque.db')
        c = conn.cursor()
        c.execute('''SELECT name FROM SQLITE_MASTER WHERE type = 'table' ''')
        if c.fetchone() is None:
            print 'creating database'
            c.execute('''CREATE TABLE queue
                (user TEXT, script BLOB, priority INTEGER,
                    submit_time INTEGER, start_time INTEGER, end_time INTEGER,
                    mode TEXT, node TEXT, name TEXT, pid INTEGER)''')
            conn.commit()
        self.conn = conn

    def print_queue(self, all=False):
        # print the current queue
        c = self.conn.cursor()
        template = "| {0:4} | {1:20} | {2:10} | {3:10} | {4:10} | {5:6} | {6:13} |"
        command = '''SELECT name, user, priority,
            start_time, end_time, mode, node, ROWID FROM queue '''
        if all:
            c.execute(command + ''' ORDER BY ROWID DESC''')
        else:
            c.execute(command)
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10, '-' * 6, '-' * 13)
        print template.format('Id', 'Name', 'User', 'Priority', 'Time Use', 'Status', 'Node')
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10, '-' * 6, '-' * 13)
        job_count = 0
        for row in c.fetchall():
            mode = row[5]
            time_passed = None
            if mode == 'R':
                time_passed = humanize_time(int(time.time()) - row[3])
                job_count = job_count + 1
            elif mode == 'F' or mode == 'K':
                time_passed = humanize_time(row[4] - row[3])
                # ignore if too long
                if not all and int(time.time()) - row[4] > 60:
                    continue
            else:
                time_passed = humanize_time(0)
            print template.format(str(row[7]), crop_string(row[0], 20), row[1], str(row[2]), time_passed, mode, row[6])
        print template.format('-' * 4, '-' * 20, '-' * 10, '-' * 10, '-' * 10, '-' * 6, '-' * 13)
        print '| ' + str(job_count) + ' jobs running now.'


    def insert_job(self, name, user, priority, script):
        c = self.conn.cursor()
        data = (user, script, priority, int(time.time()), 0, 0, 'Q', '', name, None)
        c.execute('''INSERT INTO queue VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
        self.conn.commit()
        c.execute('''SELECT ROWID FROM queue ORDER BY ROWID DESC LIMIT 1''')
        print c.fetchone()

    def submit_job(self, user, script_path):
        # analysis file
        f = open(script_path)
        name = user + ' job'
        priority = 1
        scripts = []
        reading_script = False
        currentScript = ""
        for line in f.readlines():
            content = line.strip()
            if content == '':
                continue
            elif content.startswith('name:'):
                name = content[5:].strip()
            elif content.startswith('priority:'):
                priority = int(content[9:].strip())
            elif content == '[' and not reading_script:
                reading_script = True
            elif content == ']' and reading_script:
                reading_script = False
                scripts.append(currentScript)
                currentScript = ''
            elif reading_script:
                currentScript = currentScript + '\n' + content
        if len(scripts) == 0:
            print 'not job detected in the script.'
        for script in scripts:
            self.insert_job(name, user, priority, script)

    def execute_job(self, rowid, node):
        c = self.conn.cursor()
        c.execute('''SELECT user, script, name FROM queue WHERE ROWID = ?''', (str(rowid),))
        job = c.fetchone()
        template = '''/sbin/runuser -l {0} -c 'ssh {1} "/bin/bash {2}"' '''
        tmp_script_path = '/share/apps/gorque/' + job[0] + '_' + str(rowid) + '.sh'
        f = open(tmp_script_path, 'w')
        f.write(job[1])
        f.close()
        command = template.format(job[0], node, tmp_script_path)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # update pid to database
        c.execute('''UPDATE queue SET mode = 'R', start_time = ?, node = ?, pid = ? WHERE ROWID = ?''', (int(time.time()), node, process.pid, str(rowid)))
        self.conn.commit()
        out, err = process.communicate()
        # save the output or error
        self.log_to_file(job[0], rowid, out, err, job[2])
        # remove the sh file
        os.remove(tmp_script_path)
        self.finish_job(rowid)

    def finish_job(self, rowid):
        c = self.conn.cursor()
        c.execute('''UPDATE queue SET mode = 'F', end_time = ? WHERE ROWID = ?''', (int(time.time()), str(rowid)))
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
            print gpu_pid
            os.system('''ssh %s 'kill -9 %s' ''' % (job[2], gpu_pid))
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
        free_nodes = subprocess.check_output('''for i in compute-0-0 compute-0-2 compute-0-3 compute-0-4 compute-0-5 compute-0-6 compute-0-7 compute-0-8 compute-0-9 compute-0-10 compute-0-11 compute-0-12 compute-0-13 compute-0-14 compute-0-15 compute-0-16 ; do ssh ${i} 'mem=$(nvidia-smi | grep 4799 | cut -d"/" -f3 | cut -d"|" -f2 | sed -e "s/^[ \t]*//"); if [[ "$mem" == 10MiB* ]]; then echo $(hostname) | cut -d"." -f1; fi'; done;''', shell=True)
        free_nodes = [x for x in free_nodes.split('\n') if x != '']
        return free_nodes

    def check_jobs(self):
        c = self.conn.cursor()
        c.execute('''SELECT ROWID FROM queue WHERE mode = 'Q' ORDER BY priority DESC ''')
        waiting_jobs = c.fetchall()
        if len(waiting_jobs) > 0:
            free_nodes = self.find_free_nodes()
            if len(free_nodes) > 0:
                # last use compute-0-0
                if free_nodes[0].startswith('compute-0-0'):
                    # compute0 = free_nodes[0]
                    free_nodes.remove(free_nodes[0])
                    # free_nodes.append(compute0)
                # refetch database in case already executed by another cron process.
                c.execute('''SELECT ROWID FROM queue WHERE mode = 'Q' ORDER BY priority DESC ''')
                waiting_jobs = c.fetchall()
                if len(waiting_jobs) > 0:
                    job = waiting_jobs[0]
                    node = free_nodes[0]
                    self.execute_job(job[0], node)


def main(argv):
    user = None
    script_path = None
    delete_rowid = None
    try:
        opts, args = getopt.getopt(argv, "u:s:lad:c")
    except getopt.GetoptError:
        print 'wrong syntax, please contact admin to request how to manual.'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-u':
            user = arg
        elif opt in ("-s"):
            script_path = arg
        elif opt in ("-l"):
            q = queue()
            q.print_queue()
            sys.exit(0)
        elif opt in ("-a"):
            q = queue()
            q.print_queue(True)
            sys.exit(0)
        elif opt in ("-d"):
            delete_rowid = arg
        elif opt in ("-c"):
            q = queue()
            q.check_jobs()
            sys.exit(0)
    if user is not None and script_path is not None:
        q = queue()
        q.submit_job(user, script_path)
        sys.exit(0)
    if delete_rowid is not None:
        q = queue()
        q.kill_job(delete_rowid)
        sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
