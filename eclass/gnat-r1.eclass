# Copyright 1999-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$
#
# Author: George Shapovalov <george@gentoo.org>
# Author: Steve Arnold <nerdboy@gentoo.org>
# Belongs to: ada project <ada@gentoo.org>
#
# This eclass simplifies Ada package installation, and also changes the
# way non-gnat inlcudes and object files are handled.  Instead of the old
# way, we use library.gpr (project) files and a modified GNU/Debian policy.
# ...

inherit eutils flag-o-matic multilib

# The environment is set locally in src_compile and src_install functions
# by the common code sourced here and in gnat-eselect module.
# This is the standard location for this code (belongs to eselect-gnat,
# since eselect should work even in the absense of portage tree and we can
# guarantee to some extent presence of gnat-eselect when anything gnat-related
# gets processed. See #192505)
#
# Note!
# It may not be safe to source this at top level. Only source inside local
# functions!
GnatCommon="/usr/share/gnat/lib/gnat-common.bash"

EXPORT_FUNCTIONS pkg_setup pkg_postinst src_compile

DESCRIPTION="Updated common procedures for building Ada libs using active profile"

# make sure we have an appropriately recent eselect-gnat installed, as we are
# using some common code here.
DEPEND=">=app-eselect/eselect-gnat-1.5"

# ----------------------------------
# Globals

# Gentoo GNAT/Ada policy draft (install locations, etc)
#
# Gnat package installs are no longer profile dependent; only the active GNAT
# profile is currently supported, so packages will depend on the latest SLOT.
# There is now only one set of install paths and directory locations
# that more-or-less follows the GNU & Debian Ada policies for shared libraries:
#   https://people.debian.org/~lbrenta/debian-ada-policy.html
# 
# Source files SHALL reside in directory $AdalibSpecsDir/<package-name>
#  - merge all source files (specs and bodies) into one directory if possible
#  - provide all required source files, and only source files
# The *.ali files SHALL reside in $AdalibLibTop/<package-name>
#  - *.ali files SHALL have read-only permissions for all users (mode 0444)
# Each library SHALL provide a library project file named <library>.gpr
#  - project files SHALL reside in a configured project search path as
#    shown by gnatls -v
#    - Current project path is /usr/share/gpr
#    - Goal project path is $AdalibSpecsDir (parent of library source dirs)
# Shared/static libraries and binaries SHALL reside in the standard locations

# The library project file SHALL have:
#  - a Source_Dirs attribute containing at least /usr/share/ada/adainclude/<library>
#  - a Library_ALI_Dir equal to /usr/$libdir/ada/adalib/<library>
#  - a Library_Name attribute equal to the library name of the shared library
#  - a Library_Kind attribute equal to ‘dynamic’
#  - a Library_Dir attribute equal to /usr/$libdir
#  - an Externally_Built attribute equal to ‘true’
#  - a Linker_Options section for any library dependencies
# *note: $libdir and linker options should be declared External

# Example:
#  library project <library> is
#     for Library_Name use "<library>";
#     for Library_Dir use "/usr/lib";
#     for Library_Kind use "dynamic";
#     for Source_Dirs use ("/usr/share/ada/adainclude/<library>");
#     for Library_ALI_Dir use "/usr/lib/ada/adalib/<library>";
#     for Externally_Built use "true";
#     package Linker is
#        for Linker_Options use ("-lindirectdependency");
#     end Linker;
#  end <library>;
#
# See ncurses gpr files for real examples

PREFIX=/usr
AdalibSpecsDir=${PREFIX}/share/ada/adainclude
AdalibDataDir=${PREFIX}/share/ada
AdalibLibTop=${PREFIX}/$(get_libdir)/ada/adalib

# current search dirs for gnat projects are not yet configured to spec,
# as shown by 'gnatls -v' below:
# Project Search Path:
#   <Current_Directory>
#   /usr/x86_64-pc-linux-gnu/lib/gnat
#   /usr/x86_64-pc-linux-gnu/share/gpr
#   /usr/share/gpr
#   /usr/lib64/gnat
#
AdalibgprDir=${AdalibDataDir}/../gpr
#	gpr's should go here.

