# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5

inherit base

DESCRIPTION="Menu generator for all the box WMs"
HOMEPAGE="http://github.com/ju1ius/uxdgmenu/wiki"
SRC_URI="mirror://sourceforge/${PN}/${PN}_${PV}.orig.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~ppc64 ~x86 ~x86-fbsd"

IUSE="dbus gtk"

DEPENDS="sys-fs/inotify-tools
	dev-libs/glib
	sys-devel/gettext
	dev-util/pkgconfig"

RDEPEND="${DEPENDS}
	gtk? ( >=dev-python/pygtk-2.6 )
	dbus? ( dev-python/dbus-python )
	dev-python/pyxdg"

S="${WORKDIR}/${PN}"

PATCHES=( "${FILESDIR}/${PN}-makefile-fixes.patch" )
