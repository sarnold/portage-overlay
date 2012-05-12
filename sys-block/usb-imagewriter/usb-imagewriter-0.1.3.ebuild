# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="3"
PYTHON_DEPEND="2:2.6"
PYTHON_USE_WITH="xml"
SUPPORT_PYTHON_ABIS="1"
#RESTRICT_PYTHON_ABIS="2.[45] 3.* *-jython"

inherit eutils

DESCRIPTION="Graphical tool to write .img files to USB Keys."
HOMEPAGE="https://launchpad.net/~ogra/+archive/ppa/+packages"
SRC_URI="https://launchpad.net/${PN}/trunk/0.1/+download/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

RDEPEND="${DEPEND}
	sys-apps/util-linux
	sys-apps/coreutils
	x11-libs/gksu
	dev-python/libgnome-python:2
	>=gnome-base/libglade-2:2.0"

DEPEND="sys-fs/udev
	app-shells/bash"

src_prepare() {
	epatch ${FILESDIR}/${P}-install-script-fix.patch
	epatch ${FILESDIR}/${P}-hal-to-udev-fix.patch
	if use amd64 ; then
		sed -i -e "s|/lib|/lib64|" \
			${S}/lib/imagewriter.py \
			${S}/install.sh
	fi
	cp ${FILESDIR}/header.png ${S}/share/usb-imagewriter/
}

src_configure() {
	:
}

src_compile() {
	:
}

src_install() {
	dodir /usr/share/applications
	dodir /usr/bin
	DESTDIR=${D} ./install.sh || die "install failed!"
}
