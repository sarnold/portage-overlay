# Copyright 1999-2019 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6
PYTHON_COMPAT=( python3_{5,6,7} )

inherit distutils-r1 eutils

DESCRIPTION="Python/Curses front-end for Taskwarrior (app-misc/task)"
HOMEPAGE="https://github.com/scottkosty/vit"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/scottkosty/vit.git"
	inherit git-r3
	KEYWORDS=""
else
	SRC_URI="https://github.com/scottkosty/${PN}/archive/v${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~arm64 ~x86"
fi

LICENSE="MIT"
SLOT="0"
IUSE=""

DEPEND="dev-python/tasklib[${PYTHON_USEDEP}]
	dev-python/pytz[${PYTHON_USEDEP}]
	dev-python/tzlocal[${PYTHON_USEDEP}]
	dev-python/urwid[${PYTHON_USEDEP}]"

RDEPEND="${DEPEND}"
