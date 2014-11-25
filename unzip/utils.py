# coding=utf-8
import logging
import subprocess


class GitCmdException(Exception):
    def __init__(self, stdout, stderr, message):
        self.stdout = stdout
        self.stderr = stderr
        self.message = message


class RebaseAndTagException(GitCmdException):
    def __init__(self, tag, stdout, stderr, message):
        self.tag = tag
        super(RebaseAndTagException, self).__init__(stdout, stderr, message)


def run_cmd(cmd, debug=True):
    if debug:
        logger = logging.getLogger('unzip')
        logger.debug('Running: %s' % cmd)
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode:
        raise GitCmdException(stdout=stdout, stderr=stderr, message='Problem running %s: %s' % (cmd, stderr.strip()))
    return stdout.strip()
