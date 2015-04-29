# -*- coding: utf-8 -*-
# Copyright (c) 2013-2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
import os
import sys
import subprocess

from setuptools import setup


MAJOR = 0
MINOR = 3
MICRO = 0

IS_RELEASED = True

VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)


# Return the git revision as a string
def git_version():
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, env=env,
        ).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        git_revision = out.strip().decode('ascii')
    except OSError:
        git_revision = "Unknown"

    try:
        out = _minimal_ext_cmd(['git', 'rev-list', '--count', 'HEAD'])
        git_count = out.strip().decode('ascii')
    except OSError:
        git_count = '0'

    return git_revision, git_count


def write_version_py(filename='usagi/_version.py'):
    template = """\
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

# THIS FILE IS GENERATED FROM SETUP.PY
version = '{version}'
full_version = '{full_version}'
git_revision = '{git_revision}'
is_released = {is_released}

if not is_released:
    version = full_version
"""
    fullversion = VERSION
    if os.path.exists('.git'):
        git_rev, dev_num = git_version()
    elif os.path.exists('usagi/_version.py'):
        # must be a source distribution, use existing version file
        try:
            from usagi._version import git_revision as git_rev
            from usagi._version import full_version as full_v
        except ImportError:
            raise ImportError("Unable to import git_revision. Try removing "
                              "usagi/_version.py and the build "
                              "directory before building.")
        import re
        match = re.match(r'.*?\.dev(?P<dev_num>\d+)\+.*', full_v)
        if match is None:
            dev_num = '0'
        else:
            dev_num = match.group('dev_num')
    else:
        git_rev = "Unknown"
        dev_num = '0'

    if not IS_RELEASED:
        fullversion += '.dev{0}'.format(dev_num)

    with open(filename, "wt") as fp:
        fp.write(template.format(version=VERSION,
                                 full_version=fullversion,
                                 git_revision=git_rev,
                                 is_released=IS_RELEASED))


if __name__ == "__main__":
    install_requires = [
        'jsonschema',
        'pyyaml',
        'requests',
        'six',
        'stevedore',
        'haas >= 0.6.0',
        'jq >= 0.1.3, < 0.2',
    ]
    py26_requires = ['unittest2']
    if sys.version_info < (2, 7):
        install_requires += py26_requires

    write_version_py()
    from usagi import __version__

    with open('README.rst') as fh:
        long_description = fh.read()

    setup(
        name='usagi',
        version=__version__,
        url='https://github.com/sjagoe/usagi',
        author='Simon Jagoe',
        author_email='simon@simonjagoe.com',
        classifiers=[
            'Development Status :: 1 - Planning',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: MacOS',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: OS Independent',
            'Operating System :: POSIX',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Topic :: Software Development',
            'Topic :: Software Development :: Testing',
        ],
        description='Web API testing for haas',
        long_description=long_description,
        license='BSD',
        packages=['usagi', 'usagi.plugins'],
        install_requires=install_requires,
        entry_points={
            'haas.discovery': [
                'rest-test = usagi.discoverer:RestTestDiscoverer',
                'usagi = usagi.discoverer:RestTestDiscoverer',
            ],
            'usagi.assertions': [
                'body = usagi.plugins.assertions:BodyAssertion',
                'sha256 = usagi.plugins.assertions:Sha256BodyAssertion',
                'status_code = usagi.plugins.assertions:StatusCodeAssertion',  # noqa
                'header = usagi.plugins.assertions:HeaderAssertion',
            ],
            'usagi.parameters': [
                'body = usagi.plugins.test_parameters:BodyTestParameter',  # noqa
                'headers = usagi.plugins.test_parameters:HeadersTestParameter',  # noqa
                'method = usagi.plugins.test_parameters:MethodTestParameter',  # noqa
                'queryparams = usagi.plugins.test_parameters:QueryParamsTestParameter',  # noqa
            ],
            'usagi.var_loaders': [
                'env = usagi.plugins.var_loaders:EnvVarLoader',
                'ref = usagi.plugins.var_loaders:RefVarLoader',
                'file = usagi.plugins.var_loaders:FileVarLoader',
                'template = usagi.plugins.var_loaders:TemplateVarLoader',  # noqa
            ],
        },
        extras_require={
            ':python_version=="2.6"': py26_requires,
        },
    )
