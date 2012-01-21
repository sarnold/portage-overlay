# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=2

MY_PV=${PV/_/-}
K_NOSETEXTRAVERSION="yes"
K_SECURITY_UNSUPPORTED="1"
ETYPE="sources"
inherit kernel-2
detect_version

# set to either test or release; check URI below if working with an rc kernel
BRANCH="test"
# release date sometimes gets removed once kernels go from _rc to official
RELEASE_DATE="20091013"

# modified for _rc releases
APV=${RELEASE_DATE}-${MY_PV}
MY_OKV="${KV_MAJOR}.${KV_MINOR}.${KV_PATCH}"
APV_URI="http://ftp.kernel.org/pub/linux/kernel/people/lenb/acpi/patches/${MY_OKV}/acpi-${BRANCH}-${APV}.diff.bz2
	http://ftp.kernel.org/pub/linux/kernel/people/lenb/acpi/patches/README.ACPI"
DSDT_URI="http://gaugusch.at/acpi-dsdt-initrd-patches/acpi-dsdt-initrd-v0.9d-2.6.30-20090730+log.patch"

DESCRIPTION="ACPI-patched sources (${BRANCH} branch) for the vanilla ${KV_MAJOR}.${KV_MINOR} kernel tree"
HOMEPAGE="http://www.lesswatts.org/projects/acpi/
	http://gaugusch.at/kernel.shtml"
SRC_URI="${KERNEL_URI} ${APV_URI} custom_DSDT? ( ${DSDT_URI} )"

KEYWORDS="~amd64 ~x86"
IUSE="c7 +custom_DSDT"

EPATCH_OPTS="-Np1 -F 3"
K_EXTRAEINFO="This kernel is not officially supported by Gentoo, however, it
should be fairly stable since it's the vanilla kernel source with the latest
ACPI release for that kernel version (the vanilla kernel is a little behind).
If you have a modern laptop or desktop and are having trouble with system
initialization, power management, or setting the CPU frequency, then these
patches may help.  You should also make sure you have the latest BIOS update
from your motherboard or system vendor."

src_prepare() {
#	$(bzcat "${DISTDIR}"/acpi-${BRANCH}-${APV}.diff.bz2 > acpi-updated.diff)
	# delete the failing thinkpad patch
#	sed -i '169,182d' acpi-updated.diff
#	epatch acpi-updated.diff
	epatch "${DISTDIR}"/acpi-${BRANCH}-${APV}.diff.bz2
	use custom_DSDT && epatch \
	    "${DISTDIR}"/acpi-dsdt-initrd-v0.9d-2.6.30-20090730+log.patch
	use c7 && epatch "${FILESDIR}"/c7temp.patch
}

src_install() {
	kernel-2_src_install
	dodoc "${DISTDIR}"/README.ACPI
}
