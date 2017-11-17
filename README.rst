==========
Basic Info
==========

This is mainly for fixes, workarounds, or development/testing (and quite
a few LTO hacks of different kinds).  New-ish stuff includes dev-ada/
updates to use system-gcc instead of gnat-gpl (requires `ada-overlay`_ to
get Ada language support via USE=ada).

.. _ada-overlay: https://github.com/sarnold/ada-overlay

The master branch is intended to contain working (as in buildable) 
ebuilds, while unfinished or otherwise non-working ebuilds are now 
on the wip branch (not shown below).

You can (optionally) add this overlay with layman::

  $ layman -f -a nerdboy -o https://raw.github.com/sarnold/portage-overlay/master/configs/layman.xml

Latest (sort of)
================

Other than Ada tools for that shiny new FOSS compiler (and more LTO fixes) the
latest new-ish "thing" are the IMX etnaviv drivers, plus DRM support and the
xf86-video-armada drivers.  Yay for FOSS GPU acceleration and an actual X
desktop on most iMX6 machines (eg, wandboard, udoo, nitrogen6x, and cubox).

Also, check out the new `Gentoo wiki page`_ for the amr64 espressobin board.

.. _Gentoo wiki page: https://wiki.gentoo.org/wiki/ESPRESSOBin
