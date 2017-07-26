# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

DESCRIPTION="Freescale IMX firmware"
HOMEPAGE=""
SRC_URI="http://repository.timesys.com/buildsources/f/firmware-imx/${P}/${P}.tar.gz"

LICENSE=""
SLOT="0"
KEYWORDS="~arm"
IUSE=""

DEPEND=""
RDEPEND="${DEPEND}"

src_install() {
	rm ${S}/firmware/vpu/Android.mk
	rm ${S}/firmware/ath6k/Android.mk

	insinto /lib/firmware/
	doins -r "${S}/firmware/vpu"
	doins -r "${S}/firmware/ath6k"
}
