# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

#CMAKE_IN_SOURCE_BUILD="true"
CMAKE_MAKEFILE_GENERATOR="ninja"
BUILD_DIR="${WORKDIR}/upm-${PV}_build"
CMAKE_VERBOSE=ON

PYTHON_COMPAT=( python2_7 python3_{5,6} )
PYTHON_REQ_USE='threads(+)'

inherit cmake-utils eutils flag-o-matic python-r1 toolchain-funcs

DESCRIPTION="(Useful Packages & Modules) Sensor/Actuator repository for MRAA"
HOMEPAGE="https://github.com/intel-iot-devkit/upm"

SRC_URI="https://github.com/intel-iot-devkit/upm/archive/v${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="MIT"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~mips ~x86"
IUSE="cxx doc -examples -java -modbus node"

DEPEND="${PYTHON_DEPS}
	dev-embedded/libmraa
	>=dev-lang/swig-3.0.8
	doc? ( dev-python/sphinx )
	java? ( virtual/jdk )
	node? ( <net-libs/nodejs-7 )
	modbus? ( dev-libs/libmodbus )
	dev-cpp/gtest"

RDEPEND="${DEPEND}"

S="${WORKDIR}/upm-${PV}"

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
		-DBUILDSWIGPYTHON=OFF
		-DBUILDDOC="$(usex doc)"
		-DBUILDCPP="$(usex cxx)"
		-DBUILDSWIGNODE="$(usex node)"
		-DBUILDSWIGJAVA="$(usex java)"
		-DENABLEEXAMPLES="$(usex examples)"
		-DBUILDTESTS=OFF
	)

	export GMOCK_PREFIX="${EPREFIX}/usr"

	cmake-utils_src_configure
}
