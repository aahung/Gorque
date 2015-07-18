#! /usr/bin/env python2.7

import os
import subprocess


GODIR = '/opt/gorque'
GODIR = raw_input('directory you want to install Gorque to [%s]: ' % (GODIR,))
if not os.path.isdir(GODIR):
    print('%s directory does not exit, please create it first' % (GODIR,))
    exit(-1)

GODIR = os.path.abspath(GODIR)

print 'Target directory %s' % (GODIR,)
f = open('./cpp/parameter.h', 'w')
f.write('#define GODIR "%s"' % (GODIR,))
f.close()

# compile
# check compiler
cxx = subprocess.check_output('echo $CXX', shell=True)
if cxx == '\n':
    print('Please make sure you have C++ compiler, '
          'for example, if you g++, run "export CXX=g++"')
    exit(-1)
os.system('$CXX ./cpp/godel.cpp -o ./cpp/godel')
os.system('$CXX ./cpp/goprior.cpp -o ./cpp/goprior')
os.system('$CXX ./cpp/gostat.cpp -o ./cpp/gostat')
os.system('$CXX ./cpp/gosub.cpp -o ./cpp/gosub')

os.system('chmod u=rwx,go=xr,+s ./cpp/godel')
os.system('chmod u=rwx,go=xr,+s ./cpp/goprior')
os.system('chmod u=rwx,go=xr,+s ./cpp/gostat')
os.system('chmod u=rwx,go=xr,+s ./cpp/gosub')

os.system('mv ./cpp/godel /usr/bin/godel')
os.system('mv ./cpp/goprior /usr/bin/goprior')
os.system('mv ./cpp/gostat /usr/bin/gostat')
os.system('mv ./cpp/gosub /usr/bin/gosub')

os.system('mv ./*.py %s/' % (GODIR,))
