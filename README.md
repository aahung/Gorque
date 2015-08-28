# Gorque

## Intro
Gorque is used for linux based computer cluster with CUDA-enabled compute nodes. Compute node should have command ```nvidia-smi``` and in my case, GPU free memory is set to ```11MB```.

This program is used to schedule GPU job according to 
1. one compute node could run only one job, 
2. job queued by priority (higher priority number should be executed first),
rule. 

## Install

### Python 2.7+

Gorque relies on Python 2.7 or higher, if you are using CentOS, you may only have Python 2.6. **DO NOT simply upgrade your Python**, since CentOS relies on Python 2.6, you will destroy it.
Instead of upgrading, we will install a side version Python.

```sh
yum groupinstall "Development tools"
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel

cd /opt
wget --no-check-certificate https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tar.xz
tar xf Python-2.7.10.tar.xz
cd Python-2.7.10
./configure --prefix=/usr/local
make && make altinstall
```

Then you can use the command `python2.7`.

### Gorque

```sh
./goinstall.py
```
create a folder `/etc/gorque` and create a file named `gorque.json` with content:

```json
{
    "hosts": [
        "compute-0-1",
        "compute-0-2",
        "compute-0-3",
        "compute-0-4"
    ],
    "user_jobs": {
        "default": 8,
        "override": {
            "username": 4
        }
    },
    "job_script_dir": "/share/apps/gorque_scripts/",
    "job_log_dir": "/var/log/gorque/"
}
```

## Usage

run `godaemon.py` in directory where you installed Gorque to as root in the background.

### Job script

see job_script.sh, it submit 4 jobs to 4 nodes.

### Submit job
```shell
gosub <job_script.sh>
```
### Check queue
```shell
gostat [-a]
```

### Modify priority after submitting job
```shell
goprior <job_id>
```

### Cancel job
```shell
godel <job_id>
```
job id displayed in `gostat`

## License

The MIT License

Copyright (c) 2014-2014 Aahung. http://ideati.me

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.