# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Distributed under the terms of the GNU Public License v2

EAPI="5"
#CROS_WORKON_PROJECT="chromiumos/third_party/xf86-video-armsoc"
#CROS_WORKON_LOCALNAME="xf86-video-armsoc"

#EGIT_REPO_URI="git://git.linaro.org/arm/xorg/driver/${PN}.git"
EGIT_REPO_URI="https://git.chromium.org/git/chromiumos/third_party/${PN}.git"

XORG_DRI="always"
XORG_EAUTORECONF="yes"

inherit xorg-2 git-2 eutils

DESCRIPTION="X.Org driver for ARM devices"

KEYWORDS="-* ~arm"

RDEPEND=">=x11-base/xorg-server-1.9
	!x11-drivers/mali-drivers"
DEPEND="${RDEPEND}"

src_prepare() {
##	epatch "${FILESDIR}"/0001-Import-patch-from-Marcin.patch
	epatch "${FILESDIR}"/remove-mibstore-header-include.patch
	xorg-2_src_prepare
}
