#! /usr/bin/env python2.7
import subprocess


class Torque(object):
    """qstat and pbsnode parser"""

    @staticmethod
    def qstat_out_to_dict(qstat_out):
        lines = qstat_out.split()
        d = dict()
        for line in lines:
            line = line.strip()
            tokens = line.split('+')
            for token in tokens:
                token = token.strip()
                if '/' in token:
                    node = token.split('/')[0]
                    core = token.split('/')[1]
                    if node not in d:
                        d[node] = set()
                    d[node].add(core)
        for key in d:
            # convert to core number from core id
            d[key] = len(d[key])
        return d

    @staticmethod
    def pbsnode_out_to_dict(pbsnode_out):
        # different nodes separated by double \n
        paragraphs = pbsnode_out.split('\n\n')
        d = dict()
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            items = paragraph.split('\n')
            node = None
            for item in items:
                item = item.strip()
                # first non empty is node name
                if len(item) > 0 and node is None:
                    node = item
                if item.startswith('np'):
                    # number of p
                    n = item.split('=')[1].strip()
                    if node is not None:
                        d[node] = int(n)
        return d

    @staticmethod
    def free_cpus_in_nodes(nodes):
        pbsnode_out = subprocess.check_output('pbsnodes', shell=True)
        qstat_out = subprocess.check_output('qstat -n', shell=True)
        d = dict()
        d_all = Torque.pbsnode_out_to_dict(pbsnode_out)
        d_used = Torque.qstat_out_to_dict(qstat_out)
        for node in nodes:
            d[node] = 0
            if node in d_all:
                d[node] = d_all[node]
            if node in d_used:
                d[node] = d[node] - d_used[node]
        return d
