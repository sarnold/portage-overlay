# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI=5
PYTHON_COMPAT=( python2_7 )

inherit distutils-r1

MY_PV="1.2.1+17.04.20161116.3"

DESCRIPTION="Scripts to work with Phablet. Installs Touch Developer Preview on Nexus devices"
HOMEPAGE="https://launchpad.net/phablet-tools"
SRC_URI="https://launchpad.net/ubuntu/+archive/primary/+files/${PN}_${MY_PV}.orig.tar.gz"

LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE=""

RDEPEND="dev-python/pep8[${PYTHON_USEDEP}]
	dev-python/pyflakes[${PYTHON_USEDEP}]
	dev-python/configobj[${PYTHON_USEDEP}]
	dev-python/requests[${PYTHON_USEDEP}]
	dev-python/pylzma[${PYTHON_USEDEP}]
	dev-python/mock[${PYTHON_USEDEP}]
	dev-python/requests[${PYTHON_USEDEP}]
	dev-python/testtools[${PYTHON_USEDEP}]
	dev-python/testscenarios[${PYTHON_USEDEP}]
	dev-python/pyxdg[${PYTHON_USEDEP}]
	dev-util/android-tools"

S="${WORKDIR}"


src_prepare() {
	distutils-r1_src_prepare
	sed -i \
		-e "s/'repo',//" \
		-e "s/'phablet-dev-bootstrap',//" \
		setup.py || die "error excluding dev tools"
}
