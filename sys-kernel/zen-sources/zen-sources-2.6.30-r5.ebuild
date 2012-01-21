# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

COMPRESSTYPE=".lzma"
K_PREPATCHED="yes"
UNIPATCH_STRICTORDER="yes"
K_SECURITY_UNSUPPORTED="1"
ZGR_PATCH="grsecurity_2.1.14-2.6.30.5-200908281917-for-zen-2.6.30-zen4.patch.bz2"

RESTRICT="binchecks strip primaryuri mirror"

ETYPE="sources"
inherit kernel-2
detect_version
K_NOSETEXTRAVERSION="don't_set_it"

DESCRIPTION="Hardened-enabled Zen-Sources kernel patchset."
HOMEPAGE="http://zen-sources.org
	http://forums.gentoo.org/viewtopic-t-790084.html?sid=8420cdf0eac966d159baac2d77578910"

ZEN_URI="http://zen-sources.org/files/${KV_FULL}.patch${COMPRESSTYPE}"
ZGR_URI="http://www.gentoogeek.org/files/${ZGR_PATCH}"
SRC_URI="${KERNEL_URI} ${ZEN_URI} ${ZGR_URI}"

KEYWORDS="-* ~amd64 ~ppc ~ppc64 ~x86"
IUSE="hardened"

EPATCH_OPTS="-F 3"
K_EXTRAEINFO="For more info on zen-sources, and for how to report problems, see: \
${HOMEPAGE}, also go to #zen-sources on freenode.  The Zen grsec patch provided 
here simply has a renamed extension from the one posted in the forum thread."

src_unpack(){
	kernel-2_src_unpack
	cd ${S}
	epatch ${DISTDIR}/${KV_FULL}.patch${COMPRESSTYPE}
	use hardened && epatch "${DISTDIR}/${ZGR_PATCH}"
}
