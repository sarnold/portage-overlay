# Copyright 1999-2018 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=5

PYTHON_COMPAT=( python2_7 )
DISTUTILS_OPTIONAL=1

inherit autotools distutils-r1 eutils flag-o-matic multilib systemd

DESCRIPTION="A scalable distributed monitoring system for clusters and grids"
HOMEPAGE="http://ganglia.sourceforge.net/"
SRC_URI="https://github.com/ganglia/monitor-core/archive/${PV}.tar.gz -> ${P}.tar.gz"
LICENSE="BSD"

SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~ppc ~x86"
IUSE="minimal pcre python examples"

DEPEND="dev-libs/confuse:=
	dev-libs/expat
	>=dev-libs/apr-1.0
	!dev-db/firebird
	net-libs/libtirpc:=
	>=net-libs/rpcsvc-proto-1.3
	pcre? ( dev-libs/libpcre )
	python? ( ${PYTHON_DEPS} )"

RDEPEND="
	${DEPEND}
	!minimal? ( net-analyzer/rrdtool )"

REQUIRED_USE="python? ( ${PYTHON_REQUIRED_USE} )"

S="${WORKDIR}/monitor-core-${PV}"

src_prepare() {
	eautoreconf

	if use python && ! use minimal; then
		pushd gmetad-python >/dev/null || die
		distutils-r1_src_prepare
		popd >/dev/null || die
	fi
}

src_configure() {
	if use python; then
		python_setup
	fi

	append-libs -ltirpc
	append-cppflags -I/usr/include/tirpc
	econf \
		--with-systemdsystemunitdir=$(systemd_get_unitdir) \
		--enable-gexec \
		--sysconfdir="${EPREFIX}"/etc/${PN} \
		--enable-static=no \
		$(use_enable python) \
		$(use_with pcre libpcre) \
		$(use_with !minimal gmetad)
}

src_compile() {
	default_src_compile

	if use python && ! use minimal; then
		pushd gmetad-python >/dev/null || die
		distutils-r1_src_compile
		popd >/dev/null || die
	fi
}

src_install() {
	local exdir=/usr/share/doc/${P}

	emake DESTDIR="${D}" install || die

	newinitd "${FILESDIR}"/gmond.rc-2 gmond
	doman {mans/*.1,gmond/*.5} || die "Failed to install manpages"
	dodoc AUTHORS INSTALL NEWS || die

	dodir /etc/ganglia/conf.d
	use python && dodir /usr/$(get_libdir)/ganglia/python_modules
	gmond/gmond -t > "${ED}"/etc/ganglia/gmond.conf

	# add example for gmetric (assumes orchardos for some metrics)
	dobin "${FILESDIR}"/string-metrics.sh \
		"${FILESDIR}"/canary-status.sh \
		"${FILESDIR}"/canary-switch.sh \
		"${FILESDIR}"/lp-device-check.sh \
		"${FILESDIR}"/tripos-testmode.sh

	insinto /etc/cron.d
	newins "${FILESDIR}"/gmetrics.cron.d gmetrics

	if use examples; then
		insinto ${exdir}/cmod-examples
		doins gmond/modules/example/*.c
		if use python; then
			# Installing as an examples per upstream.
			insinto ${exdir}/pymod-examples
			doins gmond/python_modules/*/*.py
			insinto ${exdir}/pymod-examples/conf.d
			doins gmond/python_modules/conf.d/*.pyconf
		fi
	fi

	if ! use minimal; then
		insinto /etc/ganglia
		doins gmetad/gmetad.conf
		doman mans/gmetad.1

		newinitd "${FILESDIR}"/gmetad.rc-2 gmetad
		keepdir /var/lib/ganglia/rrds
		fowners nobody:nobody /var/lib/ganglia/rrds

		if use python; then
			pushd gmetad-python >/dev/null || die
			distutils-r1_src_install
			popd >/dev/null || die
			newinitd "${FILESDIR}"/gmetad-python.rc gmetad-python
		fi
	fi
}

src_test() {
	default_src_test

	if use python && ! use minimal; then
		pushd gmetad-python >/dev/null || die
		distutils-r1_src_test
		popd >/dev/null || die
	fi
}

pkg_postinst() {
	elog "A default configuration file for gmond has been generated"
	elog "for you as a template by running:"
	elog "    /usr/sbin/gmond -t > /etc/ganglia/gmond.conf"

	elog "The web frontend for Ganglia has been split off.  Emerge"
	elog "sys-cluster/ganglia-web if you need it."
}
