from time import strftime
from goconfig import Config


config = Config()


def golog(data):
    f = open('%slog' % (config.job_log_dir,), 'a')
    f.write('[%s] %s' % (strftime("%m/%d/%Y %H:%M:%S"), str(data)))
    f.close()
