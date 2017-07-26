# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$

EAPI="5"

PYTHON_COMPAT=( python2_7 )

inherit eutils python-r1 unpacker

DESCRIPTION="Commercial version of app-emulation/wine with paid support."
HOMEPAGE="http://www.codeweavers.com/products/crossover/"
SRC_URI="install-crossover-standard-demo-${PV}.bin"

LICENSE="CROSSOVER"
SLOT="0"
KEYWORDS="-* ~amd64 ~x86"
IUSE="-capi +cups +dbus +gphoto2 +ldap +odbc +openal +opengl +scanner +v4l"
RESTRICT="fetch strip test"


MLIB_DEPS="amd64 ? (
	>=app-emulation/emul-linux-x86-soundlibs-2.1
	>=app-emulation/emul-linux-x86-xlibs-2.1
	app-emulation/emul-linux-x86-baselibs
	scanner? ( app-emulation/emul-linux-x86-medialibs )
	opengl? ( app-emulation/emul-linux-x86-opengl )
	openal? ( app-emulation/emul-linux-x86-sdl )
	)"

DEPEND="${RDEPEND}
        ${PYTHON_DEPS}
	dev-lang/perl
"

RDEPEND="sys-libs/glibc
	>=dev-lang/python-2.4
	>=dev-python/pygtk-2.10
	>=media-libs/freetype-2.0.0
	>=x11-libs/gtk+-2.10
	capi? ( net-dialup/capi4k-utils )
	cups? ( net-print/cups )
	gphoto2? ( media-libs/libgphoto2 )
	ldap? ( net-nds/openldap )
	odbc? ( dev-db/unixODBC )
	openal? ( media-libs/openal )
	opengl? ( virtual/opengl )
	scanner? ( media-gfx/sane-backends )
	v4l? ( media-libs/libv4l )
	dev-util/desktop-file-utils
	media-fonts/corefonts
	media-libs/alsa-lib
	media-libs/libgphoto2
	media-libs/libpng
	sys-apps/coreutils
	sys-apps/dbus
	virtual/modutils
	sys-process/procps
	virtual/jpeg
	x11-apps/mesa-progs
	x11-apps/xdpyinfo
	x11-libs/libXi
	x11-libs/libXmu
	x11-libs/libXrandr
	x11-libs/libXxf86dga
	x11-libs/libXxf86vm
	"

REQUIRED_USE="( ${PYTHON_REQUIRED_USE} )"

pkg_nofetch() {
	einfo "Please visit ${HOMEPAGE}"
	einfo "and place ${A} in ${DISTDIR}"
}

src_unpack() {
        # self unpacking zip archive; unzip warns about the exe stuff
        local a="${DISTDIR}/${A}"
        echo ">>> Unpacking ${a} to ${PWD}"
        unzip -q "${a}"
        [ $? -gt 1 ] && die "unpacking failed"
}

src_prepare() {
	python_convert_shebangs -r 2 .
}

src_install() {
	dodir /opt/cxoffice
	cp -r * "${D}/opt/cxoffice" || die "cp failed"
	#"${D}" "/opt/cxoffice/bin/cxmenu" --crossover --install
	insinto /opt/cxoffice/etc
	doins share/crossover/data/cxoffice.conf
	# Workaround for inability to make menu entries
	mkdir -p "${D}/usr/share/desktop-directories/"
	cat << END > "${D}/usr/share/desktop-directories/cxmenu-cxoffice-0-29ra4ke.directory"
[Desktop Entry]
Encoding=UTF-8
Type=Directory
X-Created-By=portage-0
Icon=/opt/cxoffice/share/icons/crossover.xpm
Name=CrossOver Standard Demo
END
	mkdir -p "${D}/etc/xdg/menus/applications-merged"
	cat << END > "${D}/etc/xdg/menus/applications-merged/cxmenu-cxoffice-0.menu"
<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN" "http://www.freedesktop.org/standards/menu-spec/1.0/menu.dtd">
<Menu>
  <Name>Applications</Name>
  <Menu>
    <Name>CrossOver+Standard</Name>
    <Directory>cxmenu-cxoffice-0-29ra4ke.directory</Directory>
    <Include>
      <Category>X-cxmenu-cxoffice-0-29ra4ke</Category>
    </Include>
  </Menu>
</Menu>
END
	make_desktop_entry /opt/cxoffice/bin/cxsetup "Manage Bottles" /opt/cxoffice/share/icons/crossover.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
	make_desktop_entry /opt/cxoffice/bin/cxinstaller "Install Windows Software" /opt/cxoffice/share/icons/crossover.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
	make_desktop_entry /opt/cxoffice/bin/cxprefs "Preferences" /opt/cxoffice/share/icons/crossover.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
	make_desktop_entry /opt/cxoffice/bin/cxreset "Terminate Windows Applications" /opt/cxoffice/share/icons/cxreset.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
	make_desktop_entry /opt/cxoffice/bin/cxuninstall "Uninstall" /opt/cxoffice/share/icons/cxuninstall.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
#	make_desktop_entry "/opt/cxoffice/bin/launchurl	file:///home/richard/cxgames/doc/en/index.html" "User Documentation" /opt/cxoffice/share/icons/cxdoc.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
	make_desktop_entry /opt/cxoffice/bin/cxrun "Run a Windows Command" /opt/cxoffice/share/icons/cxrun.xpm 'X-cxmenu-cxoffice-0-29ra4ke'
}

pkg_postinst() {
	elog "Run /opt/cxoffice/bin/cxsetup --crossover --install"
	elog "as a regular user to install menus."
}
