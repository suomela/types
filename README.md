types2: Type and hapax accumulation curves
==========================================

This is a tool for analysing textual diversity, richness, and
productivity in text corpora and other data sets.

For more information, see:

  - http://users.ics.aalto.fi/suomela/types2/
  - http://users.ics.aalto.fi/suomela/types2-d2e/


Downloading and compilation
---------------------------

See the section *Installing dependencies* below for information on how
to set the compilation environment. Then open a terminal and run:

    git clone git://github.com/suomela/types.git
    cd types

    ./config
    make
    make check


Workflow
--------

  - Create an empty database at `db/types.sqlite`
  - Populate the database with your input data
  - Run `bin/types-run` to perform data analysis
  - Run `bin/types-web` to create the web user interface
  - Open `web/index.html` in your web browser

You will find the database template in `template/types.sqlite`.
You can simply copy it to `db/types.sqlite` to get started.


Examples
--------

See https://github.com/suomela/types-examples for examples.


Installing dependencies
-----------------------

You will need:

  - Linux or OS X
  - a modern C compiler (GCC or Clang)
  - Python 2
  - SQLite 3


### OS X 10.11

First, make sure you have installed the command line tools:

    xcode-select --install

Then install Homebrew as usual, and make sure it is up-to-date:

    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew update

Then install GCC:

    brew install gcc


### Ubuntu Linux 15.04

You will probably already have Python and GCC installed, and you will
just need to install SQLite library and development tools:

    sudo apt-get install sqlite3 libsqlite3-dev


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


### D3.js

Available at http://d3js.org/

Copyright 2015 Mike Bostock.

Released under BSD license:
http://opensource.org/licenses/BSD-3-Clause


### Other parts

Copyright (c) 2016 Jukka Suomela.

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

Copyright (c) 2016 Jukka Suomela.

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
