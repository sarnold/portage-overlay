# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6
PYTHON_COMPAT=( python3_{5,6,7} pypy3 )

inherit distutils-r1 git-r3

DESCRIPTION="Creates a changelog from git log history"
HOMEPAGE="https://github.com/vaab/gitchangelog https://pypi.python.org/pypi/gitchangelog/"
EGIT_REPO_URI="https://github.com/vaab/gitchangelog"

if [[ ${PV} = 9999* ]]; then
	EGIT_BRANCH="master"
else
	EGIT_COMMIT="${PV}"
fi

KEYWORDS="~amd64 ~arm ~arm64 ~x86"
LICENSE="BSD"
SLOT="0"
IUSE="test"

RDEPEND="${PYTHON_DEPS}
	dev-python/pystache[${PYTHON_USEDEP}]
	dev-python/mako[${PYTHON_USEDEP}]
"

DEPEND="${PYTHON_DEPS}
	dev-python/setuptools[${PYTHON_USEDEP}]
	dev-python/d2to1[${PYTHON_USEDEP}]
	test? ( dev-python/nose[${PYTHON_USEDEP}]
		dev-python/minimock[${PYTHON_USEDEP}] )
"

python_test() {
	"${EPYTHON}" -m nose -sx . || die "Testing failed with ${EPYTHON}"
}
