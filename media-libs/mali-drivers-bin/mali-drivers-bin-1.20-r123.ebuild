# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Distributed under the terms of the GNU General Public License v2

EAPI=4

inherit unpacker multilib

DESCRIPTION="Mali drivers, binary only install"
HOMEPAGE="http://www.chromium.org/chromium-os/developer-information-for-chrome-os-devices/samsung-arm-chromebook"
SRC_URI="http://commondatastorage.googleapis.com/chromeos-localmirror/distfiles/mali-drivers-${PVR}.run"

LICENSE="Google-TOS"
SLOT="0"
KEYWORDS="arm"

DEPEND=""

RDEPEND="x11-base/xorg-server"

S=${WORKDIR}

src_install() {
	local opengl_imp="mali"
	local opengl_dir="opengl/${opengl_imp}"
	local x

	mkdir -p usr/lib/${opengl_dir}/lib
	for x in usr/lib/lib{EGL,GL*,mali}.so*; do
			einfo "moving ${x} to usr/lib/${opengl_dir}/lib/"
			if [ -f ${x} -o -L ${x} ]; then
					mv "${x}" usr/lib/${opengl_dir}/lib/ \
							|| die "Failed to move ${x}"
			fi
	done

	# We don't need the debug bits.
	rm -r usr/lib/debug
	# mesa installs these already
	rm -r usr/lib/pkgconfig

	insinto /usr/$(get_libdir)
	doins -r usr/lib/*

	touch "${ED}"/usr/$(get_libdir)/${opengl_dir}/.gles-only
}

pkg_postinst() {
	eselect opengl set --use-old ${opengl_imp}
}
