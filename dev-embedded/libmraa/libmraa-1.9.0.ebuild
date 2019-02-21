# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

CMAKE_IN_SOURCE_BUILD="true"
CMAKE_VERBOSE=ON

PYTHON_COMPAT=( python2_7 python3_{5,6} )
PYTHON_REQ_USE='threads(+)'

inherit cmake-utils eutils python-r1 toolchain-funcs

DESCRIPTION="Library for low speed IO Communication in C with bindings for C++, Python, Node.js & Java"
HOMEPAGE="https://github.com/intel-iot-devkit/mraa"

SRC_URI="https://github.com/intel-iot-devkit/mraa/archive/v${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="MIT"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE="doc -examples -java node tools"

DEPEND="${PYTHON_DEPS}
	>=dev-lang/swig-3.0.8
	doc? ( dev-python/sphinx )
	java? ( virtual/jdk )
	node? ( <net-libs/nodejs-7 )
	dev-cpp/gtest
	dev-libs/json-c
	virtual/libudev"

RDEPEND="${DEPEND}"

S="${WORKDIR}/mraa-${PV}"

RESTRICT="test"

src_configure() {
	tc-export CC CXX AR RANLIB PKG_CONFIG
	PKG_CONFIG_LIBDIR="${EPREFIX}/usr/$(get_libdir)/pkgconfig"

	python_setup

	local mycmakeargs=(
		-DCMAKE_INSTALL_PREFIX:PATH="${EPREFIX}/usr"
		-DLIB_INSTALL_DIR="${EPREFIX}/usr/$(get_libdir)"
		-DCMAKE_SKIP_INSTALL_RPATH=ON
		-DCMAKE_SKIP_RPATH=ON
		-DBUILDSWIG=ON
		-DBUILDSWIGPYTHON=ON
		-DBUILDDOC="$(usex doc)"
		-DBUILDSWIGNODE="$(usex node)"
		-DBUILDSWIGJAVA="$(usex java)"
		-DINSTALLTOOLS="$(usex tools)"
		-DENABLEEXAMPLES="$(usex examples)"
		-DFIRMATA=ON
		-DUSBPLAT=ON
		-DONEWIRE=OFF
		-DJSONPLAT=ON
		-DFTDI4222=OFF
		-DIMRAA=ON
		-DBUILDTESTS=OFF
	)

	export GMOCK_PREFIX="${EPREFIX}/usr"

	cmake-utils_src_configure
}
