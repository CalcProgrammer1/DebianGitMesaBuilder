#
#	Mesa Git Packaging Script for Debian Unstable
#
#	This script will create Debian (unstable) packages for Mesa from upstream git sources.
#	It will skip building swx11 versions of the Mesa libraries as these are not used in systems with a GPU
#	By default this script expects the Debian version to use llvm (and libclang) 3.8 and will change it to use llvm 3.9
#	If Debian updates their copy to use a different llvm version, or if a new version of llvm is released, this script must be updated
#
#   This script expects to be placed in /opt along with the other scripts and the Mesa git source to be present at /opt/mesa-git
#
#	The building system must have build-essential and devscripts installed
#
#   It is highly recommended to build using a dual chroot setup, one amd64 and one i386.  Run this script from the amd64 chroot to build amd64 .deb packages
#   and then exit out, chroot into the i386 chroot, cd to /opt/mesa/mesa-<latest version>/ and run dpkg-buildpackage -us -B -j24 to build i386 .deb packages
#
#   I use the following paths for my chroots:
#       /chroot/chroot-debian-unstable-amd64/
#       /chroot/chroot-debian-unstable-i386/
#
#   Create the chroots using debootstrap:
#       debootstrap --arch amd64 unstable /chroot/chroot-debian-unstable-amd64 http://ftp.debian.org/debian/
#       debootstrap --arch i386 unstable /chroot/chroot-debian-unstable-i386 http://ftp.debian.org/debian/
#
#   I have configured these in /etc/schroot/schroot.conf:
#
#   [debian-unstable-i386]
#   description=Debian Unstable i386
#   directory=/chroot/chroot-debian-unstable-i386/
#   users=adam
#   root-groups=root
#   aliases=unstable-i386
#
#   [debian-unstable-amd64]
#   description=Debian Unstable amd64
#   directory=/chroot/chroot-debian-unstable-amd64/
#   users=adam
#   root-groups=root
#   aliases=unstable-amd64
#
#   Bind mount /opt into the chroots as I use /opt as my build directory
#       sudo mount -o bind /opt /chroot/chroot-debian-unstable-amd64/opt
#       sudo mount -o bind /opt /chroot/chroot-debian-unstable-i386/opt
#
#   Enter the chroots using the following commands:
#       sudo schroot -c debian-unstable-amd64
#       sudo schroot -c debian-unstable-i386
#
#   Install build-essential, devscripts, git in both chroots
#       sudo apt-get install build-essential devscripts git
#
#   At the time of this writing (4/27/2016) it is recommended to install the LLVM development APT repository on your system (chroots included) to get the
#   most recent version of LLVM.  LLVM contains much of the radeonsi driver functionality and improvements to LLVM will likely improve your performance.
#   You can install this repository by adding the following lines to your /etc/apt/sources.list (both your main install and both chroots):
#
#   deb http://llvm.org/apt/unstable/ llvm-toolchain main
#   deb-src http://llvm.org/apt/unstable/ llvm-toolchain main
#
#   Install llvm-3.9, libclang-3.9-dev
#       sudo apt-get install llvm-3.9 libclang-3.9-dev
#
#   Copy this file to /opt/build-mesa-upstream-with-gallium-nine.py, since /opt is bind mounted it will show in both chroots
#   Copy patch.txt to /opt/patch.txt
#   Copy update-symbols.py to /opt/update-symbols.py
#
#   Clone the Mesa source repository to /opt/mesa-git
#       cd /opt
#       git clone git://anongit.freedesktop.org/mesa/mesa mesa-git
#
#   Or, if you want to try the Gallium Nine development tree:
#       cd /opt
#       git clone https://github.com/iXit/Mesa-3D
#
#   To begin build, enter your amd64 chroot and:
#       cd /opt
#       python build-mesa-upstream-with-gallium-nine.py
#
#   You may have to hit yes to some install prompts as the script will attempt to install build dependencies.
#   Then it will perform the build (dpkg-buildpackage -us -B -j24), which will likely fail the first time due to symbols mismatch with the Debian
#   version of the source as it is outdated.
#   This script will automatically attempt to resolve the symbols files (calling update-symbols.py) and then continue the build
#   where it left off (dpkg-buildpackage -us -B -j24 -nc)
#
#   If successful, a series of .deb files will be located in /opt/mesa
#
#   If these exist, you should now build i386 versions.  Enter your i386 chroot and:
#       cd /opt/mesa/mesa-<development version number>/ (use tab complete, it is 11.3 as of now)
#       dpkg-buildpackage -us -B -j24
#
#   If there are build dependencies to install, use
#       mk-build-deps --install debian/control
#   and then try the dpkg-buildpackage command again
#
#   If successful, i386 .deb packages will be located along with the amd64 versions in /opt/mesa
#
#   You may then install these on your main install with dpkg -i *.deb followed by apt-get -f install, or set up a local Debian repository
#   using reprepro and apache.  I'm not going into detail on how to set the repository server up in this document.  The packages are unsigned,
#   so installing them with apt-get will prompt you with a security warning.  This is OK for personal use but I would recommend signing your
#   packages if you intend to host a public repository.
#
#	Written by Adam Honse (calcprogrammer1) 4/27/2016
#

