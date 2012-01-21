# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils multilib qt4-r2

MY_P="${PN}${PV}"

DESCRIPTION="GUI for controlling running VM in virtual pc emulator qemu"
HOMEPAGE="http://qemuctl.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/source/${MY_P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"
IUSE=""

RDEPEND="x11-libs/qt-gui:4
	x11-libs/qt-core:4
	x11-libs/libX11
	x11-libs/libXext
	dev-libs/glib:2
	>=app-emulation/qemu-0.10.1"

DEPEND="${RDEPEND}
	x11-proto/xextproto
	x11-proto/xproto"

S="${WORKDIR}/${MY_P}"

src_configure() {
	eqmake4
}
src_install() {
	emake INSTALL_ROOT="${D}" install || die "install failed"
}
