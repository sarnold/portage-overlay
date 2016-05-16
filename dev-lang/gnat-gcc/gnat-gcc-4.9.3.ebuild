# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5
inherit gnatbuild-r1

DESCRIPTION="GNAT Ada Compiler - gcc version"
HOMEPAGE="https://gcc.gnu.org/"
LICENSE="GMGPL"

IUSE="doc openmp"

BOOT_SLOT="4.9"
PATCH_VER="1.5"
#UCLIBC_VER="1.0"
PIE_VER="0.6.4"
#SPECS_VER="0.2.0"
#SPECS_GCC_VER="4.4.3"

# SLOT is set in gnatbuild.eclass, depends only on PV (basically SLOT=GCCBRANCH)
# so the URI's are static.
KEYWORDS="~amd64 ~x86"

SRC_URI="mirror://gnu/gcc/gcc-${PV}/gcc-${PV}.tar.bz2
	mirror://gentoo/gcc-${PV}-patches-${PATCH_VER}.tar.bz2
	mirror://gentoo/gcc-${PV}-piepatches-v${PIE_VER}.tar.bz2
	amd64? ( http://dev.gentoo.org/~nerdboy/files/gnatboot-${BOOT_SLOT}-amd64.tar.xz )
	x86? ( http://dev.gentoo.org/~nerdboy/files/gnatboot-${BOOT_SLOT}-i686.tar.xz )"

# starting with 4.3.0 gnat needs these libs
RDEPEND=">=dev-libs/mpfr-3.1.2
	>=dev-libs/gmp-5.1.3
	>=dev-libs/mpc-1.0.1
	>=sys-libs/zlib-1.2
	>=sys-libs/ncurses-5.7:0"

DEPEND="${RDEPEND}
	doc? ( >=sys-apps/texinfo-5 )
	>=sys-devel/bison-1.875
	>=sys-libs/glibc-2.8
	>=sys-devel/binutils-2.20"

if [[ ${CATEGORY} != cross-* ]] ; then
	PDEPEND="${PDEPEND} elibc_glibc? ( >=sys-libs/glibc-2.8 )"
fi

src_unpack() {
	gnatbuild_src_unpack

	#fixup some hardwired flags
	cd "${S}"/gcc/ada

	# universal gcc -> gnatgcc substitution occasionally produces lines too long
	# and then build halts on the style check.
	#
	sed -i -e 's:gnatgcc:gcc:' osint.ads switch.ads ||
		die	"reversing [gnat]gcc substitution in comments failed"

	# gcc pretty much ignores --with-system-zlib. At least it still descends
	# into zlib and does configure and build there (gcc bug@7125?). For whatever
	# reason this conflicts with multilib in gcc-4.4..
	sed -i -e "s:libgui zlib:libgui:" "${S}"/configure
}

src_configure() {
	gnatbuild_src_configure
}

src_compile() {
	# looks like gnatlib_and_tools and gnatlib_shared have become part of
	# bootstrap
	gnatbuild_src_compile configure make-tools bootstrap
}

src_install() {
	gnatbuild_src_install
}

