# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

DESCRIPTION="Virtual for selecting an appropriate Ada compiler"
HOMEPAGE=""
SRC_URI=""
LICENSE=""
SLOT="2012"
KEYWORDS="~amd64 ~arm ~x86"
IUSE=""

# Only one at present, but gnat-gcc-5.x is coming soon (I Swear)
RDEPEND="|| (
	>=sys-devel/gcc-6.3.0[ada]
	>=dev-lang/gnat-gpl-2017 )"
DEPEND=""
