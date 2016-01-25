# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

PYTHON_COMPAT=( python2_7 )
DISTUTILS_SINGLE_IMPL=1
PYTHON_REQ_USE="sqlite,xml"

inherit eutils fdo-mime distutils-r1

DESCRIPTION="an Artifact Documentation And Management System to document and manage software engineering artifacts"
HOMEPAGE="http://openadams.sourceforge.net/"

if [[ ${PV} = 9999* ]]; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/VCTLabs/openadams"
	KEYWORDS=""
else
	SRC_URI="mirror://sourceforge/${PN}/${P}.zip
		https://github.com/VCTLabs/openadams/raw/master/logo.jpg -> ${PN}.jpg
	"
	KEYWORDS="~amd64 ~arm ~x86"
fi

LICENSE="GPL-2"
SLOT="0"
IUSE="doc"

DEPEND="virtual/jpeg:0
	dev-python/PyQt4[X,sql,${PYTHON_USEDEP}]"

RDEPEND="${DEPEND}"

DOCS="CHANGELOG.txt README.txt"

src_install() {
	insinto /usr/share/"${PN}"
	doins {_,naf,oa}*.* filepicker.py

	dobin "${FILESDIR}"/oa_*

	dodoc $DOCS

	if [[ ${PV} = 9999* ]]; then
		newicon "${S}"/logo.jpg "${PN}".jpg
		# use doc && dohtml -A db,shtml,svg -r docs
		# append weird file extensions not working?
	else
		doicon "${DISTDIR}"/"${PN}".jpg
	fi

	make_desktop_entry oa_editor "${PN} artifact editor" "${PN}".jpg
	make_desktop_entry oa_logview "${PN} log viewer" "${PN}".jpg
	make_desktop_entry oa_testrunner "${PN} test runner" "${PN}".jpg

	python_export EPYTHON PYTHON
	python_optimize "${D}"/usr/share/"${PN}"
}

pkg_postinst() { fdo-mime_desktop_database_update; }
pkg_postrm() { fdo-mime_desktop_database_update; }
