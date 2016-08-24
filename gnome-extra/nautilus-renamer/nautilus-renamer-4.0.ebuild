# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id $

EAPI="5"
PYTHON_COMPAT=( python{2_7,3_3,3_4,3_5} )
GCONF_DEBUG="yes"

inherit eutils fdo-mime gnome2 python-any-r1

MY_P="${PN}_${PV}"

DESCRIPTION="A python script for batch renaming files in nautilus."
HOMEPAGE="https://launchpad.net/nautilus-renamer"
SRC_URI="https://launchpad.net/${PN}/trunk/${PV}/+download/${MY_P}.tar.gz -> ${MY_P}.tar"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"

IUSE="debug nls"
LANGS="ar cs de el eo es fi fr gl id it ja ko pl pt_BR ro ru sv ta tr uk"
for X in $LANGS; do IUSE="${IUSE} linguas_${X}"; done

RDEPEND="${PYTHON_DEPS}
	( >=gnome-base/nautilus-2.32[introspection] )
	dev-libs/gobject-introspection
	dev-libs/glib
	dev-python/pygobject
	x11-libs/pango[introspection]
	dev-python/notify-python
	dev-python/pygtk
	x11-libs/gtk+[introspection]"

DEPEND="${RDEPEND}
	dev-util/pkgconfig
	dev-python/docutils
	nls? ( >=sys-devel/gettext-0.14 )"

DOCS="AUTHORS ChangeLog TODO README"

S="${WORKDIR}/${MY_P}"

pkg_setup() {
	python-any-r1_pkg_setup
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
	if use nls ; then
		scripts/genmo.py po/ mo/
	fi
}

src_install() {
	extensiondir="$(pkg-config --variable=extensiondir libnautilus-extension)"
	[ -z ${extensiondir} ] && die "pkg-config unable to get nautilus extensions dir"

	exeinto ${extensiondir}/python
	newexe nautilus-renamer.py Renamer

	if use nls; then
		[[ -d mo ]] && domo mo/*/*/*.mo || die "domo failed"
	fi
}

pkg_postinst() {
	gnome2_pkg_postinst
	gnome2_icon_cache_update
	elog ""
	ewarn "Note, you may still need to add the following symlink in order"
	ewarn "to make the scripts menu show up in Nautilus:"
	ewarn "  ln -s /usr/$(get_libdir)/nautilus/extensions-3.0/python/Renamer \${HOME}/.gnome2/nautilus-scripts/Renamer"
	elog ""
}

pkg_postrm() {
	gnome2_pkg_postrm
	gnome2_icon_cache_update
}
