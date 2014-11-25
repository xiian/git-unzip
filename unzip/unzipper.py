# coding=utf-8
import logging

from .tagger import Tagger
from .utils import run_cmd
from .commits import CommitList, Commit
from .merges import MergeList


class Unzipper(object):
    def __init__(self, zipped_branch, unzip_from_branch, zip_base, logger=None):
        self.zipped_branch = zipped_branch
        self.unzip_from_branch = unzip_from_branch
        self.zip_base = zip_base
        self.logger = logger

        self.tagger = Tagger(hashinfo=(self.zipped_branch, self.unzip_from_branch))

    def build_commit_list(self, zip_base, zipped_branch):
        import shelve

        shelf = shelve.open('/tmp/bobby')
        key = ':'.join((zip_base, zipped_branch))
        if key not in shelf:
            print "REBUILDING"
            import re

            patt = re.compile('parent (.+)', re.MULTILINE)

            commits = CommitList()
            cmd = 'git log --pretty=oneline --reverse --first-parent %s..%s' % (zip_base, zipped_branch)
            for commit_line in run_cmd(cmd).split("\n"):
                commit = commit_line.split()[0]

                cmd = 'git cat-file -p %s' % commit
                output = run_cmd(cmd)
                parents = patt.findall(output)

                commit_obj = Commit(hash=commit, parents=parents)
                commits.append(commit_obj)
            shelf[key] = commits
        return shelf[key]

    def make_merge_list_and_tag(self, commits):
        mrglist = MergeList()
        mrglist.set_tagger(self.tagger)
        # Tag all of the commits surrounding merges
        for i, commit in enumerate(commits):
            if commit.is_merge:
                next_commit = commits[i + 1]
                _merge = mrglist.add_merge(commit=commit, next_commit=next_commit)
                _merge.make_tags()
        return mrglist

    def process_merge(self, merge, prev_merge):
        self.logger.critical('Working on merge #%s' % merge.merge_no)

        if self.tagger.tag_exists(merge.get_tag_name('complete')):
            self.logger.info('Already completed merge #%s, moving on' % merge.merge_no)
            return

        self.logger.info('Need to keep going on, no complete tag found')

        if prev_merge:
            # Rebase current completed state onto new destination
            self.logger.info('Rebasing old base onto new working base')
            if not self.tagger.tag_exists(merge.get_tag_name('base_new')):
                self.tagger.rebase_and_tag(
                    tag=merge.get_tag_name('base_new', False),
                    new_base=merge.get_tag_name('base'),
                    old_base=prev_merge.get_tag_name('base')
                )

            new_base = merge.get_tag_name('base_new')
            old_base = prev_merge.get_tag_name('actual')
        else:
            new_base = merge.get_tag_name('base')
            old_base = self.tagger.format_tag('unzip-base')

        # Run reset twice to clear out any untracked things (not sure why it doesn't work the first time)
        run_cmd('git reset %s --hard' % merge.get_tag_name('pre'))
        run_cmd('git reset %s --hard' % merge.get_tag_name('pre'))
        run_cmd('git clean -fd', debug=False)

        self.tagger.rebase_and_tag(
            tag=merge.get_tag_name('complete', False),
            new_base=new_base,
            old_base=old_base
        )

        # Compare against old for goodness sakes
        print run_cmd('git diff --stat %s %s' % (merge.get_tag_name('complete'), merge.get_tag_name('actual')))

    def process_last_chunk(self, prev_merge):
        self.logger.info('Rebasing the last chunk of the branch onto the newly unzipped branch')
        run_cmd('git reset %s --hard' % self.zipped_branch)
        run_cmd('git reset %s --hard' % self.zipped_branch)
        run_cmd('git rebase --onto %s %s' % (prev_merge.get_tag_name('complete'), prev_merge.get_tag_name('actual')))

    def cleanup(self):
        # Delete all the tags created
        related_tags = [tag for tag in run_cmd('git tag').split("\n") if tag.startswith(self.tagger.base)]
        run_cmd('git tag -d %s' % ' '.join(related_tags))

    def run(self):
        assert isinstance(self.logger, logging.Logger)
        self.logger.info("Going to try to unzip %s from %s" % (self.zipped_branch, self.unzip_from_branch))
        self.logger.info('Going to be unzipping from %s to %s' % (self.zipped_branch, self.zip_base))

        # Tag the merge base
        self.tagger.make_tag('unzip-base', self.zip_base)

        # Build out the commit list
        commits = self.build_commit_list(self.zip_base, self.zipped_branch)

        # Make merge list
        mrglist = self.make_merge_list_and_tag(commits)

        self.logger.critical('-' * 100)

        # Make a worker branch
        run_cmd('git checkout -B %s' % self.tagger.format_tag('work'))

        prev_merge = None
        for merge in mrglist:
            self.process_merge(merge, prev_merge)
            prev_merge = merge

        self.logger.info('Completed merges unzipping')

        # If we're all done with merges, let's just tidy up
        self.process_last_chunk(prev_merge)

        # If we finally got here, it's time to clean up
        self.cleanup()
