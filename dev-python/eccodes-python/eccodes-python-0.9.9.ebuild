# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6

PYTHON_COMPAT=( python3_{6,7,8} )

inherit distutils-r1

DESCRIPTION="Python/numpy interface to the eccodes C library"
HOMEPAGE="https://confluence.ecmwf.int/display/ECC/Python+3+interface+for+ecCodes"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/sarnold/eccodes-python.git"
	EGIT_BRANCH="develop"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/ecmwf/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
fi

SLOT="0"
LICENSE="Apache-2.0"
IUSE="test"

RDEPEND="${PYTHON_DEPS}"

DEPEND="${PYTHON_DEPS}
	dev-python/numpy[${PYTHON_USEDEP}]
	dev-python/attrs[${PYTHON_USEDEP}]
	dev-python/cffi:=[${PYTHON_USEDEP}]
	 >=sci-libs/eccodes-2.16.0[python]
	test? ( >=dev-python/pytest-3.0.3[${PYTHON_USEDEP}] )
"

RESTRICT="!test? ( test )"

python_test() {
	distutils_install_for_testing
	PYTHONPATH="${TEST_DIR}/lib:${PYTHONPATH}" pytest -v tests \
		|| die "Test failed with ${EPYTHON}"
}
