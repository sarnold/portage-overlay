# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2

inherit autotools eutils x-modular

KEYWORDS="alpha amd64 arm hppa ia64 ppc ppc64 sh sparc x86 ~x86-fbsd"

DESCRIPTION="X.Org driver for joystick input devices (from GIT master @ ABI 12)"
SRC_URI="mirror://gentoo/${P}.tar.gz"
IUSE=""

RDEPEND=">=x11-base/xorg-server-1.10"

DEPEND="${RDEPEND}
	x11-proto/inputproto
	x11-proto/kbproto"

src_prepare() {
	eautoreconf
}
