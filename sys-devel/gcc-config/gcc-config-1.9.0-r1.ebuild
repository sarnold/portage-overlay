# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit eutils toolchain-funcs multilib

DESCRIPTION="Utility to manage compilers"
HOMEPAGE="https://gitweb.gentoo.org/proj/gcc-config.git/"
SRC_URI="mirror://gentoo/${P}.tar.xz
	https://dev.gentoo.org/~dilfridge/distfiles/${P}.tar.xz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~hppa ~ia64 ~m68k ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~amd64-fbsd ~sparc-fbsd ~x86-fbsd"
IUSE=""

RDEPEND=">=sys-apps/gentoo-functions-0.10"

src_compile() {
	emake CC="$(tc-getCC)"
}

src_install() {
	emake \
		DESTDIR="${D}" \
		PV="${PV}" \
		SUBLIBDIR="$(get_libdir)" \
		install
}

pkg_postinst() {
	# Scrub eselect-compiler remains
	rm -f "${ROOT}"/etc/env.d/05compiler &

	# We not longer use the /usr/include/g++-v3 hacks, as
	# it is not needed ...
	rm -f "${ROOT}"/usr/include/g++{,-v3} &

	# Do we have a valid multi ver setup ?
	local x
	for x in $(gcc-config -C -l 2>/dev/null | awk '$NF == "*" { print $2 }') ; do
		gcc-config ${x}
	done

	wait

	# handle LTO plugin symlink
	gcc-config -C -O

	gcc_ver=$(gcc -dumpversion)
	gcc_path="../../../../libexec/gcc/${CHOST}/${gcc_ver}"

	if tc-is-cross-compiler ; then
		bin_path="${ROOT}/usr/${CHOST}/${CTARGET}/binutils-bin"
	else
		bin_path="${ROOT}/usr/${CHOST}/binutils-bin"
	fi

	[[ -d "${bin_path}/lib" ]] ||
		mkdir -p "${bin_path}"/lib/bfd-plugins

	pushd "${bin_path}"/lib/bfd-plugins/ > /dev/null
		ln -snf "${gcc_path}"/liblto_plugin.so.0.0.0
		ln -snf liblto_plugin.so.0.0.0 liblto_plugin.so.0
		ln -snf liblto_plugin.so.0.0.0 liblto_plugin.so
	popd > /dev/null
}
