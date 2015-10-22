# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="4"

inherit eutils toolchain-funcs

DESCRIPTION="Computes cyclomatic complexity metrics on C source code."
HOMEPAGE="https://github.com/sarnold/cyclo"

if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="https://github.com/sarnold/cyclo.git"
	inherit git-r3
else
	SRC_URI="https://github.com/sarnold/cyclo/archive/2.1_pre1.tar.gz -> ${P}.tar.gz"
fi

KEYWORDS="~alpha ~amd64 ~hppa ~ia64 ~mips ~ppc ~ppc64 ~sparc ~x86 ~x86-fbsd"
SLOT="0"
LICENSE="GPL-2"
IUSE="debug"

DEPEND="sys-devel/flex"

src_compile() {
	if ! use debug ; then
		DBG="" make all || die "make failed"
	else
		DBG="${DEBUG}" make all || die "make debug failed"
	fi
}

src_install() {
	dobin cyclo mcstrip

	doman cyclo.0 mcstrip.1 cyclo.1
	dodoc README.rst mccabe.example || die "dodoc failed"
}
