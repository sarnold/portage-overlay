# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=4

inherit autotools flag-o-matic eutils

DESCRIPTION="IBM's open source, high performance Java compiler"
HOMEPAGE="http://jikes.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${P}.tar.bz2"

LICENSE="IBM"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~ppc64 ~x86 ~x86-fbsd"
IUSE=""
DEPEND=""
RDEPEND=">=dev-java/java-config-2.0.0"

pkg_setup() {
	filter-flags "-fno-rtti"
}

src_prepare() {
	epatch "${FILESDIR}"/deprecated.patch

	eautoreconf
}

src_install () {
	emake DESTDIR="${D}" install
	dodoc ChangeLog AUTHORS README TODO NEWS

	mv "${D}"/usr/bin/jikes{,-bin}
	dobin "${FILESDIR}"/jikes

	insinto /usr/share/java-config-2/compiler
	newins "${FILESDIR}"/compiler-settings jikes

	rm -rf "${D}"/usr/share/doc/${P}
}
