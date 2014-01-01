# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"

DESCRIPTION="NVIDIA Tegra2 codecs"

# should set TEGRA_PLATFORM in make.conf - valid values for this release:
#   ventana cardhu
TEGRA_PLATFORM="ventana"

IUSE=""

HOMEPAGE="https://developer.nvidia.com/linux-tegra"

SRC_URI="http://developer.nvidia.com/sites/default/files/akamai/mobile/files/L4T/${TEGRA_PLATFORM}_Tegra-Linux-codecs-R${PV}_armhf.tbz2"

SLOT="0"
KEYWORDS="~arm"
LICENSE="nvidia-tegra-codecs"

DEPEND=""
RDEPEND="${DEPEND}
	=sys-libs/tegra-libs-bin-${PV}*"

S="${WORKDIR}"
RESTRICT="strip mirror"

S="${WORKDIR}"

src_unpack() {
	unpack "${A}"
	unpack ./restricted_codecs.tbz2
}

src_install() {
	cd "${S}"/nv_tegra

	insinto /
	doins -r lib
}
