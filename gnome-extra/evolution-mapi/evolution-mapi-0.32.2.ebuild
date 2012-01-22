# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils gnome2

DESCRIPTION="Evolution module for connecting to Microsoft Exchange"
HOMEPAGE="http://www.novell.com/products/desktop/features/evolution.html"
LICENSE="GPL-2"

SLOT="2.0"
KEYWORDS="-amd64 -x86"
IUSE=""

RDEPEND="
	>=mail-client/evolution-2.32
	>=gnome-extra/evolution-data-server-2.32[kerberos]
	dev-libs/libxml2
	>=net-libs/libmapi-0.10"

DEPEND="${RDEPEND}
	>=dev-util/intltool-0.40
	dev-util/pkgconfig"

DOCS="AUTHORS ChangeLog NEWS README"

src_unpack() {
	unpack ${A}
}

src_prepare() {
	#get rid of unicode on get folders
	epatch "${FILESDIR}/${PN}-0.32.2-no_unicode_folders.patch"
}
