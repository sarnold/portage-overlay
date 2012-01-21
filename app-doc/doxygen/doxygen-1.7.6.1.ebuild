# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/app-doc/doxygen/doxygen-1.7.5.1.ebuild,v 1.1 2011/11/05 21:30:54 nerdboy Exp $

RESTRICT="mirror"
EAPI=3

inherit eutils flag-o-matic toolchain-funcs qt4-r2 fdo-mime

DESCRIPTION="documentation system for C++, C, Java, Objective-C, Python, IDL, and other languages"
HOMEPAGE="http://www.doxygen.org/"
SRC_URI="ftp://ftp.stack.nl/pub/users/dimitri/${P}.src.tar.gz"

KEYWORDS="~alpha ~amd64 ~arm ~hppa ~ia64 ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~x86-fbsd ~x86-freebsd ~amd64-linux ~x86-linux ~ppc-macos ~x86-macos ~x86-solaris"

IUSE="debug doc nodot qt4 latex elibc_FreeBSD"
LICENSE="GPL-2"
SLOT="0"

RDEPEND="qt4? ( x11-libs/qt-gui:4 )
	latex? ( >=app-text/texlive-2008[extra] )
	dev-lang/python
	virtual/libiconv
	media-libs/libpng
	app-text/ghostscript-gpl
	!nodot? ( >=media-gfx/graphviz-2.20.0
		media-libs/freetype )"

DEPEND=">=sys-apps/sed-4
	sys-devel/flex
	${RDEPEND}"

EPATCH_SUFFIX="patch"

