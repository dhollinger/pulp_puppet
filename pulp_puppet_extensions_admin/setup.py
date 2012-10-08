# Copyright (c) 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from setuptools import setup, find_packages

from pulp.common.constants import ENTRY_POINT_EXTENSIONS

setup(
    name='pulp_puppet_extensions_admin',
    version='2.0.0',
    license='GPLv2+',
    packages=find_packages(),
    author='Pulp Team',
    author_email='pulp-list@redhat.com',
    entry_points = {
        ENTRY_POINT_EXTENSIONS: [
            'repo_admin = pulp_puppet.extensions.admin.repo.pulp_cli:initialize',
        ]
    }
)