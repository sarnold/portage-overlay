# Copyright 1999-2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=6

inherit gnome.org gnome2-utils meson xdg

DESCRIPTION="GNOME MultiWriter "
HOMEPAGE="https://wiki.gnome.org/Apps/MultiWriter"

LICENSE="GPL-2+"
SLOT="0"
IUSE="-elogind gnome systemd"
REQUIRED_USE="?? ( elogind systemd )"
KEYWORDS="~alpha ~amd64 ~arm ~arm64 ~ia64 ~ppc ~ppc64 ~sh ~sparc ~x86"

COMMON_DEPEND="
	>=x11-libs/gtk+-3.11.2:3
	>=dev-libs/glib-2.31:2
	>=dev-libs/libgusb-0.2.7
	>=sys-fs/udisks-2.7.6:2
	virtual/libgudev
	>=media-libs/libcanberra-0.1[gtk3]
	>=sys-auth/polkit-0.113:0
	>=app-arch/xz-utils-5.0.5
	elogind? ( >=sys-auth/elogind-209 )
	systemd? ( >=sys-apps/systemd-209:0= )
"
RDEPEND="${COMMON_DEPEND}
	x11-themes/adwaita-icon-theme
	sys-fs/dosfstools
	gnome? ( >=gnome-base/gnome-settings-daemon-3.8 )
"
# appstream-glib for developer_name tag in appdata (gettext-0.19.8.1 own appdata.its file doesn't have it yet)
# libxml2 for xml-stripblanks in gresource
DEPEND="${COMMON_DEPEND}
	dev-libs/appstream-glib
	dev-libs/libxml2:2
	dev-libs/libxslt
	dev-util/glib-utils
	>=sys-devel/gettext-0.19.8
	virtual/pkgconfig
"

#PATCHES=(
#	"${FILESDIR}"/elogind-support.patch # https://gitlab.gnome.org/GNOME/gnome-disk-utility/merge_requests/15
#)
# from localargs below
#$(meson_feature elogind libelogind)

src_configure() {
	local emesonargs=(
		$(meson_feature systemd libsystemd)
		$(meson_use gnome gsd_plugin)
	)
	meson_src_configure
}

pkg_postinst() {
	xdg_pkg_postinst
	gnome2_schemas_update
}

pkg_postrm() {
	xdg_pkg_postrm
	gnome2_schemas_update
}
