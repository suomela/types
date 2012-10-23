Type and hapax accumulation curves
==================================

This is a new version of the tool that is available at
http://www.cs.helsinki.fi/jukka.suomela/types/


Downloading and compilation
---------------------------

See the section *Installing dependencies* below for information on how
to set the compilation environment. Then open a terminal and run:

    git clone git://github.com/suomela/types.git
    cd types
    
    ./config
    make
    make check


Examples
--------

There is a sample data set available in the subdirectory `example`.
You can experiment with the data set as follows:

    cd example
    bin/types-run
    bin/types-plot

Now you can open the file `example/html/index.html` in your web browser
and explore the results.

The computation will take a while, typically *several hours* unless you
are using a high-performance computing cluster. If you are impatient,
you can try the following commands that will finish in a couple of
minutes (however, the results are of a much worse quality):

    cd example
    bin/types-run --citer=100000 --piter=100000
    bin/types-plot


Installing dependencies
-----------------------

### Ubuntu 12.04

Open a terminal and run:

    sudo apt-get install git python-matplotlib sqlite3 libsqlite3-dev


### Ubuntu 10.04

Open a terminal and run:

    sudo apt-get install git-core python-lxml python-matplotlib sqlite3 libsqlite3-dev


### OS X Lion and OS X Mountain Lion

These instructions should work on OS X 10.7.4 and OS X 10.8.1:

  - Open *App Store*. Find *Xcode*. Install. Close App Store.

  - Open *Xcode*. Select Preferences, Downloads, Components.
    Install *Command Line Tools*. Close Xcode.

  - Download and install XQuartz: https://xquartz.macosforge.org

  - Log out and log on again.

  - Open Terminal. To install *Homebrew*, run this command and
    follow the instructions:

        ruby <(curl -fsSkL raw.github.com/mxcl/homebrew/go)

  - Run the following commands to install recent versions of *GCC*,
    *Python*, and the Python modules that we need:

        brew doctor
        brew tap homebrew/dupes
        brew update
        brew upgrade
        brew install gcc
        brew install python
        brew install freetype
        brew install libpng
        brew link freetype
        brew link libpng
        /usr/local/share/python/pip install numpy
        /usr/local/share/python/pip install matplotlib
        /usr/local/share/python/pip install lxml

---

Remarks:

  - Once you have followed the above instructions, `./config` should
    finish successfully. In particular, it should find the following
    tools:

        PYTHON = /usr/local/bin/python
        CC = /usr/local/bin/gcc-4.7

  - For more information on Homebrew, see http://mxcl.github.com/homebrew/

  - The installation of GCC takes long (1-2 hours).

  - The `brew link` commands are required on OS X 10.7. On OS X 10.8
    they are not needed; you will just get a harmless warning.

  - The `pip install` comnads will print *lots* of warnings. This is
    normal. If you see the following messages after each installation,
    you should be fine:

        Successfully installed numpy
        Successfully installed matplotlib
        Successfully installed lxml

  - For cluster environments, you can also install *Gnu Parallel*:

        brew install parallel


License
-------

### SFMT and SFMTJump

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


### Other parts

Copyright (c) 2012, Jukka Suomela.

Enjoy, use at your own risk.

To contact the author, see http://www.cs.helsinki.fi/jukka.suomela/
