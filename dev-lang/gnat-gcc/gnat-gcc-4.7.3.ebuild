# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit gnatbuild

DESCRIPTION="GNAT Ada Compiler - gcc version"
HOMEPAGE="http://gcc.gnu.org/"
LICENSE="GMGPL"

IUSE="crossdev doc lto openmp"

BOOT_SLOT="4.4"

# SLOT is set in gnatbuild.eclass, depends only on PV (basically SLOT=GCCBRANCH)
# so the URI's are static.
SRC_URI="http://ftp.gnu.org/gnu/gcc/gcc-${PV}/gcc-${PV}.tar.bz2
	amd64? ( http://dev.gentoo.org/~george/src/gnatboot-${BOOT_SLOT}-amd64.tar.bz2 )
	sparc? ( http://dev.gentoo.org/~george/src/gnatboot-${BOOT_SLOT}-sparc.tar.bz2 )
	x86?   ( http://dev.gentoo.org/~george/src/gnatboot-${BOOT_SLOT}-i686.tar.bz2 )
	arm?   ( http://www.gentoogeek.org/files/gnatboot-${BOOT_SLOT}-arm.tar.bz2 )"
#	ppc?   ( mirror://gentoo/gnatboot-${BOOT_SLOT}-ppc.tar.bz2 )

KEYWORDS="~amd64 ~arm ~x86 ~sparc"

# starting with 4.3.0 gnat needs these libs
RDEPEND=">=dev-libs/mpfr-3.1.2
	>=dev-libs/gmp-5.1.3
	>=dev-libs/mpc-1.0.1
	>=sys-libs/zlib-1.2
	>=sys-libs/ncurses-5.7"

DEPEND="${RDEPEND}
	doc? ( >=sys-apps/texinfo-5 )
	>=sys-devel/bison-1.875
	>=sys-libs/glibc-2.8
	>=sys-devel/binutils-2.20"

#QA_EXECSTACK="${BINPATH:1}/gnatls ${BINPATH:1}/gnatbind ${BINPATH:1}/gnatmake
#	${LIBEXECPATH:1}/gnat1 ${LIBPATH:1}/adalib/libgnat-${SLOT}.so"

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

	if use crossdev ; then
		# need generic numaux for crossdev gnat-gcc
		einfo "Switching numaux to IEEE 64-bit..."
		BOOTSTRAP_ADA_INC="${WORKDIR}/usr/lib/adainclude"
		cp a-numaux.ads a-numaux-x86.ads
		cp a-numaux.ads a-numaux-libc-x86.ads
		cp a-numaux.ads "${BOOTSTRAP_ADA_INC}"/a-numaux.ads
		rm -f a-numaux-x86.adb a-numaux.adb "${BOOTSTRAP_ADA_INC}"/a-numaux.adb

		epatch "${FILESDIR}"/${P}-Makefile.in-numaux.patch
	fi

	# add patch for arm hardfloat
	cd "${S}"
	is-flagq -mfloat-abi=hard && epatch "${FILESDIR}"/gnat-hardfloat.patch
}

src_compile() {
	# looks like gnatlib_and_tools and gnatlib_shared have become part of
	# bootstrap
	gnatbuild_src_compile configure make-tools

	gnatbuild_src_compile bootstrap
}

