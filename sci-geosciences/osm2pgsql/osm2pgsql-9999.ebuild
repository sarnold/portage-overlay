# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2

inherit subversion toolchain-funcs

DESCRIPTION="Tool to convert OpenStreetMap data into a format for PostgreSQL"
HOMEPAGE="http://wiki.openstreetmap.org/wiki/Osm2pgsql"
#SRC_URI="mirror://gentoo/${P}.tar.bz2"
ESVN_REPO_URI="http://svn.openstreetmap.org/applications/utils/export/${PN}"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~x86"
IUSE="debug mapnik"

RDEPEND="dev-libs/libxml2
	virtual/postgresql-server
	dev-db/postgis
	sci-libs/proj
	sci-libs/geos
	app-arch/bzip2
	sys-libs/zlib"

DEPEND="${RDEPEND}
	mapnik? ( sci-geosciences/mapnik )"

src_prepare() {
	if use debug; then
	    sed -i -e "s:-g -O2:-g:g" Makefile || die "sed 1 failed"
	else
	    sed -i -e "s:-g -O2::g" Makefile || die "sed 2 failed"
	fi
}

src_compile() {
	emake CC="$(tc-getCC)" CXX="$(tc-getCXX)" all || die "build failed"
}

src_install() {
	dobin osm2pgsql || die "dobin failed"
	use mapnik && ( doexe mapnik-osm-updater.sh || die "doexe failed" )
	dodoc README.txt
}
