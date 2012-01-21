# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"
PYTHON_DEPEND="2"
inherit eutils python gnome2

DESCRIPTION="A python script for batch renaming files in nautilus."
HOMEPAGE="https://launchpad.net/nautilus-renamer"
SRC_URI="http://launchpad.net/${PN}/trunk/${PV}/+download/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"
IUSE="debug"

RDEPEND="gnome-base/nautilus
	dev-libs/glib:2
	dev-python/pygobject
	x11-libs/pango
	dev-python/notify-python
	dev-python/pygtk
	x11-libs/gtk+:2"

DEPEND="${RDEPEND}
	dev-util/pkgconfig
	dev-python/docutils"

DOCS="AUTHORS ChangeLog TODO README"
G2CONF="${G2CONF} $(use_enable debug) --disable-static"
S="${WORKDIR}"/${PN}

pkg_setup() {
	python_pkg_setup
}

src_prepare() {
	gnome2_omf_fix
}

src_configure() {
	if [[ ${GCONF_DEBUG} != 'no' ]] ; then
		if use debug ; then
			G2CONF="${G2CONF} --enable-debug=yes"
		fi
	fi
}

src_compile() {
	echo "Nothing to see here...  Move along..."
}

src_install() {
	extensiondir="$(pkg-config --variable=extensiondir libnautilus-extension)"
	[ -z ${extensiondir} ] && die "pkg-config unable to get nautilus extensions dir"

	exeinto ${extensiondir}/python
	newexe nautilus-renamer.py Renamer

	scripts/genmo.py po/ "${D}"usr/share/locale
}

pkg_postinst() {
	python_mod_optimize ${extensiondir}/python
	gnome2_pkg_postinst
	elog ""
	ewarn "Note, you still need to add the following symlink in order"
	ewarn "to make the scripts menu show up in Nautilus:"
	ewarn "  ln -s /usr/$(get_libdir)/nautilus/extensions-3.0/python/Renamer \${HOME}/.gnome2/nautilus-scripts/Renamer"
	elog ""
}

pkg_postrm() {
	python_mod_cleanup ${extensiondir}/python
}