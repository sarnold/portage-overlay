# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils cvs flag-o-matic multilib

ECVS_SERVER="cvs.sv.gnu.org:/sources/aeskulap"
ECVS_MODULE="aeskulap"
ECVS_LOCALNAME="aeskulap"
S=${WORKDIR}/${ECVS_LOCALNAME}

DESCRIPTION="A medical image viewer and DICOM network client"
HOMEPAGE="http://aeskulap.nongnu.org"
SLOT="0"
KEYWORDS="x86 amd64 ppc"
LICENSE="GPL-2 LGPL-2.1 BSD"
IUSE="gnome"

RDEPEND=">=x11-libs/gtk+-2.6.5
	>=dev-libs/glib-2.6.5
	>=gnome-base/gconf-2.10.0
	>=gnome-base/libglade-2.5.0
	>=dev-libs/libxml2-2.6.20
	>=x11-libs/pango-1.4.0
	>=dev-libs/libxslt-1.0.15
	virtual/xft
	media-libs/fontconfig
	sys-libs/zlib
	media-libs/libpng
	media-libs/tiff
	>=sys-devel/gcc-3
	>=dev-libs/libsigc++-2.0.3
	>=dev-cpp/gtkmm-2.6
	>=dev-cpp/glibmm-2.6
	>=dev-cpp/gconfmm-2.6
	>=dev-cpp/libglademm-2.6"	

DEPEND="${RDEPEND}
	sys-devel/gettext
	dev-util/pkgconfig
	>=dev-util/intltool-0.29"

src_compile() {
	./autogen.sh 
	./configure --host=${CHOST} \
		--libdir=/usr/$(get_libdir) \
		--prefix=/usr \
		--disable-schemas-install || die

	emake || die
}

src_install() {
	make DESTDIR="${D}" install
}

DOCS="COPYING COPYING.LIB COPYING.DCMTK README"
