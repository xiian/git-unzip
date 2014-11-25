# coding=utf-8
class MergeList(list):
    def add_merge(self, commit, next_commit):
        merge = Merge(commit=commit, next_commit=next_commit, merge_no=(len(self) + 1), tagger=self.tagger)
        self.append(merge)
        return merge

    def set_tagger(self, tagger):
        self.tagger = tagger

    def set_tag_format(self, tag_format):
        self.tag_format = tag_format


class Merge(object):
    def __init__(self, commit, next_commit, merge_no, tagger):
        self.commit = commit
        self.next_commit = next_commit
        self.merge_no = merge_no

        self.actual = commit.hash
        self.pre = commit.parents[0]
        self.base = commit.parents[1]
        self.tagger = tagger

    def get_tag_name(self, label, formatted=True):
        tag_name = 'merge-%d/%s' % (self.merge_no, label)
        if formatted:
            tag_name = self.tagger.format_tag(tag_name)
        return tag_name

    def make_tags(self):
        for label in ['actual', 'pre', 'base']:
            self.tagger.make_tag(self.get_tag_name(label, False), getattr(self, label), debug=False)

