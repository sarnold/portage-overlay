# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/sci-mathematics/geomview/geomview-1.9.4.ebuild,v 1.6 2010/10/10 21:49:01 ulm Exp $

EAPI=4

inherit elisp-common eutils flag-o-matic fdo-mime

DESCRIPTION="Interactive Geometry Viewer"
SRC_URI="mirror://sourceforge/${PN}/${P}.tar.bz2"
HOMEPAGE="http://geomview.sourceforge.net"

KEYWORDS="~amd64 ~ppc ~sparc ~x86"
LICENSE="LGPL-2.1"
SLOT="0"
IUSE="-avg +bzip2 debug emacs +firefox netpbm pdf +zlib"

DEPEND="zlib? ( sys-libs/zlib )
	emacs? ( virtual/emacs )
	>=x11-libs/motif-2.3:0
	virtual/opengl"

RDEPEND="${DEPEND}
	netpbm? ( >=media-libs/netpbm-10.37.0 )
	bzip2? ( app-arch/bzip2 )
	app-arch/gzip
	pdf? ( || ( app-text/xpdf
		app-text/evince
		app-text/gv
		app-text/gsview
		app-text/epdfview
		app-text/acroread )
		)
	firefox? ( www-client/firefox )"

S="${WORKDIR}/${P/_/-}"
SITEFILE=50${PN}-gentoo.el

src_configure() {
	# GNU standard is /usr/share/doc/${PN}, so override this; also note
	# that motion averaging is still experimental.
	if use pdf; then
		local myconf="--docdir=/usr/share/doc/${PF}"
	else
		local myconf="--docdir=/usr/share/doc/${PF} --without-pdfviewer"
	fi

	econf ${myconf} $(use_enable debug d1debug) $(use_with zlib) \
		$(use_enable avg motion-averaging) \
		|| die "could not configure"
}

src_compile() {
	emake || die "make failed"

	if use emacs; then
		cp "${FILESDIR}/gvcl-mode.el" "${S}"
		elisp-compile *.el || die "elisp-compile failed"
	fi

}

src_install() {
	emake DESTDIR="${D}" install || die "emake install failed"

	doicon "${FILESDIR}"/geomview.png
	make_desktop_entry geomview "GeomView ${PV}" \
		"/usr/share/pixmaps/geomview.png" \
		"Science;Math;Education"

	dodoc AUTHORS ChangeLog NEWS INSTALL.Geomview

	if ! use pdf; then
		rm "${D}"/usr/share/doc/${PF}/${PN}.pdf
	fi

	if use emacs; then
		elisp-install ${PN} *.el *.elc|| die "elisp-install failed"
		elisp-site-file-install "${FILESDIR}/${SITEFILE}" || \
			die "elisp-site-file-install failed"
	fi

	insinto /usr/share/${PN}/geom
	doins "${FILESDIR}"/*.mesh
}

pkg_postinst() {
	fdo-mime_desktop_database_update

	elog "GeomView expects you to have both Firefox and Xpdf installed for"
	elog "viewing the documentation (this can be changed at runtime)."
	elog
	elog "If you wish to use an alternate PDF viewer, feel free to remove"
	elog "xpdf and use the viewer of your choice (see the docs for how to"
	elog "setup the \'(ui-pdf-viewer VIEWER)\' GCL-command)."

	use emacs && elisp-site-regen
}

pkg_postrm() {
	fdo-mime_desktop_database_update
	use emacs && elisp-site-regen
}
