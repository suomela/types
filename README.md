Type and hapax accumulation curves
==================================

This is a tool for analysing textual diversity, richness, and
productivity in text corpora and other data sets.

For more information, see
http://users.ics.aalto.fi/suomela/types2/


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

See https://github.com/suomela/types-examples for examples.


Installing dependencies
-----------------------

### Ubuntu 15.04

Open a terminal and run:

    sudo apt-get install git python-matplotlib python-lxml sqlite3 libsqlite3-dev


### Ubuntu 12.04

Open a terminal and run:

    sudo apt-get install git python-matplotlib sqlite3 libsqlite3-dev


### Ubuntu 10.04

Open a terminal and run:

    sudo apt-get install git-core python-lxml python-matplotlib sqlite3 libsqlite3-dev


### OS X Lion and OS X Mountain Lion

These instructions should work on OS X 10.9:

  - Open Terminal.

  - Install Homebrew: http://brew.sh/

        ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
        brew doctor
        brew update

  - Run the following commands to install recent versions of *GCC*,
    *Python*, and the Python modules that we need:

        brew install python
        brew install freetype
        pip install --upgrade setuptools
        pip install --upgrade pip
        pip install numpy
        pip install matplotlib
        pip install lxml
        brew install gcc

---

Remarks:

  - Once you have followed the above instructions, `./config` should
    finish successfully. In particular, it should find the following
    tools:

        PYTHON = /usr/local/bin/python
        CC = /usr/local/bin/gcc-4.9

  - For cluster environments, you can also install *Gnu Parallel*:

        brew install parallel
        parallel --bibtex


### Windows 7

Download the Cygwin installation program (setup.exe): http://cygwin.com/

Run setup.exe. The default settings are usually fine:

  - "Install from Internet"
  - Root directory: C:\cygwin
  - Local Package Directory: for example, C:\cygwinpkg
  - "Direct Connection"
  - Select a mirror site that is near you
  - Do not select any packages yet
  - "Create icon on Desktop", "Add icon to Start Menu"

If everything goes fine, you should have a "Cygwin Terminal" icon on
your desktop.

Next, we will install some packages. Run setup.exe again.
It should remember all settings that you have selected so far;
just hit "next" until you get the "Select Packages" dialog.
Then select the latest versions of the following packages:

    git
    gcc4
    make
    python
    python-numpy
    pkg-config
    sqlite3
    wget
    libsqlite3-devel
    libxslt-devel
    libfreetype-devel
    libpng-devel

Next, open Cygwin Terminal.

Run `python --version` to find your Python version. Go to
http://pypi.python.org/pypi/setuptools and download and install
the right version of setuptools ("Python Egg"). For example, if your
Python version is 2.6, then you can use the following commands:

    wget http://pypi.python.org/packages/2.6/s/setuptools/setuptools-0.6c11-py2.6.egg
    sh setuptools-0.6c11-py2.6.egg

Once you have installed setuptools, you can use easy_install to install
the remaining Python modules that we need:

    easy_install lxml
    easy_install matplotlib

If all goes fine, you are now ready to follow the usual installation
procedure: use `git` to download the software, run `./config`, etc.
Just keep in mind that you must do everything in Cygwin Terminal.
However, once the software finishes, you can of course browse the
results with more user-friendly tools.

---

If you see any error messages that suggest "... try running rebaseall",
follow the instructions here: http://cygwin.wikia.com/wiki/Rebaseall

In brief, you will need do the following and try again:

  - Exit Cygwin terminal
  - Run C:\cygwin\bin\ash.exe
  - In ash.exe, enter the following commands:

        /bin/rebaseall
        exit

  - Re-open Cygwin terminal

In our experiments, we encountered this issue during the installation
of matplotlib on Windows XP, but not on Windows 7.


License
-------

You can distribute everything under the BSD 3-clause license:
http://opensource.org/licenses/BSD-3-Clause

See below for details.


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

Copyright (c) 2014, Jukka Suomela.

Enjoy, use at your own risk.

To contact the author, see http://users.ics.aalto.fi/suomela/

You can use any of the following licenses to distribute this software:

  - MIT license, http://opensource.org/licenses/MIT

  - BSD 2-clause license, http://opensource.org/licenses/BSD-2-Clause

  - BSD 3-clause license, http://opensource.org/licenses/BSD-3-Clause

The BSD 3-clause license might be most convenient, as it is the same
license under which SFMT is distributed.

For your convenience, here is the text of the MIT license.

----

Copyright (c) 2014 Jukka Suomela

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
