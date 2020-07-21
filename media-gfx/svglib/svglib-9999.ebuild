# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=7

PYTHON_COMPAT=( python3_{6,7,8} )
PYTHON_REQ_USE="threads(+)"

inherit distutils-r1

DESCRIPTION="A pure-Python library for reading and converting SVG"
HOMEPAGE="https://github.com/deeplook/svglib"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/deeplook/svglib.git"
	EGIT_BRANCH="master"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/deeplook/${PN}/archive/v${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
fi

LICENSE="LGPL-3.0"
SLOT="0"
IUSE=""
REQUIRED_USE="${PYTHON_REQUIRED_USE}"

RESTRICT="!test? ( test )"

DEPEND="dev-python/reportlab[${PYTHON_USEDEP}]
	dev-python/lxml[${PYTHON_USEDEP}]
	dev-python/tinycss2[${PYTHON_USEDEP}]
	dev-python/cssselect2[${PYTHON_USEDEP}]
	dev-python/setuptools[${PYTHON_USEDEP}]
"

BDEPEND="test? ( dev-python/pytest[${PYTHON_USEDEP}] )
"

distutils_enable_sphinx docs
distutils_enable_tests pytest
