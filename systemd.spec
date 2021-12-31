# Where kdump expect the initrd overlay to be install
%global kdumpbuildroot %{_prefix}/lib/kdump/buildroot

Name:           kdump-initrd-systemd
Url:            https://www.freedesktop.org/wiki/Software/systemd
Version:        247.10
Release:        1%{?dist}
License:        LGPLv2+ and MIT and GPLv2+
Summary:        Kdump optimized version of systemd
Source0:        https://github.com/systemd/systemd-stable/archive/systemd-stable-%{version}.tar.gz

# https://github.com/systemd/systemd/pull/18124.patch
Patch1:         0001-initrd-add-an-env-variable-to-accept-non-ramfs-rootfs.patch

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  coreutils
BuildRequires:  acl
BuildRequires:  libcap-devel
BuildRequires:  libmount-devel
BuildRequires:  libblkid-devel
BuildRequires:  kmod-devel
BuildRequires:  libxslt
BuildRequires:  docbook-style-xsl
BuildRequires:  gperf
BuildRequires:  gawk
BuildRequires:  tree
BuildRequires:  hostname
BuildRequires:  python3-devel
BuildRequires:  python3-lxml
BuildRequires:  firewalld-filesystem
BuildRequires:  meson >= 0.43
BuildRequires:  m4
BuildRequires:  make
BuildRequires:  gettext
Requires:       dbus >= 1.9.18
Requires:       kexec-tools

%description
This is a re-packaged mininized systemd for kdump use.

%prep -n systemd-stable-%{version}
%setup -n systemd-stable-%{version}

# Apply patches, autosetup won't work with "-n" here
%patch1 -p1

%build -n systemd-stable-%{version}
%define ntpvendor %(source /etc/os-release; echo ${ID})
%{!?ntpvendor: echo 'NTP vendor zone is not set!'; exit 1}

# Keep these configs consistent with main systemd package
CONFIGURE_OPTS=(
        -Dmode=release
        -Dsysvinit-path=/etc/rc.d/init.d
        -Drc-local=/etc/rc.d/rc.local
        -Dntp-servers='0.%{ntpvendor}.pool.ntp.org 1.%{ntpvendor}.pool.ntp.org 2.%{ntpvendor}.pool.ntp.org 3.%{ntpvendor}.pool.ntp.org'
        -Ddns-servers=
        -Duser-path=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin
        -Dservice-watchdog=
        -Ddev-kvm-mode=0666
        -Dsplit-usr=false
        -Dsplit-bin=true
        -Ddefault-kill-user-processes=false
        -Dtty-gid=5
        -Dusers-gid=100
        -Dnobody-user=nobody
        -Dnobody-group=nobody
        -Dcompat-mutable-uid-boundaries=true
        -Dfallback-hostname=fedora
        -Ddefault-dnssec=no
        # https://bugzilla.redhat.com/show_bug.cgi?id=1867830
        -Ddefault-mdns=no
        -Ddefault-llmnr=resolve
        -Dblkid=true
        -Dkmod=true
)

CONFIGURE_OPTS_KDUMP=(
        -Dacl=false
        -Dadm-group=false
        -Danalyze=false
        -Dapparmor=false
        -Daudit=false
        -Dbacklight=false
        -Dbinfmt=false
        -Dbzip2=false
        -Dlogind=false
        -Defi=false
        -Delfutils=false
        -Dfdisk=false
        -Dfirstboot=false
        -Dfuzz-tests=false
        -Dgcrypt=false
        -Dglib=false
        -Dgnu-efi=false
        -Dgnutls=false
        -Dgshadow=false
        -Dhibernate=false
        -Dhomed=false
        -Dhostnamed=false
        -Dhtml=false
        -Dhwdb=false
        -Didn=false
        -Dima=false
        -Dimportd=false
        -Dkernel-install=false
        -Dldconfig=false
        -Dlibcurl=false
        -Dlibfido2=false
        -Dlibidn=false
        -Dlibidn2=false
        -Dlibiptc=false
        -Dlocaled=false
        -Dlz4=false
        -Dmachined=false
        -Dman=false
        -Dnetworkd=false
        -Dnscd=false
        -Dnss-myhostname=false
        -Dnss-mymachines=false
        -Dnss-resolve=false
        -Dnss-systemd=false
        -Doomd=false
        -Dopenssl=false
        -Doss-fuzz=false
        -Dp11kit=false
        -Dpam=false
        -Dpcre2=false
        -Dpolkit=false
        -Dportabled=false
        -Dpstore=false
        -Dpwquality=false
        -Dqrencode=false
        -Dquotacheck=false
        -Drandomseed=false
        -Dremote=false
        -Drepart=false
        -Dresolve=false
        -Drfkill=false
        -Dseccomp=false
        -Dselinux=false
        -Dsmack=false
        -Dstandalone-binaries=false
        -Dsysusers=false
        -Dtests=false
        -Dtimedated=false
        -Dtimesyncd=false
        -Dtpm=false
        -Dtpm2=false
        -Duserdb=false
        -Dutmp=false
        -Dvalgrind=false
        -Dxdg-autostart=false
        -Dxkbcommon=false
        -Dxz=false
        -Dzlib=false
        -Dzstd=false
        -Dlink-networkd-shared=false
        -Dlink-timesyncd-shared=false
        -Dmicrohttpd=false
        -Dhtml=false
        -Dlibcryptsetup=false
        # Avoid eh_frame overhead
        -Dc_args="-fno-asynchronous-unwind-tables"
        -Dversion-tag=v%{version}-%{release}-kdump
        # Smaller build
        -Db_lto=true
        --optimization=s
        --auto-features=disabled
)

%meson "${CONFIGURE_OPTS[@]}" "${CONFIGURE_OPTS_KDUMP[@]}"
%meson_build

# Install normally, then move everything under %kdumpbuildroot
%install
%meson_install
mkdir -p %{buildroot}/%{_sbindir}
ln -sf ../bin/udevadm %{buildroot}%{_sbindir}/udevadm

# Move everything under %{kdumpbuildroot}
mkdir -p %{buildroot}/.inst
mv %{buildroot}/* %{buildroot}/.inst/
mkdir -p %{buildroot}/%{kdumpbuildroot}
mv %{buildroot}/.inst/* %{buildroot}/%{kdumpbuildroot}

# Remove unwanted files and then simply include all rest files
rm -rf %{buildroot}/%{kdumpbuildroot}/usr/include
rm -rf %{buildroot}/%{kdumpbuildroot}/usr/lib/systemd/tests
find %{buildroot}/%{kdumpbuildroot} -printf "/%{kdumpbuildroot}/%%P\n" >> .file-list

%check
%if %{with tests}
meson test -C %{_vpath_builddir} -t 6 --print-errorlogs
%endif

%files -f .file-list
%doc %{kdumpbuildroot}/usr/share/doc/systemd
%exclude
%{kdumpbuildroot}/usr/share/doc/systemd/LICENSE.*
%license
%{kdumpbuildroot}/usr/share/doc/systemd/LICENSE.LGPL2.1
%{kdumpbuildroot}/usr/share/doc/systemd/LICENSE.GPL2

%changelog
* Wed Dec 23 2020 Kairui Song <kasong@redhat.com> - 247.2-2
- Initial release
