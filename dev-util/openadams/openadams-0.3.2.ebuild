# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

PYTHON_COMPAT=( python2_7 )
PYTHON_REQ_USE="sqlite,xml"

inherit eutils fdo-mime python-single-r1 toolchain-funcs

DESCRIPTION="an Artifact Documentation And Management System to document and manage software engineering artifacts"
HOMEPAGE="http://openadams.sourceforge.net/"

if [[ ${PV} = 9999* ]]; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/sarnold/openadams"
	DISTUTILS_IN_SOURCE_BUILD=1
else
	SRC_URI="mirror://sourceforge/${PN}/${P}.zip
		https://github.com/sarnold/openadams/raw/master/logo.jpg -> ${PN}.jpg
	"
fi

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~x86"
IUSE=""

RDEPEND="${DEPEND}
	virtual/jpeg:0
	dev-python/PyQt4[X,sql,${PYTHON_USEDEP}]"

DEPEND=""

DOCS="CHANGELOG.txt README.txt"

pkg_setup() {
	python-single-r1_pkg_setup
}

src_prepare() {
	if [[ ${PV} = 9999* ]]; then
		cp "${S}"/_naf_version.tmpl "${S}"/_naf_version.py
	fi
}

src_install() {
	dobin "${FILESDIR}"/oa_*

	insinto /usr/share/"${PN}"
	doins {_,naf,oa}*.* filepicker.py PKG-INFO COPYING.txt

	dodoc $DOCS

	doicon "${DISTDIR}"/"${PN}".jpg
	make_desktop_entry oa_editor "${PN} artifact editor" "${PN}".jpg
	make_desktop_entry oa_logview "${PN} log viewer" "${PN}".jpg
	make_desktop_entry oa_testrunner "${PN} test runner" "${PN}".jpg

	python_export EPYTHON PYTHON
	python_optimize "${D}"/usr/share/"${PN}"
}

pkg_postinst() { fdo-mime_desktop_database_update; }
pkg_postrm() { fdo-mime_desktop_database_update; }
