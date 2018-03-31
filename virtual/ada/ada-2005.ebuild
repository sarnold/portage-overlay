# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI="5"

DESCRIPTION="Virtual for selecting an appropriate Ada compiler"
SLOT="2005"
KEYWORDS="amd64 x86"

# Only one at present, but gnat-gcc-4.3 is coming soon too
RDEPEND="|| (
	>=sys-devel/gcc-5.4.0[ada]
	>=dev-lang/gnat-gpl-2016 )"