import os

print "Create mesa working directory in /opt"

os.chdir("/opt")
os.popen("rm -r mesa").read()
os.mkdir("mesa")
os.chdir("/opt/mesa")

print "Update apt sources"
os.popen("apt-get update").read()

print "Download mesa official sources"
os.popen("apt-get source mesa").read()

print "Save original folder name"
for file in os.listdir("/opt/mesa"):
	if os.path.isdir(file):
		orig_name = file

orig_path = "/opt/mesa/" + orig_name + "/"

print "Print original name"
print orig_name

print "Pull latest git changes"
os.chdir("/opt/mesa-git")
#os.popen("git pull").read()
#os.popen("git clone https://github.com/iXit/Mesa-3D mesa").read()
#os.popen("git clone git://anongit.freedesktop.org/mesa/mesa mesa").read()

print "Copy upstream files from git source directory"
os.popen("cp -r /opt/mesa-git /opt/mesa/mesa").read()

print "Get revision"
os.chdir("/opt/mesa/mesa")
git_version = os.popen("git rev-parse --short HEAD").read().rstrip()
git_date = os.popen("git show -s --date=short --format=%cd HEAD").read().rstrip()
print git_version

print "Read Mesa version from upstream sources"
upstream_version = os.popen("cat VERSION").read().rstrip()
print upstream_version

print "Move git mesa directory"
os.chdir("/opt/mesa")
new_name = "mesa-" + upstream_version + "-" + git_date + "-" + git_version + "-galliumnine"
new_path = "/opt/mesa/" + new_name + "/"
print new_path
os.rename("/opt/mesa/mesa", new_path)

print "Copy debian folder"
os.chdir("/opt/mesa")
os.popen("cp -rp " + orig_path + "debian" + " " + new_path + "debian").read()

print "Remove patches"
os.chdir(new_path + "debian/patches")
os.popen("rm *").read()
os.popen("touch series")

print "Update debian/control file"

f1 = open(new_path + "debian/control",     'r')
f2 = open(new_path + "debian/control.tmp", 'w')

swx11_block = 0

for line in f1:

	if swx11_block == 0:
		#Look for Package and swx11 in the same line
		if "Package" in line and "swx11" in line:
			#If inside swx11 block, do not write to new file until we see Package again
			swx11_block = 1

		else:
			#Look for llvm and libclang 3.8, replace with 3.9
			f2.write(line.replace('llvm-3.8-dev', 'llvm-3.9-dev').replace('libclang-3.8-dev', 'libclang-3.9-dev'))

	elif swx11_block == 1:
		if "Package" in line and not "swx11" in line:
			swx11_block = 0
			f2.write(line)

f1.close()
f2.close()

os.remove(new_path + "debian/control")
os.rename(new_path + "debian/control.tmp", new_path + "debian/control")

print "Update debian/rules file"

f1 = open(new_path + "debian/rules",     'r')
f2 = open(new_path + "debian/rules.tmp", 'w')

for line in f1:

	#Look for llvm and libclang 3.8, replace with 3.9
	f2.write(line.replace('llvm-config-3.8', 'llvm-config-3.9'))

	if "enable-va" in line:
		f2.write("	confflags_GALLIUM += --enable-nine\n")

f1.close()
f2.close()

os.remove(new_path + "debian/rules")
os.rename(new_path + "debian/rules.tmp", new_path + "debian/rules")

print "Add Gallium Nine include to mesa-common-dev"
f1 = open(new_path + "debian/mesa-common-dev.install.in", 'a')

f1.write("usr/lib/${DEB_HOST_MULTIARCH}/pkgconfig/d3d.pc\n")
f1.write("usr/include/GL/mesa_glinterop.h\n")
f1.write("/usr/include/d3dadapter/drm.h\n")
f1.write("usr/include/d3dadapter/d3dadapter9.h\n")
f1.write("usr/include/d3dadapter/present.h\n")

f1.close()

print "Add Gallium Nine shared object library files to libgl1-mesa-glx"
f1 = open(new_path + "debian/libgl1-mesa-glx.install.in", 'a')

f1.write("usr/lib/${DEB_HOST_MULTIARCH}/d3d/d3dadapter9.so\n")
f1.write("usr/lib/${DEB_HOST_MULTIARCH}/d3d/d3dadapter9.so.*\n")

f1.close()

print "Update changelog"
os.chdir(new_path)
os.popen("dch -d \"git commit " + git_version + "\"").read()

print "Install build dependencies"
os.system("mk-build-deps --tool \"apt-get --no-install-recommends -y\" --install " + new_path + "debian/control")

print "Begin building"
#os.system("dpkg-buildpackage -us -B -j24")

print "It probably had an error due to missing symbols.  Update the symbols files"
#os.system("python /opt/update-symbols.py")

print "Resume building"
#os.system("dpkg-buildpackage -us -B -j24 -nc")
