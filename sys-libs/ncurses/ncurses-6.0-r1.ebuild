# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"

inherit eutils flag-o-matic toolchain-funcs gnat-r1 versionator multilib-minimal multiprocessing

MY_PV=${PV:0:3}
PV_SNAP=${PV:4}
MY_P=${PN}-${MY_PV}
DESCRIPTION="console display library"
HOMEPAGE="https://www.gnu.org/software/ncurses/ http://dickey.his.com/ncurses/"
SRC_URI="mirror://gnu/ncurses/${MY_P}.tar.gz"

LICENSE="MIT"
# The subslot reflects the SONAME.
SLOT="0/6"
KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~m68k ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~amd64-fbsd ~sparc-fbsd ~x86-fbsd"
IUSE="ada +cxx debug doc gpm minimal profile static-libs test threads tinfo trace unicode"

DEPEND="gpm? ( sys-libs/gpm[${MULTILIB_USEDEP}] )
	ada? ( >=virtual/ada-1995 )"
#	berkdb? ( sys-libs/db )"
# Block the older ncurses that installed all files w/SLOT=5. #557472
RDEPEND="${DEPEND}
	!<=sys-libs/ncurses-5.9-r4:5
	!<x11-terms/rxvt-unicode-9.06-r3
	!<x11-terms/st-0.6-r1
	!app-emulation/emul-linux-x86-baselibs"

S=${WORKDIR}/${MY_P}

PATCHES=(
	"${FILESDIR}/${PN}-6.0-gfbsd.patch"
	"${FILESDIR}/${PN}-5.7-nongnu.patch"
	"${FILESDIR}/${PN}-6.0-rxvt-unicode-9.15.patch" #192083 #383871
	"${FILESDIR}/${PN}-6.0-pkg-config.patch"
	"${FILESDIR}/${PN}-5.9-gcc-5.patch" #545114
	"${FILESDIR}/${PN}-6.0-ticlib.patch" #557360
	"${FILESDIR}/${PN}-6.0-ada-lib-suffix.patch"
#	"${FILESDIR}/${PN}-6.0-ada-configure.patch"
#	"${FILESDIR}/${PN}-6.0-ada-makefile.patch"
#	"${FILESDIR}/${PN}-6.0-ada-project.patch"
)

src_prepare() {
	[[ -n ${PV_SNAP} ]] && epatch "${WORKDIR}"/${MY_P}-${PV_SNAP}-patch.sh
	epatch "${PATCHES[@]}"
}

src_configure() {
	unset TERMINFO #115036
	tc-export_build_env BUILD_{CC,CPP}
	BUILD_CPPFLAGS+=" -D_GNU_SOURCE" #214642

	if [[ ${ARCH} == arm* ]] ; then
		append-libs "-L/$(get_libdir) -ldl"
	fi

	# Build the various variants of ncurses -- narrow, wide, and threaded. #510440
	# Order matters here -- we want unicode/thread versions to come last so that the
	# binaries in /usr/bin support both wide and narrow.
	# The naming is also important as we use these directly with filenames and when
	# checking configure flags.
	NCURSES_TARGETS=(
		ncurses
		$(usex unicode 'ncursesw' '')
		$(usex threads 'ncursest' '')
		$(use unicode && usex threads 'ncursestw' '')
	)

	if [[ "${ARCH}" != "arm" ]] ; then
		multijob_init

	# When installing ncurses, we have to use a compatible version of tic.
	# This comes up when cross-compiling, doing multilib builds, upgrading,
	# or installing for the first time.  Build a local copy of tic whenever
	# the host version isn't available. #249363 #557598
		if ! ROOT=/ has_version "~sys-libs/${P}:0" ; then
			local lbuildflags="-static"

			# some toolchains don't quite support static linking
			local dbuildflags="-Wl,-rpath,${WORKDIR}/lib"
			case ${CHOST} in
				*-darwin*)  dbuildflags=     ;;
				*-aix*)     dbuildflags=     ;;
			esac
			echo "int main() {}" | \
				$(tc-getCC) -o x -x c - ${lbuildflags} -pipe >& /dev/null \
				|| lbuildflags="${dbuildflags}"

			# We can't re-use the multilib BUILD_DIR because we run outside of it.
			BUILD_DIR="${WORKDIR}" \
			CHOST=${CBUILD} \
			CFLAGS=${BUILD_CFLAGS} \
			CXXFLAGS=${BUILD_CXXFLAGS} \
			CPPFLAGS=${BUILD_CPPFLAGS} \
			LDFLAGS="${BUILD_LDFLAGS} ${lbuildflags}" \

			multijob_child_init do_configure cross --without-shared --with-normal
		fi
		multilib-minimal_src_configure
		multijob_finish
	else
		multilib-minimal_src_configure
	fi
}

multilib_src_configure() {
	local t
	for t in "${NCURSES_TARGETS[@]}" ; do
		if [[ ${ARCH} == "arm" ]] ; then
			do_configure "${t}"
		else
			multijob_child_init do_configure "${t}"
		fi
	done
}

