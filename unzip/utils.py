# coding=utf-8
import logging
import subprocess
from subprocess import Popen, PIPE


class GitCmdException(Exception):
    def __init__(self, stdout, stderr, message):
        self.stdout = stdout
        self.stderr = stderr
        self.message = message


class RebaseAndTagException(GitCmdException):
    def __init__(self, tag, stdout, stderr, message):
        self.tag = tag
        super(RebaseAndTagException, self).__init__(stdout, stderr, message)


def run_cmd(cmd, debug=True, multi=False):
    if debug:
        logger = logging.getLogger('unzip')
        logger.debug('Running: %s' % cmd)
    if multi:
        cmd_parts = cmd.split(' | ')
        first_cmd = cmd_parts.pop(0)

        process = Popen(first_cmd.split(), stdout=PIPE)
        for cmd in cmd_parts:
            process = Popen(cmd.split(), stdin=process.stdout, stdout=PIPE)
    else:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout = stdout or ''
    stderr = stderr or ''
    if process.returncode:
        raise GitCmdException(stdout=stdout, stderr=stderr, message='Problem running %s: %s' % (cmd, stderr.strip()))
    return stdout.strip()
