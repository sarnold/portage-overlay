# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit autotools flag-o-matic eutils toolchain-funcs fdo-mime

MY_P="NG4.2"
S=${WORKDIR}/sourcenavigator-${MY_P}
SB=${WORKDIR}/snbuild
SN="/opt/sourcenav"

DESCRIPTION="SourceNavigator NG is a source code analysis and software development tool"
SRC_URI="mirror://berlios/sourcenav/sourcenavigator-${MY_P}.tar.bz2"
HOMEPAGE="http://sourcenav.berlios.de/"

SLOT="0"
LICENSE="GPL-2 LGPL-2"
KEYWORDS="~amd64 ~sparc ~ppc ~ppc64 ~x86"
IUSE="debug"

RDEPEND="x11-libs/libX11
	x11-libs/libXdmcp
	x11-libs/libXaw
	sys-libs/glibc"

DEPEND="${RDEPEND}
	x11-proto/xproto"

WANT_AUTOCONF="2.5"
AT_M4DIR="${S}/config"

src_prepare() {
	#epatch "${FILESDIR}"/${PN}_destdir.patch
	eaclocal
}

src_compile() {
	append-flags -DHAVE_STDLIB_H=1 -D_GNU_SOURCE=1
	sh ./configure "${MY_CONF}" \
		--host="${CHOST}" \
		--prefix="${SN}" \
		--bindir="${SN}"/bin \
		--sbindir="${SN}"/sbin \
		--exec-prefix="${SN}" \
		--mandir="${SN}"/share/man \
		--infodir="${SN}"/share/info \
		--datadir="${SN}"/share \
		$(use_enable debug symbols) || die "configure failed"

	make all || die "make failed"
}

src_install() {
	# bug #298858
	emake -j1 DESTDIR="${D}" install || die "install failed"

	chmod -Rf 755 "${D}/${SN}/share/doc/${P}/demos"
	dodir /etc/env.d
	echo "PATH=${SN}/bin" > "${D}"/etc/env.d/10snavigator

	make_desktop_entry \
		/opt/sourcenav/bin/snavigator \
		"Source Navigator ${PV}" \
		"/opt/sourcenav/share/bitmaps/ide_icon.xpm" \
		"Application;Development"
}

pkg_postinst() {
	fdo-mime_desktop_database_update
}

pkg_postrm() {
	fdo-mime_desktop_database_update
}
