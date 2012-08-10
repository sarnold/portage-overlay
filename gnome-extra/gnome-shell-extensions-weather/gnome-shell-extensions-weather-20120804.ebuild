# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="4"

inherit autotools gnome2-utils git-2

DESCRIPTION="Weather extensions for GNOME Shell"
HOMEPAGE="https://github.com/Neroth/gnome-shell-extension-weather"
EGIT_REPO_URI="https://github.com/Neroth/gnome-shell-extension-weather"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"

COMMON_DEPEND="
        >=dev-libs/glib-2.26
        >=gnome-base/gnome-desktop-3:3"
RDEPEND="${COMMON_DEPEND}
        gnome-base/gnome-desktop:3[introspection]
        media-libs/clutter:1.0[introspection]
        net-libs/telepathy-glib[introspection]
        x11-libs/gtk+:3[introspection]
        x11-libs/pango[introspection]"
DEPEND="${COMMON_DEPEND}
	dev-libs/seed
	>=dev-util/pkgconfig-0.22
        >=dev-util/intltool-0.26
	gnome-base/dconf
	gnome-base/gnome-common
	sys-devel/gettext"


src_prepare() {
	./autogen.sh --prefix=/usr
}

src_configure() {
	einfo "Nothing to see here...  Move along..."
}

src_compile()   {
	emake
}


src_install()   {
#	mv weather-settings
#	dobin weather-settings

#	insinto /usr/share/applications
#	doins weather-settings.desktop

	einstall

	rm ${D}/usr/share/glib-2.0/schemas/gschemas.compiled
}

pkg_preinst() {
	gnome2_schemas_savelist
}

pkg_postinst() {
	gnome2_schemas_update
}

pkg_postrm() {
	gnome2_schemas_update --uninstall
}
