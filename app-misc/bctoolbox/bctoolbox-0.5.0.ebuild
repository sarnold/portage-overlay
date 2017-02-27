# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=6

inherit cmake-utils multilib-minimal

DESCRIPTION="A library written in C that allows you to create and run audio and video streams"
HOMEPAGE="http://www.linphone.org/"

SRC_URI="https://github.com/BelledonneCommunications/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

DEPEND="net-libs/mbedtls
	app-misc/bcunit"

RDEPEND="${DEPEND}"

src_prepare() {
	cmake-utils_src_prepare
}

multilib_src_configure() {
	local mycmakeargs=(
		-DLIB_INSTALL_DIR="/usr/$(get_libdir)"
		-DENABLE_POLARSSL=OFF
		-DENABLE_MBEDTLS=ON
	)

	cmake-utils_src_configure
}

multilib_src_compile() {
	cmake-utils_src_compile
}

multilib_src_install() {
	cmake-utils_src_install
}
