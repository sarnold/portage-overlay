# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="4"

inherit eutils git-2 toolchain-funcs

DESCRIPTION="Oink: a Collaboration of C/C++ Tools for Static Analysis and Source-to-Source Transformation"
HOMEPAGE="http://daniel-wilkerson.appspot.com/oink/index.html"

EGIT_REPO_URI="http://github.com/sarnold/${PN}.git"
EGET_COMMIT="e864115312364a874a6dc1b075b80111b236ac34"

LICENSE="BSD"
SLOT="0"
KEYWORDS="~amd64 ~arm ~ppc ~x86"
IUSE="doc examples platform zipios"

RDEPEND="${DEPEND}"

DEPEND="sys-devel/flex
	<sys-devel/bison-3.0.2
	dev-lang/perl
	media-gfx/graphviz
	media-gfx/imagemagick
	platform? ( =sys-devel/gcc-3.4.6* )
	zipios? ( >=dev-libs/zipios-2.1.0 )"

# this is barely safe for serial compilation...
#MAKEOPTS+=" -j1" #nowarn

pkg_setup() {
	if [ -n "${OINK_CONFIGURE_OPTS}" ]; then
		elog ""
		elog "User-specified build options are ${OINK_CONFIGURE_OPTS}."
		elog ""
	else
		elog ""
		elog "User-specified build options are not set (default is perform)."
		elog "If needed, set OINK_CONFIGURE_OPTS to one of the following:"
		elog "debug, fastdebug, profile, profile-debug, perform"
		elog ""
	fi
}

src_prepare() {
	if has_version '>=dev-lang/perl-5.20.2' ; then
		epatch "${FILESDIR}"/${PN}-fix_perl_array_error.patch
	fi

	elog 'Please ignore the "obsolete option -I- used" warnings'
	elog 'as these tools will not build without abusing -I-.'

	# I tried a few other cleanups here to replace obsolete -I- but
	# this wonky source will not build correctly without major cleanup
	# because it depends on an old side-effect of -I-:
	# "In addition, the -I- option inhibits the use of the current
	# directory (where the current input file came from) as the first
	# search directory for #include "file"." (not the same as -I.)
	# Without this option there are conflicts up the wazoo...

	sed -i -e "s|pure_parser|pure-parser|" \
		"${S}"/elkhound/grampar.y \
		"${S}"/ast/agrampar.y || die

	# fix silly missing define
	sed -i -e "s|$(CXX) -c|$(CXX) -DFLEX_STD -c|" "${S}"/ast/Makefile.in
}

src_configure() {
	pkg_conf="${OINK_CONFIGURE_OPTS:=perform}"
	elog ""
	elog "The current Oink build setting is: ${pkg_conf}"

	if use platform ; then
		sed -i -e "s|= gcc-3.4|= /usr/bin/gcc-3.4.6|" \
			-e "s|cpp-3.4|/usr/bin/cpp-3.4.6|" \
			platform-model/Makefile.src.incl
		sed -i -e "s|gcc-3.4 -v|/usr/bin/gcc-3.4.6 -v|" \
			platform-model/configure
	fi

	if use zipios ; then
		pkg_conf="${pkg_conf} +oink:--enable-archive-srz-zip=yes"
	else
		pkg_conf="${pkg_conf} +oink:--enable-archive-srz-zip=no"
	fi

	./configure ${pkg_conf} || die

	make clean || die "make clean failed"

	sed -i \
		-e "s|\"doc/|\"elsa/|g" \
		-e "s|\.\./||g" \
		-e "s|\"gendoc|\"elsa/gendoc|" \
		elsa/index.html
}

src_compile() {
	# only a static build setup right now (please enhance :)
	emake CC=$(tc-getCC) CXX=$(tc-getCXX) -j1 all

	if use doc ; then
		for dir in {ast,elkhound,elsa,smbase} ; do
			make -C ${dir} doc || die "make doc in ${dir} failed"
		done
	fi
}

src_test() {
	## there is currently at least one assert failure in the
	## elkhound regression tests
	make CC=$(tc-getCC) CXX=$(tc-getCXX) check
	# || die "make check failed"
}

src_install() {
	dobin ast/{astgen,ccsstr} \
		elkhound/c/{cparse,lexer2} elkhound/elkhound \
		elsa/{ccparse,tlexer,filter_elsa_noise} \
		oink/{cfgprint,dfgprint,oink,qual,staticprint,xform} \
		|| die "dobin failed"

	insinto /usr/$(get_libdir)/${PN}
	doins smbase/libsmbase.a \
		elkhound/libelkhound.a \
		oink/libelsa.a \
		libqual/libqual.a \
		libregion/libregion.a \
		ast/libast.a || die "doins lib.a failed"

	insinto /usr/share/${PN}/config
	doins libqual/config/* || die "doins config failed"

	insinto /usr/include/${PN}/libqual
	doins libqual/{libqual.h,hash.h,bool.h,hash-serialize.h,typed_set.h} \
		libqual/{typed_bag.h,typed_ddlist.h,typed_hashset.h,typed_map.h} \
		|| die "doins libqual hdrs failed"

	insinto /usr/include/${PN}/libregion
	doins libregion/{cqual-stdint.h,mempool.h,miniregion.h,profile.h,regions.h} \
		|| die "doins libregion hdrs failed"

	insinto /usr/include/${PN}/elsa
	doins elsa/include/* || die "doins elsa hdrs failed"

	dodoc README.rst && newdoc elsa/toplevel/readme.txt elsa_readme.txt

	if use doc ; then
		newdoc elsa/index.html elsa-index.html
		for dir in {ast,elkhound,smbase} ; do
			docinto ${dir} && dohtml ${dir}/*.html
		done
		rm elsa/doc/index.html
		docinto elsa && dohtml elsa/doc/*
		insinto /usr/share/doc/${PF}/elsa \
			&& doins elsa/doc/*.{txt,dot}
		docinto oink && dohtml oink/Doc/*

		for dir in {ast,elkhound,elsa,smbase}/gendoc ; do
			insinto /usr/share/doc/${PF}/${dir} \
				&& doins ${dir}/*
		done

		if use examples ; then
			insinto /usr/share/doc/${PF}/elkhound/examples/
			doins -r elkhound/examples/*
		fi
	fi
}
