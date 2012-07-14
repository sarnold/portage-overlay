# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils flag-o-matic multilib toolchain-funcs

MY_PN="${PN}_source"
MY_PV="v${PV}"
MY_P="${MY_PN}_${MY_PV}"

DESCRIPTION="NOAA/PMEL's scientific visualization and analysis tool for gridded and non-gridded data."
HOMEPAGE="http://ferret.wrc.noaa.gov/Ferret/"
SRC_URI="ftp://ftp.pmel.noaa.gov/ferret/special_request/ansley/${MY_P}.tar.gz
 ftp://ftp.pmel.noaa.gov/ferret/pub/linux/fer_environment.tar.Z
 dsets? ( ftp://ftp.pmel.noaa.gov/ferret/pub/data/fer_dsets.tar.Z )"

LICENSE="US-DOC"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~ppc64 ~x86"
IUSE="doc dsets examples extras"

RDEPEND="x11-libs/libX11
	x11-libs/libXp
	x11-libs/libXpm
	x11-libs/libXmu
	x11-libs/libXt
	x11-libs/libSM
	x11-libs/libICE
	x11-libs/libXext"

DEPEND="${RDEPEND}
	sys-libs/readline
	x11-proto/xproto
	x11-proto/xextproto
	dev-libs/liblist
	sys-libs/ncurses
	sci-libs/hdf
	sci-libs/netcdf
	sci-libs/libnc-dap
	sci-libs/libdap
	sci-libs/xgks-pmel"

S="${WORKDIR}/FERRET"

src_prepare() {
	rm -rf readline-4.1 readline list-2.1 fmt/src/list.h
	find . -type d -name CVS | xargs rm -rf
	mkdir lib ppl/lib
	edos2unix fmt/src/NCF_Util.c

	local HOSTTYPE="${CHOST}"
	cp ${FILESDIR}/platform_specific_flags.gentoo.fer \
	    platform_specific_flags.mk.${HOSTTYPE}

	sed -i \
	    -e "s#gcc-include#/usr/$(get_libdir)/gcc/${CHOST}/$(gcc-fullversion)/include#" \
	    -e "s#gcc-finclude#/usr/$(get_libdir)/gcc/${CHOST}/$(gcc-fullversion)/finclude#" \
	    -e "s#Gentoo#$(uname -mri)#" \
	    -e "s:CC              = cc:CC              = $(tc-getCC):" \
	    -e "s:g77:${FORTRANC}:" \
	    -e "s:/usr/bin/ranlib:$(tc-getRANLIB):" \
	    -e "s:/lib/cpp:$(tc-getCPP):" \
	    -e "s:LD              = cc:LD              = $(tc-getLD):" \
	    -e "s:lib64:$(get_libdir):g" \
	    platform_specific_flags.mk.${HOSTTYPE} \
	    || die "sed 1 failed"

	cp platform_specific_flags.mk.${HOSTTYPE} "${S}"/fer
	cp platform_specific_flags.mk.${HOSTTYPE} "${S}"/ppl
	use extras && cp \
	    ${FILESDIR}/platform_specific_flags.gentoo.ext \
	    "${S}"/external_functions/ef_utility/platform_specific_flags.mk.${HOSTTYPE}

	# make some code and Makefile fix-ups...
	sed -i -e "s:../list-2.1:/usr/$(get_libdir):g" \
	    fer/Makefile || die "sed 2 failed"
	sed -i -e "s:defined(__STDC:!defined(__STDC:g" \
	    fer/gui/UxXt.h || die "sed 3 failed"
	epatch "${FILESDIR}"/${P}-toolchain-update.patch
	epatch "${FILESDIR}"/${P}-ccr-update.patch
	epatch "${FILESDIR}"/gksm2ps-update.patch

	# fix the gks2ps Makefile
	sed -i \
	    -e "s|x86_64-linux|${HOSTTYPE}|" \
	    -e "s|CC=gcc|CC=$(tc-getCC)|g" \
	    -e "s|lib64|$(get_libdir)|g" \
	    -e "s|my_flags|${CFLAGS}|"
	    -e "s|gcc-include|/usr/$(get_libdir)/gcc/${CHOST}/$(gcc-fullversion)/include|" \
	    gksm2ps/Makefile || die "sed 4 failed"

	# ditto for the external functions
	sed -i \
	    -e "s|= cc|= $(tc-getCC)|g" \
	    -e "s|g77|${FORTRANC}|g" \
	    -e "s|my_flags|${CFLAGS}|"
	    -e "s|/usr/bin/ranlib$(tc-getRANLIB)||" \
	    -e "s|/lib/cpp|$(tc-getCPP)|" \
	    external_functions/Makefile || die "sed 5 failed"
}

src_compile() {
	export TMAP_LOCAL="${S}/ppl"
	export HOSTTYPE="${CHOST}"

	cd "${S}/fer"
	make -j1 update || die "make update failed"
	cd "${S}/fer/plt"
	make  || die "make plt failed"
	cd "${S}/fer"
	make -j1 DODS_gui || die "make DODS_gui failed"

	cd ${S}/gksm2ps
	make -j1 ${HOSTTYPE} || die "make gksm2ps failed"

	if use extras; then
	    cd ${S}/external_functions
	    make -j1 || die "make extras failed"
	fi
}

src_install() {
	FER_DIR="/opt/ferret"
	generate_files

	use examples && sed -i \
	    -e "s|DIR/go |DIR/go \$FER_DIR/examples |" 99ferret
	
	cd "${S}/fer"
	doicon gui/noaatiny.xpm
	make_desktop_entry /opt/ferret/bin/ferretdods_gui "Ferret ${PV}" \
	     "/usr/share/pixmaps/noaatiny.xpm" "Science;Education" \
	     "/opt/ferret/bin"

	cd "${S}"
	into ${FER_DIR}
	dobin fer/ferretdods_gui
	dobin gksm2ps/gksm2ps

	insinto ${FER_DIR}/ppl/fonts
	case "${ARCH}" in
	    amd64)
		doins "${WORKDIR}/bin/fonts_x86_64-linux/*"
		;;
	    sparc)
		doins "${WORKDIR}/bin/fonts_solaris/*"
		;;
	    x86)
		doins "${WORKDIR}/bin/fonts_linux/*"
		;;
	esac

	if use doc; then
	    insinto /usr/share/doc/${P}
	    doins "${WORKDIR}/doc/think_ferret.txt"
	    doins "${WORKDIR}/doc/grid_concepts.txt"
	    doins "${WORKDIR}/doc/ferret_users_guide.txt"
	fi
}

pkg_postinst() {
	elog "Nothing here yet."
}

generate_files() {
	cat <<-EOF > 99ferret
	FER_DIR="/opt/ferret"
	FER_DSETS="$FER_DIR/fer_dsets"
	PATH="$PATH:$FER_DIR/bin"
	FER_WEB_BROWSER="gnome-moz-remote %s"
	FER_EXTERNAL_FUNCTIONS="$FER_DIR/ext_func/libs"
	FER_GO=". $FER_DIR/go $FER_DIR/contrib"
	FER_DATA=". $FER_DSETS/data $FER_GO"
	FER_DESCR=". $FER_DSETS/descr"
	FER_GRIDS=". $FER_DSETS/grids"
	TMAP="$FER_DIR/fmt"
	PLOTFONTS="$FER_DIR/ppl/fonts"
	FER_PALETTE=". $FER_DIR/ppl"
	EOF
}
