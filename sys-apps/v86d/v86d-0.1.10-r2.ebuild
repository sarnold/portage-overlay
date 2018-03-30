# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5

inherit eutils flag-o-matic linux-info multilib toolchain-funcs

DESCRIPTION="A daemon to run x86 code in an emulated environment"
HOMEPAGE="https://github.com/sarnold/v86d"
SRC_URI="https://github.com/sarnold/v86d/archive/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 x86"
IUSE="debug x86emu"

DEPEND="dev-libs/libx86
	dev-libs/klibc"

RDEPEND="${DEPEND}"

S="${WORKDIR}/${PN}-86d-${PV}"

pkg_setup() {
	linux-info_pkg_setup
}

src_prepare() {
#	if [ -z "$(grep V86D ${ROOT}/usr/src/linux/include/uapi/linux/connector.h)" ]; then
#		## old path: ${ROOT}/usr/$(get_libdir)/klibc/include/linux/connector.h)
#		eerror "You need to compile klibc against a kernel tree patched with uvesafb"
#		eerror "prior to merging this package."
#		die "Kernel not patched with uvesafb."
#	fi

	epatch "${FILESDIR}"/01_use-external-libx86.patch \
		"${FILESDIR}"/02_dont-include-kernel.patch \
		"${FILESDIR}"/v86d-9999-add-atomic_t.patch

	default_src_prepare
}

src_configure() {
	tc-export CC LD AS AR
	./configure --default $(use_with debug) $(use_with x86emu) || die
}

src_compile() {
	# Disable stack protector, as it does not work with klibc (bug #346397).
	filter-flags -fstack-protector -fstack-protector-all
	emake KDIR="${EROOT}"/usr || die
}

src_install() {
	emake DESTDIR="${D}" install || die

	dodoc README ChangeLog

	insinto /usr/share/${PN}
	doins misc/initramfs
}

pkg_postinst() {
	elog "If you wish to place v86d into an initramfs image, you might want to use"
	elog "'/usr/share/${PN}/initramfs' in your kernel's CONFIG_INITRAMFS_SOURCE."
}
