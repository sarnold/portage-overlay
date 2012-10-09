# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils toolchain-funcs

DESCRIPTION="A minimalistic C client library for the Redis database."
HOMEPAGE="https://github.com/antirez/hiredis"
SRC_URI="mirror://gentoo/${P}.tar.gz"
#EGIT_REPO_URI="git://github.com/antirez/${PN}.git"

LICENSE="BSD"
KEYWORDS="amd64 arm ppc x86"
IUSE=""
SLOT="0"

DEPEND="dev-libs/libevent
	dev-db/redis"

RDEPEND="${DEPEND}"

DOCS="README.md CHANGELOG.md"

src_compile() {
	emake CC="$(tc-getCC)" OPTIMIZATION="" all || die "make failed"
}

src_test() {
	cd ${S}
	/usr/sbin/redis-server ${FILESDIR}/redis.conf
	./hiredis-test -h 127.0.0.1 -p 56379 -s /tmp/hiredis-test-redis.sock \
		|| ( kill `cat /tmp/hiredis-test-redis.pid` && false )
	kill `cat /tmp/hiredis-test-redis.pid`
}

src_install() {
	dobin hiredis-example hiredis-test
	dolib.so libhiredis.so
	dolib.a libhiredis.a
	insinto /usr/include/${PN}
	doins hiredis.h async.h 
	doins -r adapters

	pushd ${D}usr/$(get_libdir) > /dev/null
		ln -s libhiredis.so libhiredis.so.0
		ln -s libhiredis.so libhiredis.so.0.10
	popd > /dev/null

	dodoc ${DOCS}
}

