# coding=utf-8
class CommitList(list):
    pass


class Commit(object):
    def __init__(self, hash, parents, important=False):
        self.hash = hash
        self.parents = parents
        self.important = important

    @property
    def is_merge(self):
        return len(self.parents) > 1

    def __str__(self):
        return '%s - (%s)' % (self.hash, ', '.join(self.parents))
