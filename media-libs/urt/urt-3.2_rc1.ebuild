# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"

inherit eutils toolchain-funcs

DESCRIPTION="the Utah Raster Toolkit is a library for dealing with raster images"
HOMEPAGE="http://www.cs.utah.edu/gdc/projects/urt/"
if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="git://github.com/sarnold/urt.git"
	inherit git-2
else
	SRC_URI="https://github.com/sarnold/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"
fi

LICENSE="URT gif? ( free-noncomm )"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~m68k ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~amd64-fbsd ~x86-fbsd ~amd64-linux ~x86-linux ~ppc-macos ~x86-macos ~x64-solaris ~x86-solaris"
IUSE="-cproto gif postscript static-libs tiff X"

RDEPEND="X? ( x11-libs/libXext
		x11-libs/libX11 )
	gif? ( media-libs/giflib )
	tiff? ( media-libs/tiff )
	postscript? ( app-text/ghostscript-gpl )"

DEPEND="${RDEPEND}
	cproto? ( dev-util/cproto )
	X? ( x11-proto/xproto )"

urt_config() {
	use $1 && echo "#define $2" || echo "##define $2"
}

src_prepare() {
	rm -f bin/README

	# These are QA flags needed to address QA runtime warnings:
	# -DNO_ITIMER workaround for deprecated BSD form of sigpause
	QAFLAGS="-DNO_ITIMER"
	# These are enabled by default in Gentoo config:
	# -DX_SHARED_MEMORY enable X shm
	# -DUSE_PROTOTYPES generate prototypes.h and fn_decls.h with cproto
	OPTFLAGS="-D_DEFAULT_SOURCE"

	cp "${FILESDIR}"/gentoo-config config/gentoo
	cat >> config/gentoo <<-EOF
	$(urt_config cproto HAVE_CPROTO)
	$(urt_config X X11)
	$(urt_config postscript POSTSCRIPT)
	$(urt_config tiff TIFF)
	ExtraCFLAGS = ${CFLAGS} ${QAFLAGS} ${OPTFLAGS}
	MFLAGS = ${MAKEOPTS}
	# prevent circular depend #111455
	$(has_version media-libs/giflib && urt_config gif GIF)
	EOF
}

src_configure() {
	./Configure config/gentoo || die "config failed"
}

src_compile() {
	export AR="$(tc-getAR) rc" CC="$(tc-getCC)" CPP="$(tc-getCPP)"

	emake || die "emake failed"
}

src_install() {
	mkdir -p man-dest/man{1,3,5}

	# this just installs it into some local dirs
	make install || die "pre-install failed"

	dobin bin/* || die "dobin failed"
	dolib.so lib/librle.so* || die "dolib.so failed"

	if use static-libs ; then
		dolib.a lib/librle.a
	else
		rm -f "${ED}"usr/$(get_libdir)/librle.a
	fi

	insinto /usr/include
	doins include/rle*.h || die "doins include failed"

	doman man-dest/man?/*.[135]
	dodoc *-changes CHANGES* README.rst blurb
}
