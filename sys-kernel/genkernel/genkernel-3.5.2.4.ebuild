# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

# genkernel-9999        -> latest Git branch "master"
# genkernel-VERSION     -> normal genkernel release

EAPI=5 # approved 2012.09.11, required by all profiles since 2014.03.12

VERSION_BUSYBOX='1.27.2' # warning, be sure to bump patches
VERSION_DMRAID='1.0.0.rc16-3' # warning, be sure to bump patches
VERSION_MDADM='4.0' # warning, be sure to bump patches
VERSION_FUSE='2.8.6' # warning, be sure to bump patches
VERSION_ISCSI='2.0-872' # warning, be sure to bump patches
VERSION_LVM='2.02.173' # warning, be sure to bump patches
VERSION_UNIONFS_FUSE='0.24'
VERSION_GPG='1.4.22'

RH_HOME="ftp://sourceware.org/pub"
DM_HOME="https://people.redhat.com/~heinzm/sw/dmraid/src"
BB_HOME="https://busybox.net/downloads"

COMMON_URI="${DM_HOME}/dmraid-${VERSION_DMRAID}.tar.bz2
		${DM_HOME}/old/dmraid-${VERSION_DMRAID}.tar.bz2
		mirror://kernel/linux/utils/raid/mdadm/mdadm-${VERSION_MDADM}.tar.xz
		${RH_HOME}/lvm2/LVM2.${VERSION_LVM}.tgz
		${RH_HOME}/lvm2/old/LVM2.${VERSION_LVM}.tgz
		${BB_HOME}/busybox-${VERSION_BUSYBOX}.tar.bz2
		http://www.open-iscsi.org/bits/open-iscsi-${VERSION_ISCSI}.tar.gz
		mirror://sourceforge/fuse/fuse-${VERSION_FUSE}.tar.gz
		http://podgorny.cz/unionfs-fuse/releases/unionfs-fuse-${VERSION_UNIONFS_FUSE}.tar.bz2
		mirror://gnupg/gnupg/gnupg-${VERSION_GPG}.tar.bz2"

if [[ ${PV} == 9999* ]]
then
	EGIT_REPO_URI="git://anongit.gentoo.org/proj/${PN}.git
		https://anongit.gentoo.org/git/proj/${PN}.git"
	inherit git-2 bash-completion-r1 eutils
	S="${WORKDIR}/${PN}"
	SRC_URI="${COMMON_URI}"
else
	inherit bash-completion-r1 eutils
	SRC_URI="mirror://gentoo/${P}.tar.xz
		${COMMON_URI}"
	KEYWORDS="~alpha ~amd64 ~arm ~hppa ~ia64 ~mips ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86"
fi

DESCRIPTION="Gentoo automatic kernel building scripts"
HOMEPAGE="https://www.gentoo.org"

LICENSE="GPL-2"
SLOT="0"
RESTRICT=""
IUSE="cryptsetup ibm +firmware +premount selinux"

DEPEND="sys-fs/e2fsprogs
	premount? ( sys-fs/jfsutils
		sys-apps/coreutils
		)
	selinux? ( sys-libs/libselinux )"
RDEPEND="${DEPEND}
	cryptsetup? ( sys-fs/cryptsetup )
	app-arch/cpio
	>=app-misc/pax-utils-1.2.2
	sys-apps/util-linux[static-libs(+)]
	firmware? ( sys-kernel/linux-firmware )
	!<sys-apps/openrc-0.9.9"
# pax-utils is used for lddtree

if [[ ${PV} == 9999* ]]; then
	DEPEND="${DEPEND} app-text/asciidoc"
fi

OVERLAY_PATH="usr/share/genkernel/overlay"
QA_PRESTRIPPED="
	${OVERLAY_PATH}/sbin/.*
	${OVERLAY_PATH}/$(get_libdir)/.*
	${OVERLAY_PATH}/usr/bin/.*
"

pkg_pretend() {
	if ! use cryptsetup && has_version "sys-kernel/genkernel[crypt]"; then
		ewarn "Local use flag 'crypt' has been renamed to 'cryptsetup' (bug #414523)."
		ewarn "Please set flag 'cryptsetup' for this very package if you would like"
		ewarn "to have genkernel create an initramfs with LUKS support."
		ewarn "Sorry for the inconvenience."
		echo
	fi
}

src_unpack() {
	if [[ ${PV} == 9999* ]] ; then
		git-2_src_unpack
	else
		unpack ${P}.tar.xz
	fi
}

