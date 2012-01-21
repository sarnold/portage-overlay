# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils multilib

DESCRIPTION="Static Analysis component of the BitBlaze Binary Analysis Framework"
HOMEPAGE="http://bitblaze.cs.berkeley.edu/vine.html"
SRC_URI="http://bitblaze.cs.berkeley.edu/release/${P}/${P}.tar.gz"

LICENSE="LGPL-2.1"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE="debug +ocamlopt doc"

CDEPEND="dev-ml/ocamlgraph
	dev-ml/extlib
	dev-libs/gmetadom[ocaml]
	doc? (
		media-gfx/transfig
		virtual/latex-base
		dev-tex/hevea
		|| ( dev-texlive/texlive-latexextra
		    app-text/ptex )
		)"

RDEPEND="${CDEPEND}
	sci-mathematics/stp"

DEPEND="${CDEPEND}
	>=dev-lang/ocaml-3.10[ocamlopt?]
	>=dev-ml/camlp5-5.09[ocamlopt?]
	dev-ml/findlib
	dev-ml/camlidl"

src_prepare() {
	sed -i -e "s|) -g -O2|) ${CFLAGS} ${LDFLAGS}|" VEX/Makefile || die
	sed -i -e 's|"../c_interface.h"|<c_interface.h>|' \
		stp/ocaml/libstp_regerrorhandler.c || die
}

src_configure() {
	ocaml_lib="/usr/$(get_libdir)/ocaml"
	camlp5_dir="${ocaml_lib}/camlp5"
	local myconf="--disable-dependency-tracking
		--prefix /usr
		--bindir /usr/bin
		--libdir /usr/$(get_libdir)/vine
		--mandir /usr/share/man
		--docdir /usr/share/doc/${PF}
		--camlp5dir ${camlp5_dir}"

	use debug && myconf="--debug $myconf"
	use doc || myconf="$myconf --with-doc no"

#	use ocamlopt || myconf="$myconf -byte-only"
#	use ocamlopt && myconf="$myconf --opt"

#	export CAML_LD_LIBRARY_PATH="${S}/kernel/byterun/"
	econf $myconf || die "configure failed"
}

src_compile() {
	emake || die "make failed"
}

src_install() {
	emake DESTDIR="${D}" install || die
	dodoc README
}
