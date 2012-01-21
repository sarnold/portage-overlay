# Copyright 1999-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils

IUSE="vorbis"

DESCRIPTION="Greg Stein's python streaming audio server for desktop or LAN use"
HOMEPAGE="http://edna.sourceforge.net/"

SRC_URI="mirror://sourceforge/${PN}/${P}.tar.gz"

SLOT="0"
LICENSE="GPL-2"
KEYWORDS="~alpha ~amd64 ~hppa ~mips ~ppc ~ppc64 ~sparc ~x86"

DEPEND="dev-lang/python
	vorbis? ( dev-python/pyogg
		dev-python/pyvorbis )"

src_unpack() {
	unpack ${A}
	cd ${S}
	#if has_version '>=dev-lang/python-2.3' ; then
	#	epatch ${FILESDIR}/${P}-pep-0263.patch || die "epatch failed"
	#fi
}

src_install() {
	elog "Installing in daemon mode"
	newinitd ${FILESDIR}/edna.gentoo edna
	dosed "s:usr/lib/edna:usr/$(get_libdir)/edna:g" /etc/init.d/edna

	dodir /usr/bin /usr/$(get_libdir)/edna /usr/$(get_libdir)/edna/templates
	exeinto /usr/bin ; newexe edna.py edna
	exeinto /usr/$(get_libdir)/edna ; doexe ezt.py
	exeinto /usr/$(get_libdir)/edna ; doexe MP3Info.py
	insinto /usr/$(get_libdir)/edna/templates
	insopts -m 644
	doins templates/*
	insinto /usr/$(get_libdir)/edna/resources
	doins resources/*

	insinto /etc/edna
	insopts -m 644
	doins edna.conf
	dosym /usr/$(get_libdir)/edna/templates /etc/edna/templates
	dosym /usr/$(get_libdir)/edna/resources /etc/edna/resources

	dodoc README ChangeLog
	dohtml -r www/*
}

pkg_postinst() {
	ewarn
	elog "Edit edna.conf to taste before starting (multiple source"
	elog "directories are allowed).  Test edna from a shell prompt"
	elog "until you have it configured properly, then add edna to"
	elog "the default runlevel when you're ready.  Add the USE flag"
	elog "vorbis if you want edna to serve ogg files."
	elog
	elog "See edna.conf and the html docs for more info, and set"
	elog "PYTHONPATH=/usr/$(get_libdir)/edna to run from a shell prompt."
	ewarn
}