src_prepare() {
	if [[ ${PV} == 9999* ]] ; then
		einfo "Updating version tag"
		GK_V="$(git describe --tags | sed 's:^v::')-git"
		sed "/^GK_V/s,=.*,='${GK_V}',g" -i "${S}"/genkernel
		einfo "Producing ChangeLog from Git history..."
		pushd "${S}/.git" >/dev/null || die
		git log > "${S}"/ChangeLog || die
		popd >/dev/null || die
	fi
	if use selinux ; then
		sed -i 's/###//g' "${S}"/gen_compile.sh || die
	fi

	# Update software.sh
	sed -i \
		-e "s:VERSION_BUSYBOX:$VERSION_BUSYBOX:" \
		-e "s:VERSION_MDADM:$VERSION_MDADM:" \
		-e "s:VERSION_DMRAID:$VERSION_DMRAID:" \
		-e "s:VERSION_FUSE:$VERSION_FUSE:" \
		-e "s:VERSION_ISCSI:$VERSION_ISCSI:" \
		-e "s:VERSION_LVM:$VERSION_LVM:" \
		-e "s:VERSION_UNIONFS_FUSE:$VERSION_UNIONFS_FUSE:" \
		-e "s:VERSION_GPG:$VERSION_GPG:" \
		"${S}"/defaults/software.sh \
		|| die "Could not adjust versions"

	if use premount ; then
		epatch "${FILESDIR}"/${PN}-add-fsck-premount.patch
		install "${FILESDIR}"/libs_list "${WORKDIR}"
		sed -i -e "s|lib64|$(get_libdir)|" \
			"${WORKDIR}"/libs_list
		## FIXME
		use amd64 || sed -i -e "s|-x86-64||" \
			"${WORKDIR}"/libs_list
	fi

	epatch_user
}

src_compile() {
	if [[ ${PV} == 9999* ]]; then
		emake
	fi
}

src_install() {
	insinto /etc

	use premount && gen_files
	elog "QA_PRESTRIPPED list:"
	elog "${QA_PRESTRIPPED}"

	doins "${S}"/genkernel.conf

	doman genkernel.8
	dodoc AUTHORS ChangeLog README TODO
	dobin genkernel
	rm -f genkernel genkernel.8 AUTHORS ChangeLog README TODO genkernel.conf

	if use ibm ; then
		cp "${S}"/arch/ppc64/kernel-2.6{-pSeries,} || die
	else
		cp "${S}"/arch/ppc64/kernel-2.6{.g5,} || die
	fi
	insinto /usr/share/genkernel
	doins -r "${S}"/*

	newbashcomp "${FILESDIR}"/genkernel.bash "${PN}"
	insinto /etc
	doins "${FILESDIR}"/initramfs.mounts

	cd "${DISTDIR}"
	insinto /usr/share/genkernel/distfiles
	doins ${A/${P}.tar.xz/}
}

pkg_postinst() {
	echo
	elog 'Documentation is available in the genkernel manual page'
	elog 'as well as the following URL:'
	echo
	elog 'https://wiki.gentoo.org/wiki/Genkernel'
	echo
	ewarn "This package is known to not work with reiser4.  If you are running"
	ewarn "reiser4 and have a problem, do not file a bug.  We know it does not"
	ewarn "work and we don't plan on fixing it since reiser4 is the one that is"
	ewarn "broken in this regard.  Try using a sane filesystem like ext4."
	echo
	ewarn "The LUKS support has changed from versions prior to 3.4.4.  Now,"
	ewarn "you use crypt_root=/dev/blah instead of real_root=luks:/dev/blah."
	echo

	if use premount ; then
		elog ""
		ewarn "For USE=premount to run fsck early on separate /usr:"
		ewarn "Please add awk to the list of BUSYBOX_APPLETS in genkernel.conf."
		ewarn ""
		ewarn "And don't forget to enable the overlay in genkernel.conf."
		ewarn "An initial overlay with ext and jfs support has been"
		ewarn "created for you in /usr/share/genkernel/overlay."
		elog ""
	fi
 }

gen_files() {
	# generate overlay files for premount fsck support
	overlay="${ED}${OVERLAY_PATH}"
	mkdir -p $overlay/etc
	mkdir -p $overlay/sbin
	mkdir -p $overlay/$(get_libdir)
	mkdir -p $overlay/usr/bin

	pushd $overlay > /dev/null
		cp ${FILESDIR}/initrd.fsck $overlay/etc
		cat ${WORKDIR}/libs_list | xargs cp -t $overlay/$(get_libdir)
		cat ${FILESDIR}/sbin_list | xargs cp -t $overlay/sbin
		cat ${FILESDIR}/bin_list | xargs cp -t $overlay/usr/bin
	popd > /dev/null
}
