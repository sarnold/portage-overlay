# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2

inherit eutils x-modular

if [[ ${PV} == "9999" ]] ; then
	EGIT_REPO_URI="git://anongit.freedesktop.org/xorg/driver/xf86-input-joystick"
	inherit autotools git
	KEYWORDS=""
else
	KEYWORDS="alpha amd64 arm hppa ia64 ppc ppc64 sh sparc x86 ~x86-fbsd"
fi

DESCRIPTION="X.Org driver for joystick input devices"
IUSE=""

if [[ ${PV} == "9999" ]] ; then
	RDEPEND=">=x11-base/xorg-server-1.10"
else
	RDEPEND=">=x11-base/xorg-server-1.6"
fi
DEPEND="${RDEPEND}
	x11-proto/inputproto
	x11-proto/kbproto"

src_prepare() {
	eautoreconf
}
