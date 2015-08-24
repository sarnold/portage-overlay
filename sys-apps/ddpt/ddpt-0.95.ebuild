# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2

AUTOTOOLS_AUTORECONF=1

inherit autotools-utils linux-info

DESCRIPTION="Enhanced dd-like utility with SCSI-passthrough support"
HOMEPAGE="http://sg.danny.cz/sg/ddpt.html"
SRC_URI="http://sg.danny.cz/sg/p/${P}.tgz"

LICENSE="FreeBSD"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~x86"
IUSE="doc +sgv4 +system-libsgutils"

DEPEND="sgv4? ( >=sys-kernel/linux-headers-2.6.29 )
	system-libsgutils? ( sys-apps/sg3_utils )"
RDEPEND="${DEPEND}"

AUTOTOOLS_PRUNE_LIBTOOL_FILES="modules"
AUTOTOOLS_IN_SOURCE_BUILD=1

DOCS=( AUTHORS
	ChangeLog
	CREDITS
	INSTALL
	NEWS
	README
	TODO
	doc/ddpt_examples.txt )

# skipping tests for now
RESTRICT="test"

pkg_setup() {
	use sgv4 && CONFIG_CHECK+=" ~BLK_DEV_BSG"

	linux-info_pkg_setup
}

src_configure() {
	local myeconfargs
		use sgv4 || myeconfargs+=( --disable-linuxbsg )
		use system-libsgutils || myeconfargs+=( --disable-libsgutils )

	autotools-utils_src_configure
}
