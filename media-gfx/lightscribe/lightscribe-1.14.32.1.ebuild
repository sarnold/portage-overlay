# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/app-pda/qtopia-desktop-bin/qtopia-desktop-bin-2.2.0.ebuild,v 1.7 2008/04/28 15:57:52 mr_bones_ Exp $

inherit eutils rpm multilib

REV="1"
LS="/opt/lightscribe"
S="${WORKDIR}"

DESCRIPTION="Base LightScribe host software for burning disc labels."
SRC_URI="http://download.lightscribe.com/ls/${P}-linux-2.6-intel.rpm"
HOMEPAGE="http://www.lightscribe.com/"

LICENSE=""
SLOT="0"
KEYWORDS="amd64 x86"

IUSE=""

DEPEND=""
RDEPEND="virtual/libc
	x11-libs/libX11
	amd64? ( app-emulation/emul-linux-x86-xlibs )"

RESTRICT="fetch mirror strip"

pkg_setup() {
	# This is a binary x86 package => ABI=x86
	has_multilib_profile && ABI="x86"
}

pkg_unpack() {
	rpm_src_unpack
}

src_compile() { :; }

src_install() {
	dodir ${LS}
	# Isn't there a better way?
	local libdir="lib32"
	if has_multilib_profile ; then
	    libdir=$(get_abi_LIBDIR x86)
	fi

	into ${LS}
	    rm -f "${S}"/usr/lib/*.so
	    dolib.so "${S}"/usr/lib/liblightscribe.so.1
	    dosbin "${S}"/usr/lib/lightscribe/elcu.sh
	    dodoc "${S}"/usr/share/doc/lightscribeLicense.rtf
	exeinto ${LS}/updates
	doexe "${S}"/usr/lib/lightscribe/updates/fallback.sh
	dodir ${LS}/res

	generate_files
	insinto /etc
	doins lightscribe.rc
	doenvd 38lightscribe
}

pkg_postinst() {

	elog
	elog " Finished installing ${P} into ${LS}.  You may"
	elog " need to edit /etc/lightscribe.rc for your device."
	elog
	elog " You need more stuff to do anything with it; emerge the"
	elog " the lightscribe-apps (and lightscribe-sdk if desired)."
	elog
}

generate_files() {
	cat <<-EOF > 38${PN}
	PATH="${LS}/SimpleLabeler"
	LDPATH="${LS}/${libdir}:${LS}/common/Qt"
	EOF

	cat <<-EOF > ${PN}.rc
	ResourceDir=/opt/lightscribe/res;
	UpdateScriptDir=/opt/lightscribe/updates;
	DriveEnumeration=false;
	CDROMDevicePath=/dev/dvdrw;
	EOF
}

