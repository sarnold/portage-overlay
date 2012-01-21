# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

DESCRIPTION="GNOME/Gtk front-end for the Qemu x86 PC emulator"
HOMEPAGE="http://projects.wanderings.us/qemu_launcher"
SRC_URI="http://download.gna.org/qemulaunch/1.7.x/${PN}_${PV}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"
IUSE=""

DEPEND="dev-lang/perl
	>=dev-perl/gtk2-perl-1.121
	>=dev-perl/gtk2-gladexml-1.005
	>=dev-perl/gnome2-perl-1.023
	>=dev-perl/Locale-gettext-1.05
	>=app-emulation/qemu-0.8.1"

RDEPEND="${DEPEND}
	app-emulation/qemuctl"

src_prepare() {
	sed -i -e "s|usr/local|usr/|" \
		-e "s|doc/qemu-launcher|doc/${P}|" \
		Makefile
}

src_compile() {
	emake || die "emake failed"
}

src_install() {
	make DESTDIR=${D} install
}
