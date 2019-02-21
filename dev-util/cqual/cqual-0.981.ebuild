# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"
WANT_AUTOCONF="2.5"

AUTOTOOLS_AUTORECONF=1

inherit autotools-utils flag-o-matic

DESCRIPTION="Cqual is a type-based analysis tool for checking properties of C programs."
HOMEPAGE="http://www.cs.umd.edu/~jfoster/cqual/"
SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~x86"

IUSE="debug doc +emacs"

RDEPEND="emacs? ( app-editors/emacs )"

DEPEND="${RDEPEND}
	sys-devel/bison
	sys-devel/flex
	sys-libs/zlib"

AUTOTOOLS_IN_SOURCE_BUILD=1

src_configure() {
	strip-unsupported-flags

	autotools-utils_src_configure
}
