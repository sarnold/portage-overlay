# Copyright 1999-2013 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="4"

inherit eutils git-2 toolchain-funcs

DESCRIPTION="Oink: a Collaboration of C/C++ Tools for Static Analysis and Source-to-Source Transformation"
HOMEPAGE="http://daniel-wilkerson.appspot.com/oink/index.html"
EGIT_REPO_URI="http://github.com/dsw/${PN}.git"
SRC_URI=""

LICENSE="BSD"
SLOT="0"
KEYWORDS="~amd64 ~ppc ~x86"
IUSE="doc examples platform -zlib1g"

RDEPEND="${DEPEND}"

DEPEND="sys-devel/bison
	sys-devel/flex
	dev-lang/perl
	media-gfx/graphviz
	media-gfx/imagemagick
	platform? ( =sys-devel/gcc-3.4.6* )"
#	zlib1g? ( dev-libs/foo )"

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

src_unpack() {
	git_src_unpack
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
#		use zlib1g && \
#			pkg_conf="${pkg_conf} +oink:--enable-archive-srz-zip=yes"
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
	emake CC=$(tc-getCC) CXX=$(tc-getCXX) all || die "make failed"

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

	into /usr/$(get_libdir)/${PN}
	dolib.a smbase/libsmbase.a \
		elkhound/libelkhound.a \
		oink/libelsa.a \
		libqual/libqual.a \
		libregion/libregion.a \
		ast/libast.a || die "dolib.a failed"

	insinto /usr/$(get_libdir)/${PN}/config
	doins libqual/config/* || die "doins config failed"

	insinto /usr/$(get_libdir)/${PN}/include
	doins libqual/{libqual.h,hash.h,bool.h,hash-serialize.h,typed_set.h} \
		libqual/{typed_bag.h,typed_ddlist.h,typed_hashset.h,typed_map.h} \
		libregion/{cqual-stdint.h,mempool.h,miniregion.h,profile.h,regions.h} \
		|| die "doins hdrs failed"

	insinto /usr/$(get_libdir)/elsa/include
	doins elsa/include/* || die "doins elsa hdrs failed"

	dodoc README && newdoc elsa/toplevel/readme.txt elsa_readme.txt

	if use doc ; then
		newdoc elsa/index.html elsa-index.html
		for dir in {ast,elkhound,smbase} ; do
			docinto ${dir} && dohtml ${dir}/*.html
		done
		rm elsa/doc/index.html
		docinto elsa && dohtml elsa/doc/*
		insinto /usr/share/doc/${PF}/elsa \
			&& doins elsa/*.{txt,ps,dot,fig}
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
