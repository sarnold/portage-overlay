# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6

PYTHON_COMPAT=( python2_7 python{3_5,3_6,3_7} )

inherit distutils-r1

DESCRIPTION=""
HOMEPAGE="https://github.com/tonysimpson/nanomsg-python"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/tonysimpson/nanomsg-python.git"
	EGIT_BRANCH="master"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/tonysimpson/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
	PATCHES=( "${FILESDIR}/${P}-change-LINGER-to-SNDBUF.patch" )
fi

LICENSE="MIT"
SLOT="0"
IUSE="test"

RDEPEND="${PYTHON_DEPS}"

DEPEND="${PYTHON_DEPS}
	dev-libs/nanomsg:=
	dev-python/setuptools[${PYTHON_USEDEP}]
	test? ( dev-python/nose[${PYTHON_USEDEP}] )
"

python_test() {
	"${EPYTHON}" -m nose -sv . || die "Testing failed with ${EPYTHON}"
}
