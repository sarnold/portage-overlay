# Copyright 1999-2019 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

EAPI=6
inherit cmake-utils kde5 xdg-utils

DESCRIPTION="Qt5 tray GUI for NetworkManager and lxqt"
HOMEPAGE="https://github.com/palinek/nm-tray"
SRC_URI="https://github.com/palinek/${PN}/archive/${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~amd64 ~arm ~arm64 ~x86"
IUSE=""

RDEPEND="
	dev-qt/qtcore:5
	dev-qt/qtgui:5
	dev-qt/qtnetwork:5
	dev-qt/qtdbus:5
	dev-qt/qtwidgets:5
	kde-frameworks/networkmanager-qt:5/5.60
"

DEPEND="${RDEPEND}
	dev-qt/linguist-tools:5
"
