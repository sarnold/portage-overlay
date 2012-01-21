# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

inherit eutils

DESCRIPTION="Some bash script-foo for running apps under Gnome/Nautilus."
HOMEPAGE="http://hacktolive.org/wiki/App_Runner"
SRC_URI="mirror://gentoo/${P}.tar.gz"

LICENSE="as-is"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"
IUSE="skeldir"

RDEPEND="gnome-base/nautilus"

DEPEND="${RDEPEND}
	dev-util/pkgconfig"

DOCS="PKG_INFO"

src_compile() {
	echo "Nothing to see here...  Move along..."
}

src_install() {
	dobin bin/app-runner bin/app-runner-launch

	stagingdir="/var/cache/hacktolive/${PN}"
	exeinto ${stagingdir}
	doexe scripts/*

	if use skeldir ; then
		exeinto /etc/skel/.gnome2/nautilus-scripts
		doexe scripts/*
	fi

	dodoc ${DOCS}
}

pkg_postinst() {
	elog ""
	ewarn "Note, you still need to copy the launcher scripts to your home"
	ewarn "dir to make the menu show up in Nautilus:"
	ewarn "  cp /var/cache/hacktolive/${PN}/* \${HOME}/.gnome2/nautilus-scripts/"
	elog ""
}

pkg_postrm() {
	python_mod_cleanup ${extensiondir}/python
}
