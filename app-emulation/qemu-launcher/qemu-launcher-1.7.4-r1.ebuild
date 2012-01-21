# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils linux-info

DESCRIPTION="GNOME/Gtk front-end for the Qemu x86 PC emulator"
HOMEPAGE="http://projects.wanderings.us/qemu_launcher"
SRC_URI="http://download.gna.org/qemulaunch/1.7.x/${PN}_${PV}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~x86"
IUSE="+kvm"

DEPEND="!app-emulation/qemu-kvm
	dev-lang/perl
	>=dev-perl/gtk2-perl-1.121
	>=dev-perl/gtk2-gladexml-1.005
	>=dev-perl/gnome2-perl-1.023
	>=dev-perl/Locale-gettext-1.05
	>=app-emulation/qemu-0.10.1[kvm?]"

RDEPEND="${DEPEND}
	app-emulation/qemuctl"

kvm_kern_warn() {
	eerror "Please enable KVM support in your kernel, found at:"
	eerror
	eerror "  Virtualization"
	eerror "    Kernel-based Virtual Machine (KVM) support"
	eerror
}

pkg_setup() {
	if use kvm; then
		if kernel_is lt 2 6 25; then
			eerror "KVM support requres a host kernel of 2.6.25 or higher."
			eerror "Please upgrade your kernel..."
			die "kernel version not compatible"
		else
			if ! linux_config_exists; then
				eerror "Unable to check your kernel for KVM support"
				kvm_kern_warn
			elif ! linux_chkconfig_present KVM; then
				kvm_kern_warn
			fi
		fi

		enewgroup qemu
	fi
}

src_prepare() {
	epatch "${FILESDIR}"/${P}-qemu-update.patch
	sed -i -e "s|usr/local|usr/|" \
		-e "s|doc/qemu-launcher|doc/${P}|" \
		Makefile
	sed -i -e "s|qemu-launcher.svg|/usr/share/icons/hicolor/scalable/apps/qemu-launcher.svg|" \
		-e "s|Utility|Other|" \
		qemu-launcher.desktop
}

src_compile() {
	emake || die "emake failed"
}

src_install() {
	make DESTDIR=${D} install

	insinto /etc/udev/rules.d/
	doins ${FILESDIR}/48-qemu-kvm.rules || die

}

pkg_postinst() {
	if use kvm; then
		elog "If you don't have kvm compiled into the kernel, make sure you have"
		elog "the kernel module loaded before running qemu. The easiest way to"
		elog "ensure that the kernel module is loaded is to load it on boot."
		elog "For AMD CPUs the module is called 'kvm-amd'"
		elog "For Intel CPUs the module is called 'kvm-intel'"
		elog "Please review /etc/conf.d/modules for how to load these"
		elog
		elog "Make sure your user is in the 'qemu' group"
		elog "Just run 'gpasswd -a <USER> qemu', then have <USER> re-login."
		elog
	fi
	elog "You will need the Universal TUN/TAP driver compiled into your"
	elog "kernel or loaded as a module to use the virtual network device"
	elog "if using -net tap.  You will also need support for 802.1d"
	elog "Ethernet Bridging and a configured bridge if using the provided"
	elog "scripts from /etc/qemu.  Or else try the user-mode driver and"
	elog "just put in your MAC address and use DHCP in the guest OS."
	echo
}
