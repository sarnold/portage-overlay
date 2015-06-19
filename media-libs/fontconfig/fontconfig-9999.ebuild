# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=5
AUTOTOOLS_AUTORECONF=yes

inherit autotools-multilib eutils libtool toolchain-funcs flag-o-matic

if [[ ${PV} == *9999* ]]; then
	inherit git-r3
	EGIT_REPO_URI="https://github.com/sarnold/fontconfig.git"
	SRC_URI=""
else
	# last release is 10.0.1
	SRC_URI="https://bitbucket.org/chemoelectric/${PN}/get/release-${PV}.tar.gz -> ${P}.tar.gz"
	KEYWORDS="~amd64 ~arm ~ppc ~x86"
fi

DESCRIPTION="nerdboy fork of Crud Factory fontconfig: a fork of fontconfig"
HOMEPAGE="https://bitbucket.org/chemoelectric/fontconfig"
SRC_URI=""

LICENSE="MIT"
SLOT="1.0"

IUSE="doc static-libs"

RDEPEND="
	>=media-libs/freetype-2.2.1[${MULTILIB_USEDEP}]
	>=dev-libs/expat-1.95.3[${MULTILIB_USEDEP}]
	abi_x86_32? ( !app-emulation/emul-linux-x86-xlibs[-abi_x86_32(-)] )
"
DEPEND="
	${RDEPEND}
	virtual/pkgconfig
	doc? (
		app-text/docbook-sgml-utils[jadetex]
		=app-text/docbook-sgml-dtd-3.1*
	)
"
PDEPEND="
	app-eselect/eselect-fontconfig
	virtual/ttf-fonts
"

src_prepare() {
	/bin/sh autogen.sh --noconf || die "autogen.sh failed"

	epatch "${FILESDIR}"/${PN}-2.7.1-latin-reorder.patch	# 130466
	epatch "${FILESDIR}"/${PN}-2.3.2-docbook.patch			# 310157
	epatch "${FILESDIR}"/${PN}-2.8.0-urw-aliases.patch		# 303591

	mkdir -p m4
	eautoreconf --install

	# Needed to get a sane .so versioning on fbsd, please dont drop
	# If you have to run eautoreconf, you can also leave the elibtoolize call as
	# it will be a no-op.
	elibtoolize
}

src_configure() {
	local myeconfargs=(
		#$(use_enable doc docbook)
		# always enable docs to install manpages
		#--enable-docs
		--localstatedir="${EPREFIX}"/var
		--with-default-fonts="${EPREFIX}"/usr/share/fonts
		--with-add-fonts="${EPREFIX}"/usr/local/share/fonts
	)

	autotools-multilib_src_configure
}

src_install() {
	autotools-multilib_src_install

	# XXX: avoid calling this multiple times, bug #459210
	install_others() {
		# stuff installed from build-dir

		#autotools-utils_src_compile \          <-- manpages currently are not supported.
		#	DESTDIR="${D}" -C doc install-man

		insinto /etc/fonts
		doins "${BUILD_DIR}"/fonts.conf
	}
	multilib_foreach_abi install_others

	# Currently manpages are not implemented.
	#
	#autotools-utils_src_compile DESTDIR="${D}" -C doc install-man

	#fc-lang directory contains language coverage datafiles
	#which are needed to test the coverage of fonts.
	insinto /usr/share/fc-lang
	doins fc-lang/*.orth

	for i in AUTHORS ChangeLog README doc/fontconfig-user.{txt,pdf}; do
		test -f "${i}" && dodoc "${i}"
	done

	if [[ -e ${ED}usr/share/doc/fontconfig/ ]];  then
		mv "${ED}"usr/share/doc/fontconfig/* "${ED}"/usr/share/doc/${P}
		rm -rf "${ED}"usr/share/doc/fontconfig
	fi

	# Changes should be made to /etc/fonts/local.conf, and as we had
	# too much problems with broken fonts.conf, we force update it ...
	# <azarah@gentoo.org> (11 Dec 2002)
	echo 'CONFIG_PROTECT_MASK="/etc/fonts/fonts.conf"' > "${T}"/37fontconfig
	doenvd "${T}"/37fontconfig

	# As of fontconfig 2.7, everything sticks their noses in here.
	dodir /etc/sandbox.d
	echo 'SANDBOX_PREDICT="/var/cache/fontconfig"' > "${ED}"/etc/sandbox.d/37fontconfig
}

pkg_preinst() {
	# Bug #193476
	# /etc/fonts/conf.d/ contains symlinks to ../conf.avail/ to include various
	# config files.  If we install as-is, we'll blow away user settings.
	ebegin "Syncing fontconfig configuration to system"
	if [[ -e ${EROOT}/etc/fonts/conf.d ]]; then
		for file in "${EROOT}"/etc/fonts/conf.avail/*; do
			f=${file##*/}
			if [[ -L ${EROOT}/etc/fonts/conf.d/${f} ]]; then
				[[ -f ${ED}etc/fonts/conf.avail/${f} ]] \
					&& ln -sf ../conf.avail/"${f}" "${ED}"etc/fonts/conf.d/ &>/dev/null
			else
				[[ -f ${ED}etc/fonts/conf.avail/${f} ]] \
					&& rm "${D}"etc/fonts/conf.d/"${f}" &>/dev/null
			fi
		done
	fi
	eend $?
}

pkg_postinst() {
	einfo "Cleaning broken symlinks in "${EROOT}"etc/fonts/conf.d/"
	find -L "${EROOT}"etc/fonts/conf.d/ -type l -delete

	echo
	ewarn "Please make fontconfig configuration changes using \`eselect fontconfig\`"
	ewarn "Any changes made to /etc/fonts/fonts.conf will be overwritten."
	ewarn
	ewarn "If you need to reset your configuration to upstream defaults, delete"
	ewarn "the directory ${EROOT}etc/fonts/conf.d/ and re-emerge fontconfig."
	echo

	if [[ ${EROOT} = / ]]; then
		ebegin "Creating global font cache"
		/usr/bin/fc-cache -srf
		eend $?
	fi
}
