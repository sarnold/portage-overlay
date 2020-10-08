# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6
PYTHON_COMPAT=( python2_7 python3_{5,6,7} pypy{,3} )

inherit distutils-r1

DESCRIPTION="Separate test code from test cases in pytest"
HOMEPAGE="https://github.com/smarie/python-pytest-cases https://pypi.python.org/pypi/pytest-cases/"
SRC_URI="mirror://pypi/${P:0:1}/${PN}/${P}.tar.gz"

LICENSE="BSD"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~x86"
IUSE=""

RDEPEND="
	dev-python/pytest[${PYTHON_USEDEP}]
	dev-python/decopatch[${PYTHON_USEDEP}]
	dev-python/makefun[${PYTHON_USEDEP}]
	dev-python/wrapt[${PYTHON_USEDEP}]
	$(python_gen_cond_dep \
		'dev-python/functools32[${PYTHON_USEDEP}]' 'python2*' pypy)
	virtual/python-funcsigs
	virtual/python-enum34
"

DEPEND="
	dev-python/setuptools[${PYTHON_USEDEP}]
	dev-python/setuptools_scm[${PYTHON_USEDEP}]
	dev-python/pytest-runner[${PYTHON_USEDEP}]
	dev-python/six[${PYTHON_USEDEP}]
"
