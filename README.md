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

There are sample data set available in the following subdirectories:

    example1
    example2
    example3

You can experiment with the data sets as follows:

    cd example1
    bin/types-run
    bin/types-plot
    cd ..

Then open following file in your web browser:

    example1/html/index.html

The output should be similar to these pages:

  - http://users.ics.aalto.fi/suomela/types2/example1/
  - http://users.ics.aalto.fi/suomela/types2/example2/
  - http://users.ics.aalto.fi/suomela/types2/example3/

The computation will take a while, typically *several hours* unless you
are using a high-performance computing cluster. If you are impatient,
you can try the following commands that will finish in a couple of
minutes (however, the results are of a much worse quality):

    cd example1
    bin/types-run --citer=100000 --piter=100000
    bin/types-plot
    cd ..


Installing dependencies
-----------------------

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

        brew tap homebrew/versions
        brew install gcc48
        brew link freetype
        brew link libpng

---

Remarks:

  - Once you have followed the above instructions, `./config` should
    finish successfully. In particular, it should find the following
    tools:

        PYTHON = /usr/local/bin/python
        CC = /usr/bin/gcc

  - The `pip install` commands will print *lots* of warnings. This is
    normal. If you see the following messages after each installation,
    you should be fine:

        Successfully installed numpy
        Successfully installed matplotlib
        Successfully installed lxml

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


### Example 1

Sample data by Tanja Säily.

Derived from *CEEC*, the Corpus of Early English Correspondence:
http://www.helsinki.fi/varieng/CoRD/corpora/CEEC/

To contact the author, see
http://www.helsinki.fi/varieng/people/varieng_saily.html


### Example 2

Sample data derived from the *DBLP Computer Science Bibliography*:
http://www.informatik.uni-trier.de/~ley/db/
(source data timestamp 2012-10-29, downloaded 2012-10-30)

DBLP is Copyright (c) 1993-2011 by Michael Ley (University of Trier,
Informatik) and Schloss Dagstuhl - Leibniz-Zentrum für Informatik GmbH.

DBLP data is released under the ODC-BY 1.0 license:
http://opendatacommons.org/licenses/by/summary/


### Example 3

Sample data derived from the following Stack Exchange sites:

  - http://english.stackexchange.com/  (English Language and Usage)
  - http://math.stackexchange.com/     (Mathematics)
  - http://cstheory.stackexchange.com/ (Theoretical Computer Science)
  - http://physics.stackexchange.com/  (Physics)

The data is extracted using the StackExchange Data Explorer:
http://data.stackexchange.com/
(source data timestamp 2012-06-27, downloaded 2012-11-06)

The data is licensed under cc-wiki with attribution required:
http://creativecommons.org/licenses/by-sa/3.0/


### Other parts

Copyright (c) 2014, Jukka Suomela.

Enjoy, use at your own risk.

To contact the author, see http://users.ics.aalto.fi/suomela/
