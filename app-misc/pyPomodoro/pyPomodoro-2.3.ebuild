# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="5"
PYTHON_COMPAT=( python2_7 )

inherit eutils python-r1 fdo-mime

MY_P="${PN}${PV}"

DESCRIPTION="Graphical software timer to deal with the Pomodoro Technique."
HOMEPAGE="http://code.google.com/p/pypomodoro/"
SRC_URI="http://pypomodoro.googlecode.com/files/${MY_P}.tgz"

LICENSE="Apache-2.0"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~hppa ~ia64 ~mips ~ppc ~ppc64 ~sh ~sparc ~x86 ~amd64-linux ~x86-linux ~x64-macos ~x86-macos ~x86-solaris"
IUSE="+gui"

DEPEND="dev-python/wxpython:2.8
	gui? ( media-gfx/imagemagick )"

RDEPEND="${DEPEND}
	dev-python/gdata"

RESTRICT_PYTHON_ABIS="2.4 3.*"

pkg_setup() {
	python_set_active_version 2
}

src_unpack() {
	mkdir -p "${WORKDIR}/${P}"
	cd "${S}"
	unpack "${A}"
}

src_prepare() {
	convert "${S}"/img/ico.ico pyPomodoro.png
	python_convert_shebangs -r 2 .
}

src_install() {
	newbin run.sh pyPomodoro.sh || die "newbin failed"
	rm *.sh
	insinto $(python_get_sitedir)/${PN}
	doins -r "${S}"/[a-z]*
	dosed \
		"s|exec|$(PYTHON -a)|" \
		"s|./|$(python_get_sitedir)/${PN}/|" \
		/usr/bin/pyPomodoro.sh

	dodoc "${FILESDIR}/README"

	if use gui; then
		doicon pyPomodoro.png
		make_desktop_entry pyPomodoro.sh "pyPomodoro ${PV}" \
			"pyPomodoro.png" "Utility;GTK;"
	fi
}

pkg_postinst() {
	if use gui; then
		validate_desktop_entries
		fdo-mime_desktop_database_update
	fi
}

pkg_postrm() {
	use gui && fdo-mime_desktop_database_update
}
