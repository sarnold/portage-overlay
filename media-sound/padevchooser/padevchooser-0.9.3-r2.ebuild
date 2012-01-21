# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/media-sound/padevchooser/padevchooser-0.9.3-r1.ebuild,v 1.4 2010/03/08 20:30:59 maekke Exp $

EAPI=2

inherit eutils autotools

DESCRIPTION="PulseAudio Device Chooser, tool for quick access to PulseAudio features"
HOMEPAGE="http://0pointer.de/lennart/projects/padevchooser/"
#SRC_URI="http://0pointer.de/lennart/projects/${PN}/${P}.tar.gz"
SRC_URI="mirror://gentoo/${PN}-latest.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="amd64 ~ppc ~sparc x86"

IUSE=""

DEPEND=">=x11-libs/gtk+-2.0
	>=gnome-base/libglade-2.0
	>=gnome-base/gconf-2.0
	x11-libs/libnotify
	>=media-sound/pulseaudio-0.9.2[avahi,glib]"
RDEPEND="${DEPEND}
	x11-themes/gnome-icon-theme"

S="${WORKDIR}/${PN}"

src_prepare() {
	epatch "${FILESDIR}"/${P}-r2-libnotify-0.7.patch

	#eautoreconf
	eaclocal
	eautoconf
	eautoheader
	eautomake

	# make the missing README file
	generate_files
}

src_configure() {
	# Lynx is used during make dist basically
	econf \
		--disable-dependency-tracking \
		--disable-lynx || die "econf failed"
}

src_install() {
	emake DESTDIR="${D}" install || die "make install failed"
	dohtml -r doc
	dodoc README
}

generate_files() {
	cat <<-EOF > doc/README
	This is my own version of the padevchooser package based on the latest
	GIT master/head as of 11/07/2010.  The only broken part so far is the 
	missing README that breaks the make rules...
	
	See the package README.html for the real info.
	EOF
}
