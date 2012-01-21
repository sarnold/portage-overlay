# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2
inherit eutils autotools

DESCRIPTION="General purpose library and file format for storing scientific data"
HOMEPAGE="http://www.hdfgroup.org/HDF5/"
SRC_URI="http://www.hdfgroup.org/ftp/HDF5/current/src/${P}.tar.gz"

LICENSE="NCSA-HDF"
SLOT="0"
KEYWORDS="~amd64 ~hppa ~ppc ~ppc64 ~x86 ~sparc"

IUSE="cxx examples fortran mpi static szip threads zlib"

RDEPEND="mpi? ( || (
			sys-cluster/openmpi[romio]
			sys-cluster/mpich2[romio]
			>=sys-cluster/lam-mpi-7.1.4[romio] ) )
	szip? ( >=sci-libs/szip-2.1 )
	zlib? ( sys-libs/zlib )"

DEPEND="${RDEPEND}
	>=sys-devel/libtool-2.2
	sys-process/time"

pkg_setup() {
	if use mpi && use cxx; then
		ewarn "Simultaneous mpi and cxx is not supported by ${PN}"
		ewarn "Will disable cxx interface"
	fi
	if use mpi && use fortran; then
		export FC=mpif90
	fi
}

src_prepare() {
	epatch "${FILESDIR}"/${P}-as-needed.patch
	epatch "${FILESDIR}"/${P}-includes.patch
	epatch "${FILESDIR}"/${P}-gnutools.patch
	epatch "${FILESDIR}"/${P}-noreturn.patch
	epatch "${FILESDIR}"/${P}-destdir.patch
	epatch "${FILESDIR}"/${P}-signal.patch

	# gentoo examples directory
	sed -i \
		-e 's:$(docdir)/hdf5:$(docdir):' \
		$(find . -name Makefile.am) || die
	eautoreconf
	# enable shared libs by default for h5cc config utility
	sed -i -e "s/SHLIB:-no/SHLIB:-yes/g" tools/misc/h5cc.in \
		|| die "sed h5cc.in failed"

	# fix QA warnings (implicit declaration) on test tools
	sed -i -e "s:unistd.h:getopt.h:" \
		perform/perf.c \
		testpar/t_posix_compliant.c \
		|| die
}

src_configure() {
	# threadsafe incompatible with many options
	local myconf="--disable-threadsafe"
	use threads && ! use fortran && ! use cxx && ! use mpi \
		&& myconf="--enable-threadsafe"

	if use mpi && use cxx; then
		myconf="${myconf} --disable-cxx"
	elif use cxx; then
		myconf="${myconf} --enable-cxx"
	fi

	# Shared libs should be the default, as the configure --help says, but
	# without --enable-shared, the lib*.so shared libs are not installed.
	# However, if they aren't installed, then the *.a libs need -fPIC.
	if use static; then
		myconf="${myconf} --with-pic"
	else
		myconf="${myconf} --enable-shared"
	fi

	econf \
		--docdir=/usr/share/doc/${PF} \
		--disable-sharedlib-rpath \
		--enable-production \
		--enable-strict-format-checks \
		--enable-deprecated-symbols \
		$(use_enable fortran) \
		$(use_enable mpi parallel) \
		$(use_with szip szlib) \
		$(use_with threads pthread) \
		$(use_with zlib) \
		${myconf}
}

src_test() {
	# all tests pass; a few are skipped, and MPI skips parts if it sees
	# only one process on the build host.
	export HDF5_Make_Ignore=yes
	if use mpi ; then
	    EBUILD_CC="${CC}"
	    export HDF5_PARAPREFIX="${S}/testpar"
	    export CC="$(type -p mpicc)"
	    export MPI_UNIVERSE="localhost 5"
	    # certain tests need at least 4 processes or they get skipped	
	    export NPROCS=4
	    install -g portage -o portage -m 0600 "${FILESDIR}"/mpd.conf "${HOME}"/.mpd.conf
	    mpd --daemon --listenport=4268
	    mpd --daemon -h localhost -p 4268 -n
	    mpd --daemon -h localhost -p 4268 -n
	    mpd --daemon -h localhost -p 4268 -n
	    elog "NPROCS = ${NPROCS}"
	    elog "mpdtrace output:"
	    mpdtrace
	fi
	make check || die "make test failed"
	use mpi && mpdallexit
	use mpi && CC="${EBUILD_CC}"
	export HDF5_Make_Ignore=no
}

src_install() {
	emake DESTDIR="${D}" install || die "emake install failed"
	dodoc README.txt
	if use examples; then
		emake -j1 DESTDIR="${D}" install-examples \
			|| die "emake install examples failed"
	fi
}
