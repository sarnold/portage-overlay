# Copyright 1999-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header:  $
# $Id: bitpim.ebuild 4291 2007-06-22 02:08:52Z djpham $

DESCRIPTION="This program allows you to manage data on CDMA phones from LG, Samsung, Sanyo and others."
HOMEPAGE="http://www.bitpim.org/"
SRC_URI="file:///${P}.tar.bz2"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"

RDEPEND=">=dev-libs/libusb-0.1.10a"

RESTRICT="fetch"

src_unpack() {
    mkdir -p ${S}
    cd ${S}
    tar xfj ${DISTDIR}/${A}
}

src_install() {
    # copy the binary files over
    cd ${S}
    tar cf - . | (cd ${D};tar xf -)
}

pkg_postinst() {
    if [ -x ${ROOT}usr/bin/udevinfo ] && \
       [ -d ${ROOT}etc/udev/rules.d ] && \
       [ $(${ROOT}usr/bin/udevinfo -V | cut -d' ' -f3) -ge 95 ]
    then
        respath=${ROOT}usr/lib/%%NAME%%-%%VERSION%%/resources
        cp -f $respath/60-bitpim.rules ${ROOT}etc/udev/rules.d
        cp -f $respath/bpudev ${ROOT}usr/bin
        chmod 755 ${ROOT}usr/bin/bpudev
        mkdir -p ${ROOT}var/bitpim
    fi
}

pkg_postrm() {
    rm -rf ${ROOT}usr/lib/%%NAME%%-%%VERSION%% ${ROOT}var/bitpim \
       ${ROOT}usr/bin/bpudev ${ROOT}etc/udev/rules.d/60-bitpim.rules
}
