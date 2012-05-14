Name:               ganglia
Version:            3.3.7
Release:            4%{?dist}
Summary:            Ganglia Distributed Monitoring System

Group:              Applications/Internet
License:            BSD
URL:                http://ganglia.sourceforge.net/
Source0:            http://downloads.sourceforge.net/sourceforge/%{name}/%{name}-%{version}.tar.gz
Source1:            gmond.service
Source2:            gmetad.service
Patch0:             diskusage-pcre.patch
Patch2:             diskmetrics.patch
Buildroot:          %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:      systemd-units
BuildRequires:      rrdtool-devel
BuildRequires:      apr-devel >= 1
BuildRequires:      libpng-devel
BuildRequires:      libart_lgpl-devel
BuildRequires:      libconfuse-devel
BuildRequires:      expat-devel
BuildRequires:      python-devel
BuildRequires:      freetype-devel
BuildRequires:      pcre-devel


%description
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

%package web
Summary:            Ganglia Web Frontend
Group:              Applications/Internet
Requires:           rrdtool
Requires:           php
Requires:           php-gd
Requires:           php-ZendFramework
Requires:           %{name}-gmetad = %{version}-%{release}

%description web
This package provides a web frontend to display the XML tree published by
ganglia, and to provide historical graphs of collected metrics. This website is
written in the PHP4 language.

%package gmetad
Summary:            Ganglia Metadata collection daemon
Group:              Applications/Internet
Requires:           %{name} = %{version}-%{release}
# This is actually needed for the %triggerun script but Requires(triggerun)
# is not valid.  We can use %post because this particular %triggerun script
# should fire just after this package is installed.
Requires(post):     systemd-sysv
Requires(post):     systemd-units
Requires(preun):    systemd-units
Requires(postun):   systemd-units

%description gmetad
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This gmetad daemon aggregates monitoring data from several clusters
to form a monitoring grid. It also keeps metric history using rrdtool.

%package gmond
Summary:            Ganglia Monitoring daemon
Group:              Applications/Internet
Requires:           %{name} = %{version}-%{release}
# This is actually needed for the %triggerun script but Requires(triggerun)
# is not valid.  We can use %post because this particular %triggerun script
# should fire just after this package is installed.
Requires(post):     systemd-sysv
Requires(post):     systemd-units
Requires(preun):    systemd-units
Requires(postun):   systemd-units

%description gmond
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This gmond daemon provides the ganglia service within a single cluster or
Multicast domain.

%package gmond-python
Summary:            Ganglia Monitor daemon python DSO and metric modules
Group:              Applications/Internet
Requires:           ganglia-gmond
Requires:           python

%description gmond-python
Ganglia is a scalable, real-time monitoring and execution environment
with all execution requests and statistics expressed in an open
well-defined XML format.

This package provides the gmond python DSO and python gmond modules, which
can be loaded via the DSO at gmond daemon start time.

%package devel
Summary:            Ganglia Library
Group:              Applications/Internet
Requires:           %{name} = %{version}-%{release}

%description devel
The Ganglia Monitoring Core library provides a set of functions that
programmers can use to build scalable cluster or grid applications

