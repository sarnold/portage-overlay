# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

inherit autotools-utils

DESCRIPTION="pepper is a flexible command-line tool for retrieving statistics and generating reports from source code repositories."

HOMEPAGE="http://scm-pepper.sourceforge.net/"
SRC_URI="mirror://sourceforge/scm-pepper/${P}.tar.gz"

KEYWORDS="~amd64 ~arm ~x86"
LICENSE="GPL-3+"
SLOT="0"

IUSE="apr git +gnuplot leveldb mercurial svn zlib"

RDEPEND="apr? ( dev-libs/apr-util )
	git? ( dev-vcs/git )
	gnuplot? ( sci-visualization/gnuplot )
	mercurial? ( dev-vcs/mercurial )
	svn? ( dev-vcs/subversion )
	leveldb? ( dev-libs/leveldb )
	zlib? ( sys-libs/zlib )
	dev-lang/lua"

DEPEND="${RDEPEND}
	app-text/asciidoc
	app-text/xmlto"

src_prepare() {
	autotools-utils_src_prepare
}

src_configure() {
	local myconf=""

	use zlib || myconf="--without-zlib"

	use apr && myconf="$myconf --with-apr=/usr"

myeconfargs=(
		$myconf
		$(use_enable git) \
		$(use_enable mercurial) \
		$(use_enable svn) \
		$(use_enable gnuplot) \
		$(use_enable leveldb)
	)

	autotools-utils_src_configure
}

src_install () {
	autotools-utils_src_install
	dodoc README INSTALL AUTHORS
}