# A simple wrapper to get the relevant part of the DEPEND
# params:
#  $1 - should contain dependency specification analogous to DEPEND,
#       if omitted, DEPEND is processed
get_ada_dep() {
	[[ -z "$1" ]] && DEP="${DEPEND}" || DEP="$1"
	local TempStr
	for fn in $DEP; do # here $DEP should *not* be in ""
		[[ $fn =~ "virtual/ada" ]] && TempStr=${fn/*virtual\//}
		# above match should be to full virtual/ada, as simply "ada" is a common
		# part of ${PN}, even for some packages under dev-ada
	done
#	debug-print-function $FUNCNAME "TempStr=${TempStr:0:8}"
	[[ -n ${TempStr} ]] && echo ${TempStr:0:8}
}

# This function is used to check whether the requested gnat profile matches the
# requested Ada standard
# !!ATTN!!
# This must match dependencies as specified in vitrual/ada !!!
#
# params:
#  $1 - the requested gnat profile in usual form (e.g. x86_64-pc-linux-gnu-gnat-gcc-4.1)
#  $2 - Ada standard specification, as would be specified in DEPEND.
#       Valid  values: ada-1995, ada-2005, ada
#
#       This used to treat ada-1995 and ada alike, but some packages (still
#       requested by users) no longer compile with new compilers (not the
#       standard issue, but rather compiler becoming stricter most of the time).
#       Plus there are some "intermediary versions", not fully 2005 compliant
#       but already causing problems.  Therefore, now we do exact matching.
belongs_to_standard() {
#	debug-print-function $FUNCNAME $*
	. ${GnatCommon} || die "failed to source gnat-common lib"
	local GnatSlot=$(get_gnat_SLOT $1)
	local ReducedSlot=${GnatSlot//\./}
	#
	if [[ $2 == 'ada' ]] ; then
#		debug-print-function "ada or ada-1995 match"
		return 0 # no restrictions imposed
	elif [[ "$2" == 'ada-1995' ]] ; then
		if [[ $(get_gnat_Pkg $1) == "gcc" ]]; then
#			debug-print-function "got gcc profile, GnatSlot=${ReducedSlot}"
			[[ ${ReducedSlot} -le "42" ]] && return 0 || return 1
		elif [[ $(get_gnat_Pkg $1) == "gpl" ]]; then
#			debug-print-function "got gpl profile, GnatSlot=${ReducedSlot}"
			[[ ${ReducedSlot} -lt "41" ]] && return 0 || return 1
		else
			return 1 # unknown compiler encountered
		fi
	elif [[ "$2" == 'ada-2005' ]] ; then
		if [[ $(get_gnat_Pkg $1) == "gcc" ]]; then
#			debug-print-function "got gcc profile, GnatSlot=${ReducedSlot}"
			[[ ${ReducedSlot} -ge "43" ]] && return 0 || return 1
		elif [[ $(get_gnat_Pkg $1) == "gpl" ]]; then
#			debug-print-function "got gpl profile, GnatSlot=${ReducedSlot}"
			[[ ${ReducedSlot} -ge "41" ]] && return 0 || return 1
		else
			return 1 # unknown compiler encountered
		fi
	elif [[ "$2" == 'ada-2012' ]] ; then
		if [[ $(get_gnat_Pkg $1) == "gcc" ]]; then
#			debug-print-function "got gcc profile, GnatSlot=${ReducedSlot}"
			[[ ${ReducedSlot} -ge "49" ]] && return 0 || return 1
		elif [[ $(get_gnat_Pkg $1) == "gpl" ]]; then
#			debug-print-function "got gpl profile, GnatSlot=${ReducedSlot}"
			[[ ${ReducedSlot} -ge "46" ]] && return 0 || return 1
		else
			return 1 # unknown compiler encountered
		fi
	else
		return 1 # unknown standard requested, check spelling!
	fi
}


# ------------------------------------
# Functions

gnat-r1_pkg_setup() {
	debug-print-function $FUNCNAME $*

	# check whether all the primary compilers are installed
	. ${GnatCommon} || die "failed to source gnat-common lib"
	for fn in $(cat ${PRIMELIST}); do
		if [[ ! -f ${SPECSDIR}/${fn} ]]; then
			elog "The ${fn} Ada compiler profile is specified as primary, but is not installed."
			elog "Please rectify the situation before emerging Ada library!"
			elog "Please either install again all the missing compilers listed"
			elog "as primary, or edit /etc/ada/primary_compilers and update the"
			elog "list of primary compilers there."
			einfo ""
			ewarn "If you do the latter, please don't forget to rebuild all"
			ewarn "affected libs!"
			die "Primary compiler is missing"
		fi
	done

	export ADAC=${ADAC:-gnatgcc}
	export ADAMAKE=${ADAMAKE:-gnatmake}
	export ADABIND=${ADABIND:-gnatbind}

	export ADACFLAGS=${ADACFLAGS:-${CFLAGS}}
	export ADALFLAGS=${ADALFLAGS:-${LDFLAGS}}

	if ! multilib_is_native_abi ; then
		export ADACFLAGS="-m32 ${ADACFLAGS}"
		export ADALFLAGS="-m32 ${ADALFLAGS}"
		export ADA_INCLUDE_PATH="/usr/lib64/gnat-gcc/x86_64-pc-linux-gnu/4.9/32/adainclude"
		export ADA_OBJECTS_PATH="/usr/lib64/gnat-gcc/x86_64-pc-linux-gnu/4.9/32/adalib"
#	else
#		export ADA_INCLUDE_PATH="/usr/lib64/gnat-gcc/x86_64-pc-linux-gnu/4.9/adainclude"
#		export ADA_OBJECTS_PATH="/usr/lib64/gnat-gcc/x86_64-pc-linux-gnu/4.9/adalib"
	fi

#	export ADAMAKEFLAGS=${ADAMAKEFLAGS:-"-cargs ${ADACFLAGS} -margs"}
	export ADAMAKEFLAGS=${ADAMAKEFLAGS:-""}
	export ADABINDFLAGS=${ADABINDFLAGS:-""}
}

gnat-r1_src_compile() {
	:
}

gnat-r1_pkg_postinst() {
	einfo "Updating gnat configuration to pick up ${PN} library..."
	eselect gnat update
	elog "The environment has been set up to make gnat automatically find files"
	elog "for the installed library. In order to immediately activate these"
	elog "settings please run:"
	elog
	#elog "env-update"
	elog "source /etc/profile"
	einfo
	einfo "Otherwise the settings will become active next time you login"
}




# standard lib_compile plug. Adapted from base.eclass
lib_compile() {
	debug-print-function $FUNCNAME $*
	[ -z "$1" ] && lib_compile all

	cd ${SL}

	while [ "$1" ]; do
	case $1 in
		configure)
			debug-print-section configure
			econf || die "died running econf, $FUNCNAME:configure"
		;;
		make)
			debug-print-section make
			emake || die "died running emake, $FUNCNAME:make"
		;;
		all)
			debug-print-section all
			lib_compile configure make
		;;
	esac
	shift
	done
}

# Cycles through installed gnat profiles and calls lib_compile and then
# lib_install in turn.
# Use this function to build/install profile-specific binaries. The code
# building/installing common stuff (docs, etc) can go before/after, as needed,
# so that it is called only once..
#
# lib_compile and lib_install are passed the active gnat profile name - may be used or
# discarded as needed..
gnat_src_compile() {
	debug-print-function $FUNCNAME $*

	# We source the eselect-gnat module and use its functions directly, instead of
	# duplicating code or trying to violate sandbox in some way..
	. ${GnatCommon} || die "failed to source gnat-common lib"

	compilers=( $(find_primary_compilers ) )
	if [[ -n ${compilers[@]} ]] ; then
		local i
		local AdaDep=$(get_ada_dep)
		for (( i = 0 ; i < ${#compilers[@]} ; i = i + 1 )) ; do
			if $(belongs_to_standard ${compilers[${i}]} ${AdaDep}); then
				einfo "compiling for gnat profile ${compilers[${i}]}"

				# copy sources
				mkdir "${DL}" "${DLbin}" "${DLgpr}"
				cp -dpR "${S}" "${SL}"

				# setup environment
				# As eselect-gnat also manages the libs, this will ensure the right
				# lib profiles are activated too (in case we depend on some Ada lib)
				generate_envFile ${compilers[${i}]} ${BuildEnv} && \
				expand_BuildEnv "${BuildEnv}" && \
				. "${BuildEnv}"  || die "failed to switch to ${compilers[${i}]}"
				# many libs (notably xmlada and gtkada) do not like to see
				# themselves installed. Need to strip them from ADA_*_PATH
				# NOTE: this should not be done in pkg_setup, as we setup
				# environment right above
				export ADA_INCLUDE_PATH=$(filter_env_var ADA_INCLUDE_PATH)
				export ADA_OBJECTS_PATH=$(filter_env_var ADA_OBJECTS_PATH)

				# call compilation callback
				cd "${SL}"
				gnat_filter_flags ${compilers[${i}]}
				lib_compile ${compilers[${i}]} || die "failed compiling for ${compilers[${i}]}"

				# call install callback
				cd "${SL}"
				lib_install ${compilers[${i}]} || die "failed installing profile-specific part for ${compilers[${i}]}"
				# move installed and cleanup
				mv "${DL}" "${DL}-${compilers[${i}]}"
				mv "${DLbin}" "${DLbin}-${compilers[${i}]}"
				mv "${DLgpr}" "${DLgpr}-${compilers[${i}]}"
				rm -rf "${SL}"
			else
				einfo "skipping gnat profile ${compilers[${i}]}"
			fi
		done
	else
		ewarn "Please note!"
		elog "Treatment of installed Ada compilers has recently changed!"
		elog "Libs are now being built only for \"primary\" compilers."
		elog "Please list gnat profiles (as reported by \"eselect gnat list\")"
		elog "that you want to regularly use (i.e., not just for testing)"
		elog "in ${PRIMELIST}, one per line."
		die "please make sure you have at least one gnat compiler installed and set as primary!"
	fi
}


# This function simply moves gnat-profile-specific stuff into proper locations.
# Use src_install in ebuild to install the rest of the package
gnat_src_install() {
	debug-print-function $FUNCNAME $*

	# prep lib specs directory
	. ${GnatCommon} || die "failed to source gnat-common lib"
	dodir ${SPECSDIR}/${PN}

	compilers=( $(find_primary_compilers) )
	if [[ -n ${compilers[@]} ]] ; then
		local i
		local AdaDep=$(get_ada_dep)
		for (( i = 0 ; i < ${#compilers[@]} ; i = i + 1 )) ; do
			if $(belongs_to_standard ${compilers[${i}]} ${AdaDep}); then
				debug-print-section "installing for gnat profile ${compilers[${i}]}"

				local DLlocation=${AdalibLibTop}/${compilers[${i}]}
				dodir ${DLlocation}
				cp -dpR "${DL}-${compilers[${i}]}" "${D}/${DLlocation}/${PN}"
				cp -dpR "${DLbin}-${compilers[${i}]}" "${D}/${DLlocation}"/bin
				cp -dpR "${DLgpr}-${compilers[${i}]}" "${D}/${DLlocation}"/gpr
				# create profile-specific specs file
				cp ${LibEnv} "${D}/${SPECSDIR}/${PN}/${compilers[${i}]}"
				sed -i -e "s:%DL%:${DLlocation}/${PN}:g" "${D}/${SPECSDIR}/${PN}/${compilers[${i}]}"
				sed -i -e "s:%DLbin%:${DLlocation}/bin:g" "${D}/${SPECSDIR}/${PN}/${compilers[${i}]}"
				sed -i -e "s:%DLgpr%:${DLlocation}/gpr:g" "${D}/${SPECSDIR}/${PN}/${compilers[${i}]}"
			else
				einfo "skipping gnat profile ${compilers[${i}]}"
			fi
		done
	else
		die "please make sure you have at least one gnat compiler installed!"
	fi
}