%prep
%setup -q
%patch0 -p1
%patch2 -p1
## Hey, those shouldn't be executable...
chmod -x lib/*.{h,x}

%build
%configure \
    --enable-setuid=ganglia \
    --enable-setgid=ganglia \
    --with-gmetad \
    --disable-static \
    --enable-shared \
    --sysconfdir=%{_sysconfdir}/ganglia

## Default to run as user ganglia instead of nobody
%{__perl} -pi.orig -e 's|nobody|ganglia|g' \
    gmond/gmond.conf.html ganglia.html gmond/conf.pod

## Don't have initscripts turn daemons on by default
%{__perl} -pi.orig -e 's|2345|-|g' \
    gmond/gmond.init gmetad/gmetad.init

make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT 

## Put web files in place
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/%{name}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
cp -rp web/* $RPM_BUILD_ROOT%{_datadir}/%{name}/
mv $RPM_BUILD_ROOT%{_datadir}/%{name}/conf_default.php $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/
ln -s ../../..%{_sysconfdir}/%{name}/conf_default.php \
    $RPM_BUILD_ROOT%{_datadir}/%{name}/conf_default.php
cat << __EOF__ > $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/%{name}.conf
  #
  # Ganglia monitoring system php web frontend
  #
  
  Alias /%{name} %{_datadir}/%{name}

  <Location /%{name}>
    Order deny,allow
    Deny from all
    Allow from 127.0.0.1
    Allow from ::1
    # Allow from .example.com
  </Location>
__EOF__

## Create directory structures
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d
mkdir -p $RPM_BUILD_ROOT%{_libdir}/ganglia/python_modules
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/rrds
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/conf
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/dwoo/cache
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}/dwoo/compiled
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man5
## Put files in place
install -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/gmond.service
install -p -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/gmetad.service
cp -p gmond/gmond.conf.5 $RPM_BUILD_ROOT%{_mandir}/man5/gmond.conf.5
cp -p gmetad/gmetad.conf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/gmetad.conf
cp -p mans/*.1 $RPM_BUILD_ROOT%{_mandir}/man1/
## Build default gmond.conf from gmond using the '-t' flag
gmond/gmond -t | %{__perl} -pe 's|nobody|ganglia|g' > $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/gmond.conf

## Python bits
# Copy the python metric modules and .conf files
cp -p gmond/python_modules/conf.d/*.pyconf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/
cp -p gmond/modules/conf.d/*.conf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/
cp -p gmond/python_modules/*/*.py $RPM_BUILD_ROOT%{_libdir}/ganglia/python_modules/
# Don't install the example modules
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/example.conf
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/example.pyconf
# Don't install the status modules
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/modgstatus.conf
# Clean up the .conf.in files
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/*.conf.in
## Disable the diskusage module until it is configured properly
#mv $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/diskusage.pyconf $RPM_BUILD_ROOT%{_sysconfdir}/ganglia/conf.d/diskusage.pyconf.off
# Don't install Makefile* in the web dir
rm -f $RPM_BUILD_ROOT%{_datadir}/%{name}/Makefile*

## Install binaries
make install DESTDIR=$RPM_BUILD_ROOT
## House cleaning
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_datadir}/%{name}/{Makefile.am,version.php.in}

#use system php-ZendFramework
rm -rf $RPM_BUILD_ROOT/usr/share/ganglia/lib/Zend
ln -s /usr/share/php/Zend $RPM_BUILD_ROOT/usr/share/ganglia/lib/Zend

%clean
rm -rf $RPM_BUILD_ROOT

%pre
## Add the "ganglia" user
/usr/sbin/useradd -c "Ganglia Monitoring System" \
        -s /sbin/nologin -r -d %{_localstatedir}/lib/%{name} ganglia 2> /dev/null || :
/sbin/ldconfig

%post -p /sbin/ldconfig

%post gmond
if [ $1 -eq 1 ] ; then 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun gmond
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable gmond.service > /dev/null 2>&1 || :
    /bin/systemctl stop gmond.service > /dev/null 2>&1 || :
fi

%postun gmond
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart gmond.service >/dev/null 2>&1 || :
fi

%post gmetad
if [ $1 -eq 1 ] ; then 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun gmetad
if [ $1 -eq 0 ] ; then
    /bin/systemctl --no-reload disable gmetad.service > /dev/null 2>&1 || :
    /bin/systemctl stop gmetad.service > /dev/null 2>&1 || :
fi

%postun gmetad
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    /bin/systemctl try-restart gmetad.service >/dev/null 2>&1 || :
fi

%post devel -p /sbin/ldconfig

%postun devel -p /sbin/ldconfig

%post web
if [ ! -L /usr/share/ganglia/lib/Zend ]; then
  ln -s /usr/share/php/Zend /usr/share/ganglia/lib/Zend
fi


### A sysv => systemd migration contains all of the same scriptlets as a
### systemd package.  These are additional scriptlets

# Note: the NEVR in trigger scripts should all be the version in
# which the package switched to systemd unit files and the comparision
# should be less than.  Using <= the last version with the sysV script won't
# work for several reasons:
# 1) disttag is different between Fedora releases
# 2) An update in an old Fedora release may create a newer NEVR
#    Note that this means an update in an older Fedora release must be NEVR
#    lower than this.  Freezing the version and release of the old package and
#    using a number after the disttag is one way to do this.  Example:
#        httpd-1.0-1%{?dist} => httpd-1.0-1%{?dist}.1

%triggerun gmond -- ganglia-gmond < 3.3.7-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply gmond
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save gmond >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del gmond >/dev/null 2>&1 || :
/bin/systemctl try-restart gmond.service >/dev/null 2>&1 || :

%triggerun gmetad -- ganglia-gmetad < 3.3.7-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply gmetad
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save gmetad >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del gmetad >/dev/null 2>&1 || :
/bin/systemctl try-restart gmetad.service >/dev/null 2>&1 || :

%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING NEWS README ChangeLog
%{_libdir}/libganglia*.so.*
%dir %{_libdir}/ganglia
%{_libdir}/ganglia/*.so
%exclude %{_libdir}/ganglia/modpython.so

%files gmetad
%defattr(-,root,root,-)
%dir %{_localstatedir}/lib/%{name}
%attr(0755,ganglia,ganglia) %{_localstatedir}/lib/%{name}/rrds
%{_sbindir}/gmetad
%{_unitdir}/gmetad.service
%{_mandir}/man1/gmetad.1*
%{_mandir}/man1/gmetad.py.1*
%dir %{_sysconfdir}/ganglia
%config(noreplace) %{_sysconfdir}/ganglia/gmetad.conf

%files gmond
%defattr(-,root,root,-)
%{_bindir}/gmetric
%{_bindir}/gstat
%{_sbindir}/gmond
%{_unitdir}/gmond.service
%{_mandir}/man5/gmond.conf.5*
%{_mandir}/man1/gmond.1*
%{_mandir}/man1/gstat.1*
%{_mandir}/man1/gmetric.1*
%dir %{_sysconfdir}/ganglia
%dir %{_sysconfdir}/ganglia/conf.d
%config(noreplace) %{_sysconfdir}/ganglia/gmond.conf
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/*.conf
%exclude %{_sysconfdir}/ganglia/conf.d/modpython.conf

%files gmond-python
%defattr(-,root,root,-)
%dir %{_libdir}/ganglia/python_modules/
%{_libdir}/ganglia/python_modules/*.py*
%{_libdir}/ganglia/modpython.so*
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/*.pyconf*
%config(noreplace) %{_sysconfdir}/ganglia/conf.d/modpython.conf

%files devel
%defattr(-,root,root,-)
%{_bindir}/ganglia-config
%{_includedir}/*.h
%{_libdir}/libganglia*.so

%files web
%defattr(-,root,root,-)
%doc web/AUTHORS web/COPYING
%config(noreplace) %{_sysconfdir}/%{name}/conf_default.php
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{_datadir}/%{name}
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/conf
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/dwoo
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/dwoo/cache
%dir %attr(0755,apache,apache) %{_localstatedir}/lib/%{name}/dwoo/compiled

%changelog
* Mon May 14 2012 Jon Ciesla <limburgher@gmail.com> - 3.3.7-4
- Unbundle Zend.

* Fri May 11 2012 Terje Rosten <terje.rosten@ntnu.no> - 3.3.7-3
- Fix web frontend

* Fri May 11 2012 Jon Ciesla <limburgher@gmail.com> - 3.3.7-2
- scriptlet corrections.

* Mon May 07 2012 Terje Rosten <terje.rosten@ntnu.no> - 3.3.7-1
- Update to 3.3.7
- Split buildreq/req
- Remove svn tag
- Fix src url
- Remove patches now upstream
- More man pages
- Move web config
- Move ganglia-config to -devel
- Systemd support

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 3.1.7-6
- Rebuild against PCRE 8.30

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Jun 14 2011 Kostas Georgiou <georgiou@fedoraproject.org> - 3.1.7-4
- Fix buffer overflow in moddisk.so #689483

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Jul 31 2010 Thomas Spura <tomspur@fedoraproject.org> - 3.1.7-2
- Rebuild for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Thu Apr 22 2010 Kostas Georgiou <georgiou@fedoraproject.org> - 3.1.7-1
- New upstream release
- Spec file cleanups
- Use the new name_match feature to enable the diskusage plugin by default

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sun Mar 29 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.2-3
- Rebuilt for #492703, no obvious reasons why the previous build was bad :(

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Feb 17 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.2-1
- Update to 3.1.2
- Remove unneeded patch for CVE-2009-0241

* Tue Jan 20 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.1-4
- [480236] Updated patch for the buffer overflow from upstream with
  additional fixes

* Wed Jan 14 2009 Kostas Georgiou <k.georgiou@imperial.ac.uk> - 3.1.1-3
- Fix for gmetad server buffer overflow
- The private_clusters file should not be readable by everyone

* Sun Nov 30 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 3.1.1-2
- Rebuild for Python 2.6

* Fri Oct 24 2008 Jarod Wilson <jarod@redhat.com> 3.1.1-1
- Update to 3.1.1

* Thu Aug 28 2008 Michael Schwendt <mschwendt@fedoraproject.org> 3.1.0-2
- Include unowned directories.

* Mon Aug 11 2008 Kostas Georgiou <k.georgiou@imperial.ac.uk> 3.1.0-1
- Upstream patches from 3.1.1
- Move private_clusters config to /etc and mark it as a config file
- Only allow connections from localhost by default on the web frontend
- Add some extra module config files (modules are always loaded at the
  moment so removing the configs has no effect beyond metric collection
  (upstream is working on way way to disable module loading from the
  configs)

* Tue Jul 29 2008 Kostas Georgiou <k.georgiou@imperial.ac.uk> 3.1.0-0.5
- Add the config files for the python module

* Thu Jul 17 2008 Kostas Georgiou <k.georgiou@imperial.ac.uk> 3.1.0-0.4
- Update to the 3.1.0 pre-release
- Fixes gmond.conf to use the ganglia user and not nobody
- Removal of the ppc64 work-around
 
* Fri Jun 13 2008 Jarod Wilson <jwilson@redhat.com> 3.1.0-0.3.r1399
- One more try at work-around. Needs powerpc64, not ppc64...

* Fri Jun 13 2008 Jarod Wilson <jwilson@redhat.com> 3.1.0-0.2.r1399
- Work-around for incorrectly hard-coded libdir on ppc64

* Wed Jun 11 2008 Jarod Wilson <jwilson@redhat.com> 3.1.0-0.1.r1399
- Update to 3.1.x pre-release snapshot, svn rev 1399

* Mon Jun 09 2008 Jarod Wilson <jwilson@redhat.com> 3.0.7-2
- Bump and rebuild against latest rrdtool

* Wed Feb 27 2008 Jarod Wilson <jwilson@redhat.com> 3.0.7-1
- New upstream release
- Fixes "Show Hosts" toggle
- Fixes to host view metric graphs
- Fixes two memory leaks

* Thu Feb 14 2008 Jarod Wilson <jwilson@redhat.com> 3.0.6-2
- Bump and rebuild with gcc 4.3

* Mon Dec 17 2007 Jarod Wilson <jwilson@redhat.com> 3.0.6-1
- New upstream release (security fix for web frontend
  cross-scripting vulnerability) {CVE-2007-6465}

* Wed Oct 24 2007 Jarod Wilson <jwilson@redhat.com> 3.0.5-2
- Reorg packages to fix multilib conflicts (#341201)

* Wed Oct 03 2007 Jarod Wilson <jwilson@redhat.com> 3.0.5-1
- New upstream release

* Fri May 18 2007 Jarod Wilson <jwilson@redhat.com> 3.0.4-3
- Add missing Req: php-gd so people will see nifty pie charts

* Sat Mar 24 2007 Jarod Wilson <jwilson@redhat.com> 3.0.4-2
- Own created directories (#233790)

* Tue Jan 02 2007 Jarod Wilson <jwilson@redhat.com> 3.0.4-1
- New upstream release

* Thu Nov 09 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-11
- gmond also needs ganglia user (#214762)

* Tue Sep 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-10
- Rebuild for new glibc

* Fri Jul 28 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-9
- Add missing Reqs on chkconfig and service
- Make %%preun sections match Fedora Extras standards
- Minor %%configure tweak

* Tue Jul 11 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-8
- Add missing php req for ganglia-web
- Misc tiny spec cleanups

* Tue Jun 13 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-7
- Clean up documentation

* Mon Jun 12 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-6
- Remove misplaced execute perms on source files

* Thu Jun 08 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-5
- Whack Obsoletes/Provides, since its never been in FE before
- Use mandir macro
- Check if service is running before issuing a stop in postun
- Remove shadow-utils Prereq, its on the FE exception list

* Mon Jun 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-4
- Run things as user ganglia instead of nobody
- Don't turn on daemons by default

* Mon Jun 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-3
- Kill off static libs
- Add URL for Source0

* Mon Jun 05 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-2
- Move web-frontend from /var/www/html/ to /usr/share/
- Make everything arch-specific

* Thu Jun 01 2006 Jarod Wilson <jwilson@redhat.com> 3.0.3-1
- Initial build for Fedora Extras, converting existing spec to
  (attempt to) conform with Fedora packaging guidelines
