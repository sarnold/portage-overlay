# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6
PYTHON_COMPAT=( python2_7 )

inherit distutils-r1 gnome2-utils xdg-utils

DESCRIPTION="GNOME Arduino Electronics Prototyping Environment"
HOMEPAGE="http://gnome.eu.org/evo/index.php/Gnoduino"
#SRC_URI="http://gnome.eu.org/gnoduino-0.3.0.tar.gz"
SRC_URI="http://gnome.eu.org/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"

IUSE=""

RDEPEND="${PYTHON_DEPS}
	dev-python/pyserial[${PYTHON_USEDEP}]
	dev-python/pygtksourceview[${PYTHON_USEDEP}]
	dev-python/pygobject[${PYTHON_USEDEP}]
	dev-python/pygtk[${PYTHON_USEDEP}]
	dev-python/gconf-python[${PYTHON_USEDEP}]
	dev-python/gnome-vfs-python[${PYTHON_USEDEP}]"
DEPEND="${RDEPEND}"

S="${WORKDIR}"/${P}

#PATCHES=( "${FILESDIR}"/${P}-update-to-pyserial3-api.patch )

src_install(){
	export GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL="1"
	distutils-r1_src_install
	unset GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL
}

pkg_postrm() {
	gnome2_icon_cache_update
        gnome2_gconf_uninstall
	xdg_desktop_database_update
}

pkg_preinst() {
	gnome2_gconf_savelist
}

pkg_postinst() {
	gnome2_icon_cache_update
	gnome2_gconf_install
	xdg_desktop_database_update

	ewarn "To be able to fully use Gnoduino you need to aquire the avr toolchain,"
	ewarn "i.e.: "
	ewarn "   USE="-openmp" crossdev -t avr -s4 -S --without-headers "
	ewarn " and set the kernel options: "
	ewarn "   Device Drivers -> USB support -> USB Serial Converter support -> USB FTDI Single Port Serial Driver "
	ewarn "   Device Drivers -> USB support -> USB Modem \(CDC ACM\) support "
	ewarn " "
	ewarn " Some resources:"
	ewarn "   http://playground.arduino.cc/linux/gentoo "
	ewarn "   https://bugs.gentoo.org/show_bug.cgi?id=147155 "
        ewarn "   http://forums.gentoo.org/viewtopic-t-907860.html "
        ewarn " "
	elog
}

