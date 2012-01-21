# Copyright 1999-2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header$

# Package doesn't use distutils
inherit python

DESCRIPTION="This program allows you to view and manipulate data on LG VX4400/VX6000 and many Sanyo Sprint mobile phones"
HOMEPAGE="http://www.bitpim.org/"
SRC_URI=""
LICENSE="GPL-2"

# Source is distributed only by CVS
# We will check out a particular revision
ECVS_AUTH="pserver"
ECVS_SERVER="cvs.sourceforge.net:/cvsroot/${PN}"
ECVS_MODULE="${PN}"
ECVS_BRANCH="BITPIM_${PV//./_}"
ECVS_USER="anonymous"
ECVS_PASS=""
ECVS_CVS_OPTIONS="-dP"

inherit cvs

SLOT="0"
KEYWORDS="~x86"
IUSE="crypt usb evo"

# Exact dep for wxpython ok since they've moved onto 2.5.x
DEPEND=">=dev-lang/python-2.3
		=dev-python/wxpython-2.4.2.4
		dev-python/pyserial
		dev-python/dsv
		crypt? ( dev-python/paramiko )
		usb? ( >=dev-lang/swig-1.3.19 dev-libs/libusb sys-devel/gcc )"

S=${WORKDIR}/${ECVS_MODULE}

src_compile() {
	# USB stuff
	if [ `use usb` ]; then
		cd native/usb
		sh ./build.sh
	fi

	# Everything else is pure Python

}

# To copy a whole directory; where is this in Portage lib?
docpr() {
	[ ! -d $D/$INSDESTTREE ] && install -d $D/$INSDESTTREE
	for dir in $@; do
		cp -rv $dir ${D}/$INSDESTTREE
		# delete CVS cruft
		cruft=$(find $dir -name CVS -type d)
		rm -rfv $cruft
	done
}

# Default source install is for static release, so we do
# everything ourselves
src_install() {
	# Enter source dir
	cd ${S}

	# Install files into right place
	#
	# BitPim is a self-contained app, so jamming it into 
	# Python's site-packages might not be worthwhile.  We'll
	# Put it in its own home, and add the PYTHONPATH in the 
	# wrapper executables below.
	distutils_python_version
	export RLOC=/usr/lib/${PF}  # export for use later
	insinto $RLOC
	
	# Main Python source
	doins *.py 
	docpr ./resources ./help
	
	# Native products
	insinto $RLOC/native
	doins ./native/*.py
	docpr native/qtopiadesktop
	[ `use evo` ] && docpr native/evolution 

	# Bitfling
	if [ `use crypt` ]; then
		FLINGDIR="${RLOC}/bitfling"
		insinto $FLINGDIR
		cd bitfling
		doins *.py
		# "paramiko" is now external, but code still wants "paramiko_bp"
		# necessitating an ugly hack
		# First get site-packages
		SPATH=`python -c "import sys, re; paths=sys.path; spath=(filter(lambda a: re.search(\"site-packages$\", a), paths)); print spath.pop()"`
		dosym $SPATH/paramiko ${RLOC}/bitfling/paramiko_bp
		cd ${S}
	fi
	
	# NOTE: docs are old, so skipping them
	
	# Creating scripts
	echo "#!/bin/sh" >> ${T}/bitpim
	echo "export PYTHONPATH=\"$RLOC:$PYTHONPATH\""
	echo "exec python ${RLOC}/bp.py bitpim" >> ${T}/bitpim
	dobin ${T}/bitpim
	if [ `use crypt` ]; then
		echo "#!/bin/sh" >> ${T}/bitfling
		echo "export PYTHONPATH=\"$RLOC:$PYTHONPATH\""
		echo "exec python ${RLOC}/bp.py bitfling" >> ${T}/bitfling
		dobin ${T}/bitfling
	fi

}

pkg_postinst() {
	# Optimize in installed directory
	python_mod_optimize ${ROOT}/${RLOC}

	# Helpful message re. support
	einfo "For support information please visit http://bitpim.org/"
}

