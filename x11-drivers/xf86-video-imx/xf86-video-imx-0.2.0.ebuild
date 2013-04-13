# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=3
XORG_EAUTORECONF="yes"
inherit xorg-2

DESCRIPTION="xf86 imx driver"
HOMEPAGE=""

# the source package was extracted from Genesi git repo 4/7/2013
#  no changes for the last two years
SRC_URI="mirror://gentoo/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~arm"
IUSE=""

RDEPEND="~x11-base/xorg-server-1.11.4-r1
	>=x11-libs/libz160-bin-${PV}"

DEPEND="${RDEPEND}
	x11-proto/fontsproto
	x11-proto/randrproto
	x11-proto/renderproto
	x11-proto/videoproto
	x11-proto/xproto
	>=sys-libs/imx-lib-${PV}"

