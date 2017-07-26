# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

inherit base eutils

DESCRIPTION="A tool for porting libtoolized software to Android."
HOMEPAGE="http://cgit.collabora.com/git/user/derek/androgenizer.git"
SRC_URI="mirror://gentoo/${P}.tar.gz"

LICENSE="as-is"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~ppc ~ppc64 ~sparc ~x86 ~amd64-linux ~x86-linux ~ppc-macos ~x86-macos"

IUSE="debug"

src_prepare() {
	if ! use debug; then
		sed -i -e "s|-Wall -g3|${CFLAGS}|" ${S}/Makefile
	fi
}

src_compile() {
	make all
}

src_install() {
	dobin androgenizer
	dodoc USAGE.txt
}

pkg_postinst() {
	elog "See the USAGE.txt file for a brief usage description; for a more"
	elog "detailed discussion, see http://blogs.igalia.com/eocanha/?p=242"
}
