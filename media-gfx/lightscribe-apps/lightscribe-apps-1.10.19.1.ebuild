# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils fdo-mime rpm multilib

REV="1"
LS="/opt/lightscribe"
S="${WORKDIR}"
MY_PN="lightscribeApplications"

DESCRIPTION="LightScribe GUI applications for burning disc labels."
SRC_URI="http://download.lightscribe.com/ls/${MY_PN}-${PV}-linux-2.6-intel.rpm"
HOMEPAGE="http://www.lightscribe.com/"

LICENSE=""
SLOT="0"
KEYWORDS="amd64 x86"

IUSE=""

DEPEND="media-gfx/lightscribe"

RDEPEND="virtual/libc
	x11-libs/libX11
	amd64? ( app-emulation/emul-linux-x86-xlibs )"

RESTRICT="mirror strip fetch"

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

	# apparently it needs to be SUID root in order to burn a label
	cp -a "${S}"/opt/${MY_PN}/SimpleLabeler "${D}${LS}"
	cp -a "${S}"/opt/${MY_PN}/common "${D}${LS}"

	make_desktop_entry \
	    ${LS}/SimpleLabeler/SimpleLabeler \
	    "LightScribe SimpleLabeler ${PV}" \
	    "/opt/lightscribe/SimpleLabeler/content/images/LabelWizardIcon.png" \
	    "Application;Graphics;"
}

pkg_postinst() {
	fdo-mime_desktop_database_update

	elog
	elog " Finished installing ${MY_PN}-${PV} into ${LS}"
	elog
}

pkg_postrm() {
	fdo-mime_desktop_database_update
}