do_configure() {
	local target=$1
	shift

	mkdir "${BUILD_DIR}/${target}"
	cd "${BUILD_DIR}/${target}" || die

	local conf=(
		# We need the basic terminfo files in /etc, bug #37026.  We will
		# add '--with-terminfo-dirs' and then populate /etc/terminfo in
		# src_install() ...
		--with-terminfo-dirs="${EPREFIX}/etc/terminfo:${EPREFIX}/usr/share/terminfo"

		# Disabled until #245417 is sorted out.
		#$(use_with berkdb hashed-db)

		# ncurses is dumb and doesn't install .pc files unless pkg-config
		# is also installed.  Force the tests to go our way.  Note that it
		# doesn't actually use pkg-config ... it just looks for set vars.
		--enable-pc-files
		--with-pkg-config="$(tc-getPKG_CONFIG)"
		# This path is used to control where the .pc files are installed.
		--with-pkg-config-libdir="${EPREFIX}/usr/$(get_libdir)/pkgconfig"

		# Now the rest of the various standard flags.
		--with-shared
		--without-hashed-db
		$(use_with cxx)
		$(use_with cxx cxx-binding)
		--with-cxx-shared
		$(use_with debug)
		$(use_with profile)
		# The configure script uses ldd to parse the linked output which
		# is flaky for cross-compiling/multilib/ldd versions/etc...
		$(use_with gpm gpm libgpm.so.1)
		--disable-termcap
		--enable-symlinks
		--with-rcs-ids
		--with-manpage-format=normal
		--enable-const
		--enable-colorfgbg
		--enable-hard-tabs
		--enable-echo
		$(multilib_native_with ada)
		# $(use_with ada)
		$(use_enable !ada warnings)
		$(use_with debug assertions)
		$(use_enable !debug leaks)
		$(use_with debug expanded)
		$(use_with !debug macros)
		$(multilib_native_with progs)
		$(use_with test tests)
		$(use_with trace)
		$(use_with tinfo termlib)
	)

	if [[ ${target} == ncurses*w ]] ; then
		conf+=( --enable-widec )
	else
		conf+=( --disable-widec )
	fi
	if [[ ${target} == ncursest* ]] ; then
		conf+=( --with-{pthread,reentrant} )
	else
		conf+=( --without-{pthread,reentrant} )
	fi
	# Make sure each variant goes in a unique location.
	if [[ ${target} == "ncurses" ]] ; then
		# "ncurses" variant goes into "${EPREFIX}"/usr/include
		# It is needed on Prefix because the configure script appends
		# "ncurses" to "${prefix}/include" if "${prefix}" is not /usr.
		conf+=( --enable-overwrite )
	else
		conf+=( --includedir="${EPREFIX}"/usr/include/${target} )
	fi
	# See comments in src_configure.
	if [[ ${target} != "cross" ]] ; then
		local cross_path="${WORKDIR}/cross"
		[[ -d ${cross_path} ]] && export TIC_PATH="${cross_path}/progs/tic"
	fi

	# try enabling Ada support again
	if use ada ; then
		unset ADAMAKEFLAGS
#		MULTILIB_COMPAT=( abi_x86_{32,64} )
#		if ! multilib_is_native_abi ; then
#			# configure is pretty weird...
#			BITSARG="32"
#			export BITSFLAG="-m${BITSARG}"
#			export RTSFLAG="--RTS=${BITSARG}"
#			RTSPATH="/usr/lib/gnat-gcc/x86_64-pc-linux-gnu/4.9/${BITSARG}"
#			ARCH_LARGS="${RTSPATH}/adalib"
#			ARCH_PATH="-aI${RTSPATH}/adainclude -aO${ARCH_LARGS}"
#			ARCHFLAGS="${BITSFLAG} ${ARCH_PATH}"
#			LDFLAGS="${LDFLAGS} -Wl,-m32 -Wl,-m,elf_i386"
#			LINKFLAGS="-largs -lgnat"
			AdalibLibTop=${PREFIX}/$(get_libdir)/ada
#			EXTRA_RPATH="/usr/lib32 /lib32 ${RTSPATH} ${ARCH_LARG}"
#			conf+=( --with-ada-compiler="gnatmake ${BITSFLAG}" )
#		else
#			ARCHFLAGS=""
#			BITSFLAG=""
#			BITSARG="64"
#			RTSPATH="/usr/lib/gnat-gcc/x86_64-pc-linux-gnu/4.9"
#		fi

#		sed -i -e "s|\$(CFLAGS_default)|${BITSFLAG}|" \
#			"${S}"/Ada95/src/Makefile.in

		conf+=( --with-ada-sharedlib="libada${target}.so.${PV}" )
		conf+=(
			--with-ada-include="${AdalibSpecsDir}/${target}"
			--with-ada-objects="${AdalibLibTop}/${target}"
		)
	fi

	# Force bash until upstream rebuilds the configure script with a newer
	# version of autotools. #545532
	# Note use=ada requires LIB_NAME and the patch to build just the native
	# libs correctly (teensy bit of bit-rot in the Ada source tree).  All
	# the rest of the shennanigans does not fix multilib/x86...
	CONFIG_SHELL=${BASH} \
	ECONF_SOURCE=${S} \
	LIB_NAME=${target} \
	econf "${conf[@]}" "$@"
}

