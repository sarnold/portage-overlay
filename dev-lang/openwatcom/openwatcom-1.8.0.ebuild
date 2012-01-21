# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils

LICENSE="OWPL-1"
DESCRIPTION="The Open Watcom compiler"
HOMEPAGE="http://www.openwatcom.org"
SRC_URI="http://openwatcom.mirrors.pair.com/source/open_watcom_${PV}-src.tar.bz2"

KEYWORDS="~x86"
SLOT="0"
IUSE="examples source"

DEPEND="sys-devel/gcc"

RESTRICT=""

S=${WORKDIR}/OW18src

src_prepare() {
	epatch "${FILESDIR}/build.sh.patch"
	epatch "${FILESDIR}/wmake_c_mglob.c.patch"
}

src_compile() {
	./build.sh || die "build.sh failed"
}

src_install() {
	mkdir -p "${D}"/opt
	cp -R rel2 "${D}"/opt/openwatcom
	ln -s binl "${D}"/opt/openwatcom/bin

	use examples || rm -rf "${D}"/opt/openwatcom/samples
	use source || rm -rf "${D}"/opt/openwatcom/src

	INSTALL_DIR=/opt/openwatcom

	local env_file=05${PN}
	cat > ${env_file} <<-EOF
		WATCOM=${INSTALL_DIR}
		INCLUDE=${INSTALL_DIR}/lh
		PATH=${INSTALL_DIR}/binl
	EOF
	doenvd ${env_file} || die "doenvd ${env_file} failed"
}
