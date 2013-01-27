# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

PATCHVER="1.0"
ELF2FLT_VER=""
inherit toolchain-binutils

KEYWORDS="~alpha ~amd64 ~arm ~hppa ~ia64 ~m68k ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 -amd64-fbsd -sparc-fbsd -x86-fbsd"

src_unpack() {
	toolchain-binutils_src_unpack
	epatch ${FILESDIR}/${PN}-2.23-gold-pt-pax-flags.patch
}