src_compile() {
	if [[ "${ARCH}" != "arm" ]] ; then
		# See comments in src_configure.
		if ! ROOT=/ has_version "~sys-libs/${P}:0" ; then
			BUILD_DIR="${WORKDIR}" \
			do_compile cross -C progs tic
		fi
	fi

	multilib-minimal_src_compile
}

multilib_src_compile() {
	local t
	for t in "${NCURSES_TARGETS[@]}" ; do
		do_compile "${t}"
	done
}

do_compile() {
	local target=$1
	shift

	cd "${BUILD_DIR}/${target}" || die

	# A little hack to fix parallel builds ... they break when
	# generating sources so if we generate the sources first (in
	# non-parallel), we can then build the rest of the package
	# in parallel.  This is not really a perf hit since the source
	# generation is quite small.
	emake -j1 sources
	# For some reason, sources depends on pc-files which depends on
	# compiled libraries which depends on sources which ...
	# Manually delete the pc-files file so the install step will
	# create the .pc files we want.
	rm -f misc/pc-files
	if use ada ; then
		BUILD_DIR="${BUILD_DIR}/${target}" \
		SOURCE_DIR="${S}/Ada95" \
		emake "$@"
	else
		emake "$@"
	fi
}

multilib_src_install() {
	local target
	for target in "${NCURSES_TARGETS[@]}" ; do
		emake -C "${BUILD_DIR}/${target}" DESTDIR="${ED}" install
		if use ada && multilib_is_native_abi ; then
			dosym libada${target}$(get_libname).${PV} \
				/usr/$(get_libdir)/libada${target}$(get_libname $(get_major_version))
		fi
	done

	# Move main libraries into /.
	# Note the Ada libs don't need pkgconfig or libtool
	if multilib_is_native_abi ; then
		gen_usr_ldscript -a \
			"${NCURSES_TARGETS[@]}" \
			$(use tinfo && usex unicode 'tinfow' '') \
			$(usev tinfo)
	fi
	if ! tc-is-static-only ; then
		# Provide a link for -lcurses and -lAdaCurses.
		dosym libncurses$(get_libname) /usr/$(get_libdir)/libcurses$(get_libname)
		if use ada && multilib_is_native_abi ; then
			dosym libadancurses$(get_libname) \
				/usr/$(get_libdir)/libAdaCurses$(get_libname)
		fi
	fi
	use static-libs || find "${ED}"/usr/ -name '*.a' -delete

	# Build fails to create this ...
	dosym ../share/terminfo /usr/$(get_libdir)/terminfo

	if use ada ; then
		local target="ncurses"
#		for target in "${NCURSES_TARGETS[@]}" ; do
			insinto ${AdalibgprDir}
			doins "${FILESDIR}"/ada${target}.gpr
			use tinfo || sed -i -e 's|"-ltinfo", ||' \
				"${ED}/${AdalibgprDir}"/ada${target}.gpr
#		done
	fi
}

multilib_src_install_all() {
#	if ! use berkdb ; then
		# We need the basic terminfo files in /etc, bug #37026
		einfo "Installing basic terminfo files in /etc..."
		for x in ansi console dumb linux rxvt rxvt-unicode screen sun vt{52,100,102,200,220} \
				 xterm xterm-color xterm-xfree86
		do
			local termfile=$(find "${ED}"/usr/share/terminfo/ -name "${x}" 2>/dev/null)
			local basedir=$(basename $(dirname "${termfile}"))

			if [[ -n ${termfile} ]] ; then
				dodir /etc/terminfo/${basedir}
				mv ${termfile} "${ED}"/etc/terminfo/${basedir}/
				dosym ../../../../etc/terminfo/${basedir}/${x} \
					/usr/share/terminfo/${basedir}/${x}
			fi
		done
#	fi

	echo "CONFIG_PROTECT_MASK=\"/etc/terminfo\"" > "${T}"/50ncurses
	doenvd "${T}"/50ncurses

	use minimal && rm -r "${ED}"/usr/share/terminfo*
	# Because ncurses5-config --terminfo returns the directory we keep it
	keepdir /usr/share/terminfo #245374

	cd "${S}"
	dodoc ANNOUNCE MANIFEST NEWS README* TO-DO doc/*.doc
	use doc && dohtml -r doc/html/
}

pkg_preinst() {
	preserve_old_lib /$(get_libdir)/libncurses.so.5
	use unicode && preserve_old_lib /$(get_libdir)/libncursesw.so.5
}

pkg_postinst() {
	preserve_old_lib_notify /$(get_libdir)/libncurses.so.5
	use unicode && preserve_old_lib_notify /$(get_libdir)/libncursesw.so.5
}
