# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6
PYTHON_COMPAT=( python2_7 )
inherit multilib multiprocessing autotools python-single-r1

MYP=${PN}-gpl-${PV}

DESCRIPTION="GNAT Component Collection"
HOMEPAGE="http://libre.adacore.com"
SRC_URI="http://mirrors.cdn.adacore.com/art/591c45e2c7a447af2deed016
	-> ${MYP}-src.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64"
IUSE="gmp +system-gcc gnat_2017 gtk iconv postgresql pygobject projects readline
	+shared sqlite static static-pic syslog -tools"

RDEPEND="system-gcc? ( >=sys-devel/gcc-6.3.0[ada] )
	gnat_2017? ( dev-lang/gnat-gpl:6.3.0 )
	${PYTHON_DEPS}
	gmp? ( dev-libs/gmp:* )
	gtk? (
		dev-ada/gtkada[system-gcc?,gnat_2017?,shared?,static?]
		dev-libs/atk
		dev-libs/glib
		x11-libs/cairo
		x11-libs/gdk-pixbuf
		x11-libs/gtk+:3
		x11-libs/pango
	)
	pygobject? ( dev-python/pygobject:3[${PYTHON_USEDEP}] )
	postgresql? ( dev-db/postgresql:* )
	sqlite? ( dev-db/sqlite )
	projects? (
		>=dev-ada/gprbuild-2017[system-gcc?,gnat_2017?,shared?,static?]
	)
	static? (
		>=dev-ada/gprbuild-2017[system-gcc?,gnat_2017?,shared?,static=]
	)
	static-pic? (
		>=dev-ada/gprbuild-2017[system-gcc?,gnat_2017?,shared?,static=,static-pic=]
	)"
DEPEND="${RDEPEND}
	dev-ada/gprbuild[system-gcc?,gnat_2017?]"

REQUIRED_USE="${PYTHON_REQUIRED_USE}
	pygobject? ( gtk )
	tools? ( static static-pic )
	^^ ( system-gcc gnat_2017 )"

S="${WORKDIR}"/${MYP}-src

PATCHES=( "${FILESDIR}"/${P}-gentoo.patch )

src_prepare() {
	eapply -F 3 -- "${PATCHES[@]}"
	mv configure.{in,ac} || die
	eautoreconf

	eapply_user
}

src_configure() {
	if use system-gcc; then
		GCC_PV=$(gcc -dumpversion)
	else
		GCC_PV=6.3.0
	fi
	GCC=${CHOST}-gcc-${GCC_PV}
	GNATMAKE=${CHOST}-gnatmake-${GCC_PV}
	GNATCHOP=${CHOST}-gnatchop-${GCC_PV}
	if use sqlite; then
		myConf="--with-sqlite=$(get_libdir)"
	else
		myConf="--without-sqlite"
	fi
	if use gtk ; then
		myConf="$myConf --with-gtk=3.0"
	else
		myConf="$myConf --with-gtk=no"
	fi
	use static || myConf="$myConf --disable-static"

	econf \
		GNATCHOP="${GNATCHOP}" \
		GNATMAKE="${GNATMAKE}" \
		--with-python \
		$(use_with gmp) \
		$(use_with iconv) \
		$(use_with postgresql) \
		$(use_enable projects) \
		$(use_enable pygobject) \
		$(use_enable readline gpl) \
		$(use_enable readline) \
		$(use_enable static-pic) \
		$(use_enable syslog) \
		--with-python-exec=${EPYTHON} \
		--enable-shared-python \
		--disable-pygtk \
		CC=${GCC} \
		$myConf
}

src_compile() {
	if use shared; then
		emake PROCESSORS=$(makeopts_jobs) GPRBUILD_OPTIONS=-v GCC=${GCC} \
			build_library_type/relocatable
	fi
	if use static-pic; then
		emake PROCESSORS=$(makeopts_jobs) GPRBUILD_OPTIONS=-v GCC=${GCC} \
			build_library_type/static-pic
	fi
	if use static; then
		emake PROCESSORS=$(makeopts_jobs) GPRBUILD_OPTIONS=-v GCC=${GCC} \
			build_library_type/static
	fi
	if use tools; then
		emake PROCESSORS=$(makeopts_jobs) GPRBUILD_OPTIONS=-v GCC=${GCC} \
			build_tools/static
	fi
	python_fix_shebang .
}

src_install() {
	if use shared; then
		emake prefix="${D}usr" install_library_type/relocatable
	fi
	if use static-pic; then
		emake prefix="${D}usr" install_library_type/static-pic
	fi
	if use static; then
		emake prefix="${D}usr" install_library_type/static
	fi
	if use tools; then
		emake prefix="${D}usr" install_tools/static
	fi
	emake prefix="${D}usr" install_gps_plugin
	einstalldocs
}

src_test() {
	# The test suite is in
	# To run you need to have the ada compiler available as gcc
	# Even in this case there are still some problem
	# Going into the testsuite directory and running
	# ./run.py -v -v
	# run here (having enabled most USE flags)
	true
}
