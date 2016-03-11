# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

PYTHON_COMPAT=( python3_{3,4} )

inherit distutils-r1

DESCRIPTION="a text-based Requirements Management tool"
HOMEPAGE="http://doorstop.info"

if [[ ${PV} = 9999* ]]; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/VCTLabs/openadams"
	KEYWORDS=""
else
	SRC_URI="https://github.com/jacebrowning/${PN}/archive/v${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~x86"
fi

LICENSE="LGPL-3"
SLOT="0"
IUSE=""

RDEPEND="${DEPEND}
	>=dev-python/pyyaml-3[${PYTHON_USEDEP}]
	dev-python/markdown[${PYTHON_USEDEP}]
	=dev-python/openpyxl-2.1*[${PYTHON_USEDEP}]
	dev-python/bottle[${PYTHON_USEDEP}]
	dev-python/requests[${PYTHON_USEDEP}]
	dev-python/pyficache[${PYTHON_USEDEP}]
"

DEPEND=""

DOCS="CHANGES.md README.md"
