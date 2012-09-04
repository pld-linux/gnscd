# NOTE
# - works in glibc 2.3, but apparently up to version where format changed,
#   2.16.0 definately segfaults on both x86_64/i686
# TODO
# - x86_64 warning is important?
#  thread.c: In function 'handle_client_thread':
#  thread.c:303:18: warning: cast from pointer to integer of different size [-Wpointer-to-int-cast]
#  thread.c: In function 'dispatch_client':
#  thread.c:346:64: warning: cast to pointer from integer of different size [-Wint-to-pointer-cast]
%define		svnrev	6
Summary:	NSCD (Name Service Caching Daemon) Google reimplementation of GNU nscd
Name:		gnscd
Version:	1.0.3
Release:	0.1
License:	GPL v2
Group:		Networking/Daemons
# use get-source.sh
Source0:	%{name}-%{svnrev}.tar.bz2
# Source0-md5:	2f0f325ccb10c50c6ec5c63cabced836
Source1:	nscd.init
Source2:	nscd.sysconfig
Source3:	nscd.logrotate
Source4:	nscd.conf
Source5:	nscd.tmpfiles
Source6:	get-source.sh
URL:		https://code.google.com/p/gnscd/
BuildRequires:	sed >= 4.0
Provides:	group(nscd)
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	rc-scripts >= 0.4.1.26
Provides:	user(nscd)
Obsoletes:	nscd
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# glibc private symbols
%define		_noautoreq		libc.so.6(GLIBC_PRIVATE)

%description
A daemon which handles passwd, group and host lookups for running
programs and caches the results for the next query. You only need this
package if you are using slow Name Services like LDAP, NIS or NIS+.

gnscd is Google reimplementation of GNU nscd, rewritten with different
networking and database code. Additionally, it listens on both
/var/run/nscd/socket and the older path /var/run/.nscd_socket, making
the nscd-compat wrapper daemon unnecessary.

It should mostly be a drop-in replacement for existing installs using
nscd.

%prep
%setup -qc
mv %{name}/* .

%{__sed} -i -e 's,gcc,$(CC),' src/Makefile

%build
%{__make} -C src \
	CC="%{__cc}" \
	ARCH=exe \
	CFLAGS="%{rpmcflags} -D_GNU_SOURCE" \
	LDFLAGS="-lpthread %{rpmldflags}"

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_sbindir},%{_mandir}/man8,/var/log,/var/run/nscd,/etc/{logrotate.d,rc.d/init.d,sysconfig},%{systemdtmpfilesdir}}
install -p src/gnscd.exe $RPM_BUILD_ROOT%{_sbindir}/nscd
install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/nscd
cp -p %{name}.8 $RPM_BUILD_ROOT%{_mandir}/man8
echo '.so man8/nscd.8' >  $RPM_BUILD_ROOT%{_mandir}/man8/nscd.8
cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/nscd
cp -p %{SOURCE3} $RPM_BUILD_ROOT/etc/logrotate.d/nscd
cp -p %{SOURCE4} $RPM_BUILD_ROOT%{_sysconfdir}
cp -p %{SOURCE5} $RPM_BUILD_ROOT%{systemdtmpfilesdir}/nscd.conf
: > $RPM_BUILD_ROOT/var/log/nscd

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -P nscd -g 144 -r nscd
%useradd -P nscd -u 144 -r -d /tmp -s /bin/false -c "Name Service Cache Daemon" -g nscd nscd

%post
if [ ! -f /var/log/nscd ]; then
	umask 027
	touch /var/log/nscd
	chown root:root /var/log/nscd
	chmod 640 /var/log/nscd
fi
/sbin/chkconfig --add nscd
%service nscd restart "Name Service Cache Daemon"

%preun
if [ "$1" = "0" ]; then
	%service nscd stop
	/sbin/chkconfig --del nscd
fi

%postun
if [ "$1" = "0" ]; then
	%userremove nscd
	%groupremove nscd
fi

%files
%defattr(644,root,root,755)
%doc debian/changelog
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/nscd
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/nscd.conf
%attr(754,root,root) /etc/rc.d/init.d/nscd
%attr(755,root,root) %{_sbindir}/nscd
%{_mandir}/man8/*nscd.8*
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/logrotate.d/nscd
%attr(640,root,root) %ghost /var/log/nscd
%{systemdtmpfilesdir}/nscd.conf
%dir /var/run/nscd
