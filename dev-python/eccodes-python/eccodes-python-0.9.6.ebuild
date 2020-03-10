# Copyright 1999-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6

PYTHON_COMPAT=( python3_{6,7} )

inherit distutils-r1

DESCRIPTION="Python/numpy interface to the eccodes C library"
HOMEPAGE="https://confluence.ecmwf.int/display/ECC/Python+3+interface+for+ecCodes"
SRC_URI="https://github.com/ecmwf/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"

SLOT="0"
LICENSE="Apache-2.0"
KEYWORDS="~amd64 ~arm ~arm64 ~x86"
IUSE="test"

RDEPEND="
	dev-python/numpy[${PYTHON_USEDEP}]
	dev-python/attrs[${PYTHON_USEDEP}]
	dev-python/cffi:=[${PYTHON_USEDEP}]
	>=sci-libs/eccodes-2.16.0[python]
"
BDEPEND="${RDEPEND}"

RESTRICT="!test? ( test )"

# PATCHES=( "${FILESDIR}/${PN}-ignore-test-import-warnings.patch" )
