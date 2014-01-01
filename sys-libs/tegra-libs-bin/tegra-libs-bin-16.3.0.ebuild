# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

DESCRIPTION="NVIDIA Tegra2 libraries"

# should set TEGRA_PLATFORM in make.conf - valid values for this release:
#   ventana cardhu
TEGRA_PLATFORM="ventana"

IUSE=""

HOMEPAGE="https://developer.nvidia.com/linux-tegra"

SRC_URI="http://developer.nvidia.com/sites/default/files/akamai/mobile/files/L4T/${TEGRA_PLATFORM}_Tegra-Linux-R${PV}_armhf.tbz2"

SLOT="0"
KEYWORDS="~arm"
LICENSE="nvidia"

DEPEND=""
RDEPEND="${DEPEND}"

S="${WORKDIR}"
RESTRICT="strip mirror"

S="${WORKDIR}"/Linux_for_Tegra

src_unpack() {
	unpack "${A}"
	cd "${S}"/nv_tegra
	unpack ./nvidia_drivers.tbz2
}

src_install() {
	cd "${S}"/nv_tegra
	# We have x11-drivers/tegra-drivers for this
	rm -rf usr/lib/xorg/

	# These collide with mesa :(
	rm usr/lib/libEGL* usr/lib/libGLES* usr/lib/libjpeg.so

	insinto /
	doins -r usr lib etc
}
