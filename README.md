# Gorque, developed by aahung at landxh@gmail.com

This program is used to schedule GPU job according to 
1) one compute node could run only one job, 
2) job queued by priority (higher priority number should be executed first),
rule. 

## Install

## Usage

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