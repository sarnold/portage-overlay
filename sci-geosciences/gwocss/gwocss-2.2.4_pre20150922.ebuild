# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

FORTRAN_STANDARD="77 90 95"

inherit autotools eutils fortran-2 toolchain-funcs user

if [[ ${PV} == *9999* ]]; then
	EGIT_REPO_URI="https://github.com/sarnold/gwocss.git"
	inherit git-2
else
	KEYWORDS="~amd64 ~arm ~hppa ~ia64 ~mips ~ppc ~ppc64 ~x86"
	SRC_URI="https://github.com/sarnold/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
fi

DESCRIPTION="A diagnostic windfield model for complex terrain"
HOMEPAGE="http://sarnold.github.io/gwocss/"

LICENSE="GPL-3"
SLOT="0"
IUSE="doxygen demo"

RDEPEND=""
DEPEND="${RDEPEND}
	doxygen? ( app-doc/doxygen )"

DOCS="AUTHORS CHANGELOG.md NEWS README docs/GWOCSS_overview.pdf"

GWOCSS_DIR=/var/lib/gwocss

pkg_setup() {
	fortran-2_pkg_setup

	enewgroup gwocss
	enewuser gwocss -1 -1 ${GWOCSS_DIR} gwocss
}

src_prepare() {
	epatch "${FILESDIR}"/${PN}-ebuild_update.patch \
		"${FILESDIR}"/${PN}-init_update.patch

	eaclocal
	eautomake
	eautoconf
}

src_configure() {
	FC=$(tc-getFC) FFLAGS=${FCFLAGS} econf
}

src_install() {
	default

	if use doxygen ; then
		dohtml -r docs/html
	fi

	# the rest of this is for installing the reference data as the demo
	# modeling domain and making everything gwocss group-writable

	if use demo ; then
		local inputdir="${GWOCSS_DIR}/demo/slcin"
		local demodirs="${GWOCSS_DIR}/demo ${inputdir} ${GWOCSS_DIR}/demo/slcout"
	fi

	keepdir ${GWOCSS_DIR} ${demodirs}
	fowners gwocss:gwocss ${GWOCSS_DIR} ${demodirs}
	fperms 2775 ${GWOCSS_DIR} ${demodirs}

	if use demo ; then
		insinto ${inputdir}
		doins "${S}"/slcin/*
		fowners gwocss:gwocss ${inputdir}/{10162215WXIN,RUNSTF1.DAT,SLC1KM.DAT,SLCFILES}
		fperms 0775 ${inputdir}/{10162215WXIN,RUNSTF1.DAT,SLC1KM.DAT,SLCFILES}
	fi

	use demo || sed -i -e "s|demo||" "${S}"/packaging/gentoo/${PN}.confd
	newinitd "${S}"/packaging/gentoo/${PN}.init gwocss
	newconfd "${S}"/packaging/gentoo/${PN}.confd gwocss
}

pkg_postinst() {
	elog ""
	elog "The model reference data discussed in the overview is kept"
	elog "for testing and comparison purposes, as well as installed"
	elog "in ${GWOCSS_DIR}/demo as the default domain (for use=demo)."
	elog "To run the system-wide binary, add yourself to the gwocss"
	elog "group and set ENABLE=yes in /etc/conf.d/gwocss, then run"
	elog "the 'gwocss' command with a configured domain and inputs."
	elog "The conf file is used by both the init and wrapper scripts;"
	elog "the init script simply checks/fixes permissions under the"
	elog "${GWOCSS_DIR}/<domain> directories."
	elog ""
}

pkg_prerm() {
	elog ""
	elog "Existing modeling domains under ${GWOCSS_DIR}"
	elog "are not removed, so you will need to archive and remove"
	elog "by hand (including the demo domain)."
	elog ""
}
