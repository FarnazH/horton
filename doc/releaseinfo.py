"""Determine release info."""

import datetime
import json
import subprocess


def transform_git_date(s):
    """Convert a date printed by git into a more condensed one."""
    words = s.split()
    return '%s %02i, %s' % (words[1], int(words[2]), words[4])


def get_releaseinfo():
    """Retrieve release info from git and also write releaseinfo.json."""
    # Default values in case the git commands don't work
    version = '2.1.0b3'
    describe = '%s-nogit' % version
    release_date = '??? ??, ????'
    doc_release_date = release_date
    doc_build_date = datetime.datetime.now().strftime('%b %d, %Y')

    # get a version strings from git commands
    try:
        # The date of the commit for which the docs are generated.
        doc_git_date = subprocess.check_output(['git', 'show', '--format=%cd', 'HEAD'])
        doc_release_date = transform_git_date(doc_git_date)
        # The full version description, including extra info if not at tag.
        describe = subprocess.check_output(['git', 'describe', '--tags']).strip()
        if '-' in describe:
            version = describe.split('-')[0]
        else:
            version = describe
        git_date = subprocess.check_output(['git', 'show', '--format=%cd', version])
        release_date = transform_git_date(git_date)
    except (subprocess.CalledProcessError, OSError):
        pass

    # Make a dictionary
    releaseinfo = {
        'version': version,
        'describe': describe,
        'release_date': release_date,
        'doc_release_date': doc_release_date,
        'doc_build_date': doc_build_date,
    }

    # Write json file
    with open('releaseinfo.json', 'w') as f:
        json.dump(releaseinfo, f)

    return releaseinfo
