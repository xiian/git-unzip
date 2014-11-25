# coding=utf-8
from .utils import run_cmd, GitCmdException, RebaseAndTagException


class Tagger(object):
    def __init__(self, hashinfo=None):
        from hashlib import sha1

        hasher = sha1()
        hasher.update(".".join(hashinfo))
        self.base = 'unzip-%s/' % hasher.hexdigest()[0:8]

    def format_tag(self, name):
        return ''.join((self.base, name))

    def make_tag(self, name, commit=None, debug=True):
        commit = commit or ''
        formatted_name = self.format_tag(name)
        run_cmd('git tag -f %s %s' % (formatted_name, commit), debug=debug)
        return formatted_name

    def tag_exists(self, tag):
        try:
            run_cmd('git rev-parse %s' % tag)
            return True
        except GitCmdException:
            return False

    def rebase_and_tag(self, tag, new_base, old_base):
        try:
            run_cmd('git rebase --onto %s %s' % (new_base, old_base))
            self.make_tag(tag)
        except GitCmdException as e:
            raise RebaseAndTagException(tag=self.format_tag(tag), stderr=e.stderr, stdout=e.stdout, message=e.message)
