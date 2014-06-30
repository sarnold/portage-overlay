# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"
GCONF_DEBUG="no"
GNOME2_LA_PUNT="yes"

inherit autotools gnome2 flag-o-matic

DESCRIPTION="Tools aimed to make easy the administration of UNIX systems"
HOMEPAGE="http://www.gnome.org/projects/gst/"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~ia64 ~ppc ~ppc64 ~sparc ~x86"
IUSE="nfs policykit samba"

RDEPEND="
	>=app-admin/system-tools-backends-2.10.1
	>=dev-libs/liboobs-2.91.1
	>=x11-libs/gtk+-2.91:3
	>=dev-libs/glib-2.25.3:2
	dev-libs/dbus-glib
	>=gnome-base/nautilus-2.9.90
	sys-libs/cracklib
	nfs? ( net-fs/nfs-utils )
	samba? ( >=net-fs/samba-3 )
	policykit? ( >=sys-auth/polkit-0.97
		>=gnome-extra/polkit-gnome-0.105 )
"
DEPEND="${RDEPEND}
	app-text/docbook-xml-dtd:4.1.2
	app-text/scrollkeeper
	>=app-text/gnome-doc-utils-0.3.2
	>=dev-util/intltool-0.35.0
	>=sys-devel/gettext-0.17
	virtual/pkgconfig"

pkg_setup() {
	DOCS="AUTHORS BUGS ChangeLog HACKING NEWS README TODO"

	G2CONF="${G2CONF}
		--disable-static
		$(use_enable policykit polkit)"

	if ! use nfs && ! use samba; then
		G2CONF="${G2CONF} --disable-shares"
	fi
}

src_prepare() {
	epatch ${FILESDIR}/${PN}-configure.patch
	eautoreconf
	gnome2_src_prepare
}

src_configure() {
	append-ldflags -lm
	gnome2_src_configure
}

src_install() {
	gnome2_src_install
	insinto /etc/${PN}
	doins ${FILESDIR}/user-profiles.conf
}

pkg_postinst() {
	elog ""
	ewarn "In order to modify system settings, you have to"
	ewarn "be in the stb-admin group."
	ewarn "Just run gpasswd -a <USER> stb-admin, then have <USER> re-login."
	elog ""
	gnome2_pkg_postinst
}
