# Copyright 1999-2013 Gentoo Technologies, Inc, and Douglas Russell
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit eutils

DESCRIPTION="Small set of GKrellm Themes"
HOMEPAGE="http://www.gentoogeek.org/"
SRC_URI="http://www.gentoogeek.org/files/${PN}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~hppa ~mips ~ppc ~ppc64 ~sparc ~x86"
IUSE=""

DEPEND=">=app-admin/gkrellm-2.0"

S=${WORKDIR}/themes

src_install() {
	cd "${WORKDIR}"
	insinto /usr/share/gkrellm2
	doins -r themes
}

pkg_postinst() {
	einfo
	einfo "GkrellM users (i.e. < GKrellM2.0) must make a symlink between the"
	einfo "all-users theme directory and /usr/share/gkrellm2/themes/"
	einfo "Move any themes you wish to retain from the GKrellM all-users theme"
	einfo "directory to the /usr/share/gkrellm2/themes/ directory."
	einfo "rm <PATH TO GKRELLM THEME DIRECTORY> (Probably /usr/share/gkrellm/themes)"
	einfo "ln -s /usr/share/gkrellm2/themes/ <PATH TO GKRELLM THEME DIRECTORY>"
	einfo
}

