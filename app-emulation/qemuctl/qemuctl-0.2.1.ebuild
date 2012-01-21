# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils

DESCRIPTION="GUI for controlling running VM in virtual pc emulator qemu"
HOMEPAGE="http://qemuctl.sourceforge.net/"
SRC_URI="mirror://gentoo/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"
IUSE=""

DEPEND="dev-lang/perl
    >=dev-perl/gtk2-perl-1.121
    >=dev-util/glade-2.0
    >=app-emulation/qemu-0.8.1"

## upstream tarball for this release is dorked in that the name should
## be a .tar instead of .tar.gz (the correct package is on the mirrors)
## as well as having a weird name in the first place...
src_prepare() {
	epatch "${FILESDIR}"/${P}-gtk-fix.patch
	epatch "${FILESDIR}"/${P}-makefile-fix.patch
	sed -i -e "s|doc/qemu-launcher|doc/${PN}-${PV}|" \
		Makefile
}

src_install() {
	make DESTDIR=${D} install
}
