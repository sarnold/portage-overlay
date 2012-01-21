# $Id: bitpim.spec 4219 2007-05-09 02:15:50Z djpham $

# NOTE: This file is preprocessed and some substitutions made by makedist.py

# Leave out all the stripping nonsense which strips the python bytecode out
# of the main exe!
%define __os_install_post /usr/lib/rpm/brp-compress
# the debug stuff is left in since it strips all the shared libraries which
# is ok.  here is how to turn off debuginfo packages (and increase the rpm
# size by 33%)
# %define debug_package %{nil}

Summary: Interfaces with the phonebook, calendar, wallpaper of many CDMA phones
Name: %%RPMNAME%%
Version: %%RPMVERSION%%
Release: %%RELEASE%%
Packager: %%PUBLISHER%%
License: GNU GPL
Group: Utilities/Phone
URL: http://www.bitpim.org
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
AutoReqProv: no

%description
BitPim is a program that allows you to view and manipulate data on
many CDMA phones from LG, Samsung, Sanyo and other manufacturers. This
includes the PhoneBook, Calendar, WallPapers, RingTones (functionality
varies by phone) and the Filesystem for most Qualcomm CDMA chipset
based phones.

%prep
%setup -q

%build

%install
find $RPM_BUILD_ROOT -type d -print0 | xargs -0 chmod +w || true
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
tar xvf dist.tar -C $RPM_BUILD_ROOT

%post
if [ -x /usr/bin/udevinfo ] && \
   [ -d /etc/udev/rules.d ] && \
   [ $(/usr/bin/udevinfo -V | cut -d' ' -f3) -ge 95 ]
then
    respath=/usr/lib/%%NAME%%-%%VERSION%%/resources
    cp -f $respath/60-bitpim.rules /etc/udev/rules.d
    cp -f $respath/bpudev /usr/bin
    chmod 755 /usr/bin/bpudev
    mkdir -p /var/bitpim
fi

%postun
rm -rf /usr/lib/%%NAME%%-%%VERSION%% /var/bitpim \
   /usr/bin/bpudev /etc/udev/rules.d/60-bitpim.rules

%clean
find $RPM_BUILD_ROOT -type d -print0 | xargs -0 chmod +w || true
rm -rf $RPM_BUILD_ROOT

%files -f FILELIST
%defattr(-,root,root,-)

%doc
