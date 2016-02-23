# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

PYTHON_COMPAT=( python2_7 python3_3 python3_4 )

inherit apache-module eutils python-single-r1

if [[ ${PV} == 9999* ]] ; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/grisha/mod_python.git"
else
	SRC_URI="http://dist.modpython.org/dist/${P}.tgz"
	KEYWORDS="alpha amd64 ~arm ia64 ~mips ppc sparc x86"
fi

DESCRIPTION="An Apache2 module providing an embedded Python interpreter"
HOMEPAGE="http://modpython.org/"

LICENSE="Apache-2.0"
IUSE="doc test"
SLOT="0"

APACHE2_MOD_CONF="16_${PN}"
APACHE2_MOD_DEFINE="PYTHON"
need_apache2

RDEPEND="${RDEPEND}"
DEPEND="${DEPEND}
	test? (
		app-admin/apache-tools
		net-misc/curl
	)"

src_prepare() {
	epatch "${FILESDIR}"/${P}-buildsystem.patch \
		"${FILESDIR}"/${P}-fix_thread_reload_crash.patch

	export CFLAGS="$(apxs2 -q CFLAGS)"
	export LDFLAGS="$(apxs2 -q LDFLAGS)"
}

src_compile() {
	default
}

src_test() {
	cd test || die
	PYTHONPATH="$(ls -d ${S}/dist/build/lib.*)" ${PYTHON} test.py || die
}

src_install() {
	default

	use doc && dohtml -r doc-html/*

	apache-module_src_install
}
