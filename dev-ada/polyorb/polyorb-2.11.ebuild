# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id

EAPI="5"

inherit autotools base

IUSE="doc ssl"

DESCRIPTION="A CORBA implementation for Ada"
HOMEPAGE="http://libre.adacore.com/polyorb/"
SRC_URI="https://launchpad.net/~adconrad/+archive/ubuntu/ada-bootstrap/+files/polyorb_2.11~20140418.orig.tar.xz
	mirror://gentoo/polyorb-patches-2.11.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"

RDEPEND="ssl? ( dev-libs/openssl )"
DEPEND="${RDEPEND}
	sys-devel/gcc[ada]"

S="${WORKDIR}/${P}~20140418.orig"

PATCHES=(
	"${WORKDIR}"/polyorb-patches-${PV}/fix-pi-get-effective-component.patch
	"${WORKDIR}"/polyorb-patches-${PV}/enable-dynamic-libs-build.patch
	"${WORKDIR}"/polyorb-patches-${PV}/makefile-install-target.patch
	"${WORKDIR}"/polyorb-patches-${PV}/add-version-to-libraries.patch
	"${WORKDIR}"/polyorb-patches-${PV}/fix-manpage-has-errors-from-man.patch
	"${WORKDIR}"/polyorb-patches-${PV}/configure-local-makefile.patch
	"${WORKDIR}"/polyorb-patches-${PV}/debianize-polyorb-config-in.patch
	"${WORKDIR}"/polyorb-patches-${PV}/add-linker-option.patch
	"${WORKDIR}"/polyorb-patches-${PV}/link-polyorb-setup-with-services.patch
	"${WORKDIR}"/polyorb-patches-${PV}/remove-rtcorba.patch
	"${WORKDIR}"/polyorb-patches-${PV}/polyorb-config-patch-for-gnatdist.patch
	"${WORKDIR}"/polyorb-patches-${PV}/polyorb-config.patch
	"${WORKDIR}"/polyorb-patches-${PV}/disable-rtcorba-tests.patch
	"${WORKDIR}"/polyorb-patches-${PV}/bug-561121.patch
	"${WORKDIR}"/polyorb-patches-${PV}/handle-time-stamping-problem.patch
	"${WORKDIR}"/polyorb-patches-${PV}/fix-texi-syntax-error.patch
	"${WORKDIR}"/polyorb-patches-${PV}/remove-soap-in-tests.patch
	"${WORKDIR}"/polyorb-patches-${PV}/enforce-local-network-use.patch
	"${WORKDIR}"/polyorb-patches-${PV}/remove-unsupported-tests.patch
	"${WORKDIR}"/polyorb-patches-${PV}/hardening.patch
	"${WORKDIR}"/polyorb-patches-${PV}/new-warnings-handling.patch
	"${WORKDIR}"/polyorb-patches-${PV}/idlac-code-generation-handling.patch
	"${WORKDIR}"/polyorb-patches-${PV}/xe_back-polyorb.adb.patch
	"${WORKDIR}"/polyorb-patches-${PV}/support-tilde-in-pathname.patch
	"${WORKDIR}"/polyorb-patches-${PV}/make-clean.patch
	"${WORKDIR}"/polyorb-patches-${PV}/add-missing-include.patch
	"${WORKDIR}"/polyorb-patches-${PV}/examples_corba_echo_echo-impl.adb.patch
	"${FILESDIR}"/${P}-fix-build-gnatprfh-make-target.patch
)

EXTRA_ECONF="--with-gprbuild"

MAKEOPTS="-j1"

src_prepare() {
	sed -i -e "s|usr/lib|usr/$(get_libdir)|g" \
		"${S}"/polyorb-config.in || die

	AT_M4DIR=support eaclocal
	AT_M4DIR=support eautoheader
	AT_M4DIR=support eautoconf

	base_src_prepare

	pushd "${S}"/compilers/idlac > /dev/null
		python make_nodes.py nodes.txt > nodes.ada \
			&& gnatchop -w nodes.ada && rm -f nodes.ada

	popd > /dev/null

	sed -i -e 's:gnatwe:gnatwn:g' \
			"${S}"/projects/compilers_gnatdist.gpr \
			|| die "sed failed"
}

src_install() {
	emake DESTDIR=${D} install

	dodoc CHANGE_10049 FEATURES MANIFEST NEWS README
	doinfo docs/*.info
	if use doc; then
		dohtml docs/polyorb_ug.html/*.html
		insinto /usr/share/doc/${PF}
		doins docs/*.pdf

		dodir /usr/share/doc/${PF}/examples
		insinto /usr/share/doc/${PF}/examples
		doins -r examples/*
	fi
}
