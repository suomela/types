Type and hapax accumulation curves
==================================

This is a new version of the tool that is available at
http://www.cs.helsinki.fi/jukka.suomela/types/


Compilation
===========

Open a terminal and run:

    ./config
    make
    make check


Installing Dependencies
=======================

OS X 10.8.1
-----------

Install Xcode command line tools:

- Open *App Store*. Find *Xcode*. Install. Close App Store.

- Open *Xcode*. Select Preferences, Downloads, Components.
  Install *Command Line Tools*. Close Xcode.

- Open Terminal. Make sure that everything looks good:

        gcc --version


Install Homebrew:

- Open Terminal. Run:

        ruby <(curl -fsSkL raw.github.com/mxcl/homebrew/go)
        brew doctor

- See http://mxcl.github.com/homebrew/ for more details.


Install a recent version of GCC:

- Open Terminal. Run:
    
        brew tap homebrew/dupes
        brew install gcc
    
- Make sure that everything looks good:
    
        gcc-4.7 --version


Install a recent version of Python:

- Download and install XQuartz: https://xquartz.macosforge.org

- Log out and log on again.

- Open Terminal. Run:
    
        brew install python

- Make sure that everything looks good:
    
        /usr/local/bin/python --version


Install the required Python modules and their dependencies:

- Open Terminal. Run:
    
        brew install freetype
        brew install libpng
        /usr/local/share/python/pip install numpy
        /usr/local/share/python/pip install matplotlib
        /usr/local/share/python/pip install lxml


Now `./config` should be happy. In particular, it should find the following
tools:

    PYTHON = /usr/local/bin/python
    CC = /usr/local/bin/gcc-4.7


For cluster environments, you can also install *Gnu Parallel*:

    brew install parallel


License
=======

SFMT and SFMTJump
-----------------

Copyright (c) 2006,2007 Mutsuo Saito, Makoto Matsumoto and Hiroshima
University.
Copyright (c) 2012 Mutsuo Saito, Makoto Matsumoto, Hiroshima University
and The University of Tokyo.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
    * Neither the names of Hiroshima University, The University of
      Tokyo nor the names of its contributors may be used to endorse
      or promote products derived from this software without specific
      prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Other parts
-----------

Copyright (c) 2012, Jukka Suomela.

Enjoy, use at your own risk.
