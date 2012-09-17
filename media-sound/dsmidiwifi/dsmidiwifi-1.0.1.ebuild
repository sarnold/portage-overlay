# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2

inherit eutils multilib qt4-r2 versionator

DESCRIPTION="network midi server that supports Nintendo DS, iPhone, and Android"
HOMEPAGE="http://code.google.com/p/dsmi"

MY_PV="v$(replace_version_separator 2 '')"
MY_PF="${PN}-${MY_PV}"

SRC_URI="http://dsmi.googlecode.com/files/dsmidiwifi-${MY_PV}.tgz"

LICENSE="LGPL"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"
IUSE=""
DEPEND=""
RDEPEND="${DEPEND}"

PATCHES=(
)

S=${WORKDIR}/${MY_PF}/source

src_configure() {
	eqmake4 DSMIDIWiFi.pro
}

src_install() {
	dobin DSMIDIWiFi
}
