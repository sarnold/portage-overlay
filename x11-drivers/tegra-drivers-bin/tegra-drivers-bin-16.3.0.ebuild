# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

DESCRIPTION="NVIDIA Tegra X.org binary driver"

# should set these in make.conf - valid values for this release:
#   ventana cardhu
#   14
TEGRA_PLATFORM="ventana"
XORG_ABI="14"

HOMEPAGE="https://developer.nvidia.com/linux-tegra"
SRC_URI="https://developer.nvidia.com/sites/default/files/akamai/mobile/files/L4T/${TEGRA_PLATFORM}_Tegra-Linux-tegra_drv_abi${XORG_ABI}-R${PV}_armhf.tbz2"

LICENSE="nvidia"
SLOT="0"
KEYWORDS="arm"

IUSE=""

DEPEND=">=x11-base/xorg-server-1.14.1
	=sys-libs/tegra-libs-bin-${PV}"

RDEPEND="${DEPEND}"

RESTRICT="strip mirror"

S="${WORKDIR}"

src_unpack() {
	unpack "${A}"
	unpack ./tegra_drv_abi_${XORG_ABI}.tbz2
}

src_install() {
	insinto /
	doins -r usr
}
