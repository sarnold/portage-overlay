# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=7

PYTHON_COMPAT=( python3_{6,7,8} )
DISTUTILS_USE_SETUPTOOLS=rdepend

inherit distutils-r1

DESCRIPTION="Generates PDF documents from HTML content"
HOMEPAGE="https://pypi.python.org/pypi/xhtml2pdf"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/xhtml2pdf/xhtml2pdf.git"
	EGIT_BRANCH="master"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/xhtml2pdf/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
fi

LICENSE="Apache-2.0"
SLOT="0"
IUSE=""

RESTRICT="!test? ( test )"

DEPEND="dev-python/reportlab[${PYTHON_USEDEP}]
	dev-python/pillow[${PYTHON_USEDEP}]
	dev-python/PyPDF2[${PYTHON_USEDEP}]
	dev-python/html5lib[${PYTHON_USEDEP}]
	dev-python/six[${PYTHON_USEDEP}]
	dev-python/setuptools[${PYTHON_USEDEP}]
"

BDEPEND="test? ( dev-python/nose[${PYTHON_USEDEP}] )
"

distutils_enable_sphinx docs
distutils_enable_tests nose

python_install() {
	distutils-r1_python_install

	python_optimize
}
