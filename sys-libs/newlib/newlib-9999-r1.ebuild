# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="6"

inherit flag-o-matic toolchain-funcs

if [[ ${PV} == "9999" ]] ; then
	EGIT_REPO_URI="git://sourceware.org/git/newlib-cygwin.git"
	inherit git-r3
else
	SRC_URI="ftp://sourceware.org/pub/newlib/${P}.tar.gz"
	if [[ ${PV} != *.201[5-9]???? ]] ; then
		KEYWORDS="-* ~arm ~hppa ~m68k ~mips ~ppc ~ppc64 ~sh ~sparc ~x86"
	fi
fi

export CBUILD=${CBUILD:-${CHOST}}
export CTARGET=${CTARGET:-${CHOST}}
if [[ ${CTARGET} == ${CHOST} ]] ; then
	if [[ ${CATEGORY} == cross-* ]] ; then
		export CTARGET=${CATEGORY#cross-}
	fi
fi

DESCRIPTION="Newlib is a C library intended for use on embedded systems"
HOMEPAGE="https://sourceware.org/newlib/"

LICENSE="NEWLIB LIBGLOSS GPL-2"
SLOT="0"
IUSE="nls threads unicode crosscompile_opts_headers-only newlib-nano -newlib-supplied-syscalls"
RESTRICT="strip"

NEWLIBBUILD="${WORKDIR}/build"
NEWLIBNANOBUILD="${WORKDIR}/build.nano"
NEWLIBNANOTMPINSTALL="${WORKDIR}/nano_tmp_install"

CFLAGS_FULL="-ffunction-sections -fdata-sections"
CFLAGS_NANO="-Os -ffunction-sections -fdata-sections"

pkg_setup() {
	# Reject newlib-on-glibc type installs
	if [[ ${CTARGET} == ${CHOST} ]] ; then
		case ${CHOST} in
			*-newlib|*-elf) ;;
			*) die "Use sys-devel/crossdev to build a newlib toolchain" ;;
		esac
	fi
}

src_configure() {
	# we should fix this ...
	unset LDFLAGS
	CHOST=${CTARGET} strip-unsupported-flags
	CCASFLAGS_ORIG="${CCASFLAGS}"
	CFLAGS_ORIG="${CFLAGS}"

	local myconf=(
		# Disable legacy syscall stub code in newlib.  These have been
		# moved to libgloss for a long time now, so the code in newlib
		# itself just gets in the way.
		$(use_enable newlib-supplied-syscalls)
	)
	[[ ${CTARGET} == "spu" ]] \
		&& myconf+=( --disable-newlib-multithread ) \
		|| myconf+=( $(use_enable threads newlib-multithread) )

	mkdir -p "${NEWLIBBUILD}"
	cd "${NEWLIBBUILD}"

	export "CFLAGS_FOR_TARGET=${CFLAGS_ORIG} ${CFLAGS_FULL}"
	export "CCASFLAGS=${CCASFLAGS_ORIG} ${CFLAGS_FULL}"
	ECONF_SOURCE=${S} \
	econf \
		$(use_enable unicode newlib-mb) \
		$(use_enable nls) \
		--enable-newlib-io-long-long \
		--enable-newlib-register-fini \
		"${myconf[@]}"

	# Build newlib-nano beside newlib (original)
	# Based on https://tracker.debian.org/media/packages/n/newlib/rules-2.1.0%2Bgit20140818.1a8323b-2
	if use newlib-nano ; then
		mkdir -p "${NEWLIBNANOBUILD}"
		cd "${NEWLIBNANOBUILD}"
		export "CFLAGS_FOR_TARGET=${CFLAGS_ORIG} ${CFLAGS_NANO}"
		export "CCASFLAGS=${CCASFLAGS_ORIG} ${CFLAGS_NANO}"
		ECONF_SOURCE=${S} \
		econf \
			$(use_enable unicode newlib-mb) \
			$(use_enable nls) \
			--enable-newlib-reent-small \
			--disable-newlib-fvwrite-in-streamio \
			--disable-newlib-fseek-optimization \
			--disable-newlib-wide-orient \
			--enable-newlib-nano-malloc \
			--disable-newlib-unbuf-stream-opt \
			--enable-lite-exit \
			--enable-newlib-global-atexit \
			--enable-newlib-nano-formatted-io \
			${myconf}
	fi
}

src_compile() {
	export "CFLAGS_FOR_TARGET=${CFLAGS_ORIG} ${CFLAGS_FULL}"
	export "CCASFLAGS=${CCASFLAGS_ORIG} ${CFLAGS_FULL}"
	emake -C "${NEWLIBBUILD}"
	if use newlib-nano ; then
		export "CFLAGS_FOR_TARGET=${CFLAGS_ORIG} ${CFLAGS_NANO}"
		export "CCASFLAGS=${CCASFLAGS_ORIG} ${CFLAGS_NANO}"
		emake -C "${NEWLIBNANOBUILD}"
	fi
}

src_install() {
	cd "${NEWLIBBUILD}"
	emake -j1 DESTDIR="${D}" install
#	env -uRESTRICT CHOST=${CTARGET} prepallstrip

	if use newlib-nano ; then
		cd "${NEWLIBNANOBUILD}"
		emake -j1 DESTDIR="${NEWLIBNANOTMPINSTALL}" install
		# Rename nano lib* files to lib*_nano and move to the real ${D}
		# Avoid dependency on perl-rename by using a for loop instead.
		local nanolibfiles=""
		nanolibfiles=$(find "${NEWLIBNANOTMPINSTALL}" -regex ".*/lib\(c\|g\|rdimon\)\.a" -print)
		for f in ${nanolibfiles}; do
			local l="${f##${NEWLIBNANOTMPINSTALL}}"
			echo mv "${f}" "${D}/${l%%\.a}_nano.a"
			mv "${f}" "${D}/${l%%\.a}_nano.a"
		done
		# Move nano's version of newlib.h to nano/newlib.h
		mkdir -p ${D}/usr/${CTARGET}/include/nano
		mv ${NEWLIBNANOTMPINSTALL}/usr/${CTARGET}/include/newlib.h \
			${D}/usr/${CTARGET}/include/nano/newlib.h
	fi

	# minor hack to keep things clean
	rm -fR "${D}"/usr/share/info
	rm -fR "${D}"/usr/info
}
