# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"

inherit eutils toolchain-funcs

DESCRIPTION="SLiM + slock = slimlock"
HOMEPAGE="https://github.com/dannyn/slimlock"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/sarnold/cyclo.git"
	inherit git-r3
else
	SRC_URI="https://github.com/dannyn/slimlock/archive/v0.12.tar.gz -> ${P}.tar.gz"
fi

KEYWORDS="~alpha ~amd64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~sparc ~x86 ~x86-fbsd"
SLOT="0"
LICENSE="GPL-2"
IUSE=""

DEPEND="virtual/pam
	x11-misc/slim"