src_prepare() {
	# use CFLAGS, CXXFLAGS, LDFLAGS
	export ECFLAGS="${CFLAGS}" ECXXFLAGS="${CXXFLAGS}" ELDFLAGS="${LDFLAGS}"

	sed -i.orig -e 's:^\(TMAKE_CFLAGS_\(RELEASE\|DEBUG\)\s*\)=.*$:\1= $(ECFLAGS):' \
		-e 's:^\(TMAKE_CXXFLAGS_\(RELEASE\|DEBUG\)\s*\)=.*$:\1= $(ECXXFLAGS):' \
		-e 's:^\(TMAKE_LFLAGS_\(RELEASE\|DEBUG\)\s*\)=.*$:\1= $(ELDFLAGS):' \
		-e "s:^\(TMAKE_CC\s*=\).*$:\1 $(tc-getCC):g" \
		-e "s:^\(TMAKE_CXX\s*=\).*$:\1 $(tc-getCXX):g" \
		-e "s:^\(TMAKE_LINK\s*=\).*$:\1 $(tc-getCXX):g" \
		-e "/^TMAKE_AR\s*=/s:\<ar\>:$(tc-getAR):g" \
		tmake/lib/{{linux,gnu,freebsd,netbsd,openbsd,solaris}-g++,macosx-c++,linux-64}/tmake.conf \
		|| die "sed 1 failed"

	# Ensure we link to -liconv
	if use elibc_FreeBSD; then
		for pro in */*.pro.in */*/*.pro.in; do
		echo "unix:LIBS += -liconv" >> "${pro}"
		done
	fi

	# Call dot with -Teps instead of -Tps for EPS generation - bug #282150
	epatch "${FILESDIR}"/${PN}-1.7.5.1-dot-eps.patch

	# prefix search tools patch, plus OSX fixes
	epatch "${FILESDIR}"/${PN}-1.5.6-prefix-misc-alt.patch

	# enhancement patch from John
	epatch "${FILESDIR}"/${PN}-1.7.5.1-overloaded_methods_and_styles.patch

	# fix final DESTDIR issue
	sed -i.orig -e "s:\$(INSTALL):\$(DESTDIR)/\$(INSTALL):g" \
		addon/doxywizard/Makefile.in || die "sed 2 failed"

	# fix pdf doc
	sed -i.orig -e "s:g_kowal:g kowal:" \
		doc/maintainers.txt || die "sed 3 failed"

	if is-flagq "-O3" ; then
		echo
		ewarn "Compiling with -O3 is known to produce incorrectly"
		ewarn "optimized code which breaks doxygen."
		echo
		elog "Continuing with -O2 instead ..."
		echo
		replace-flags "-O3" "-O2"
	fi

	if use qt4; then
		# doxywizard built without respecting LDFLAGS,
		# so add eqmake4 wrapper flags here.
		cat >> "${S}/addon/doxywizard/doxywizard.pro.in" <<-EOF || die
			QMAKE_CC    = $(tc-getCC)
			QMAKE_CXX   = $(tc-getCXX)
			QMAKE_LINK  = $(tc-getCXX)
			QMAKE_CFLAGS_RELEASE    += ${CFLAGS}
			QMAKE_CFLAGS_DEBUG      += ${CFLAGS}
			QMAKE_CXXFLAGS_RELEASE  += ${CXXFLAGS}
			QMAKE_CXXFLAGS_DEBUG    += ${CXXFLAGS}
			QMAKE_LFLAGS_RELEASE    += ${LDFLAGS}
			QMAKE_LFLAGS_DEBUG      += ${LDFLAGS}
		EOF
	fi
}

src_configure() {
	# set ./configure options (prefix, Qt based wizard, docdir)

	local my_conf="--shared"

	if use debug ; then
		my_conf="${my_conf} --debug"
	else
		my_conf="${my_conf} --release "
	fi

	use ppc64 && my_conf="${my_conf} --english-only" #263641

	use qt4 && my_conf="${my_conf} --with-doxywizard"

	./configure --prefix "${EPREFIX}/usr" ${my_conf} \
			|| die 'configure failed'
}

src_compile() {
	emake all || die 'emake failed'

	# generate html and pdf (if tetex in use) documents.
	# errors here are not considered fatal, hence the ewarn message
	# TeX's font caching in /var/cache/fonts causes sandbox warnings,
	# so we allow it.
	if use doc; then
		if use nodot; then
			sed -i -e "s/HAVE_DOT               = YES/HAVE_DOT    = NO/" \
				{Doxyfile,doc/Doxyfile} \
				|| ewarn "disabling dot failed"
		fi
		if use latex; then
			addwrite /var/cache/fonts
			addwrite /var/cache/fontconfig
			addwrite /usr/share/texmf/fonts/pk
			addwrite /usr/share/texmf/ls-R
			make pdf || ewarn '"make pdf docs" failed.'
		else
			cp doc/Doxyfile doc/Doxyfile.orig
			cp doc/Makefile doc/Makefile.orig
			sed -i.orig -e "s/GENERATE_LATEX    = YES/GENERATE_LATEX    = NO/" \
				doc/Doxyfile
			sed -i.orig -e "s/@epstopdf/# @epstopdf/" \
				-e "s/@cp Makefile.latex/# @cp Makefile.latex/" \
				-e "s/@sed/# @sed/" doc/Makefile
			make docs || ewarn '"make docs" failed.'
		fi
	fi
}

src_install() {
	emake DESTDIR="${ED}" MAN1DIR=share/man/man1 \
		install || die '"make install" failed.'

	if use qt4; then
		doicon "${FILESDIR}/doxywizard.png"
		make_desktop_entry doxywizard "DoxyWizard ${PV}" \
			"/usr/share/pixmaps/doxywizard.png" \
			"Application;Development"
	fi

	dodoc INSTALL LANGUAGE.HOWTO README

	# pdf and html manuals
	if use doc; then
		dohtml -r html/*
		if use latex; then
			insinto /usr/share/doc/"${PF}"
			doins latex/doxygen_manual.pdf
		fi
	fi
}

pkg_postinst() {
	fdo-mime_desktop_database_update

	elog
	elog "The USE flags qt4, doc, and latex will enable doxywizard, or"
	elog "the html and pdf documentation, respectively.  For examples"
	elog "and other goodies, see the source tarball.  For some example"
	elog "output, run doxygen on the doxygen source using the Doxyfile"
	elog "provided in the top-level source dir."
	elog
	elog "Enabling the nodot USE flag will remove the GraphViz dependency,"
	elog "along with Doxygen's ability to generate diagrams in the docs."
	elog "See the Doxygen homepage for additional helper tools to parse"
	elog "more languages."
	elog
}

pkg_postrm() {
	fdo-mime_desktop_database_update
}
