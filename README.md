Type and hapax accumulation curves
==================================


Compilation
===========

Open Terminal and run:

	./config
	make
	make check


Installing Dependencies
=======================

OS X 10.8.1
-----------

1. Install *Xcode command line tools*:

    - Open *App Store*. Find *Xcode*. Install. Close App Store.
    
    - Open *Xcode*. Select Preferences, Downloads, Components. Install *Command Line Tools*. Close Xcode.
    
    - Open Terminal. Make sure that everything looks good:

        gcc --version

2. Install *Homebrew*:

    - Open Terminal. Run:
    
        ruby <(curl -fsSkL raw.github.com/mxcl/homebrew/go)
        brew doctor

    - See http://mxcl.github.com/homebrew/ for more details.

3. Install a recent version of *GCC*:

    - Open Terminal. Run:
    
        brew tap homebrew/dupes
        brew install gcc
	
	- Make sure that everything looks good:
	
		gcc-4.7 --version

4. Install a recent version of *Python*:

	- Download and install XQuartz: https://xquartz.macosforge.org

	- Log out and log on again.

    - Open Terminal. Run:
    
		brew install python

	- Make sure that everything looks good:
	
		/usr/local/bin/python --version

5. Install the required Python modules and their dependencies:

    - Open Terminal. Run:
    
		brew install freetype
		brew install libpng
		/usr/local/share/python/pip install numpy
		/usr/local/share/python/pip install matplotlib
		/usr/local/share/python/pip install lxml

Now `./config` should be happy. In particular, it should find the following tools:

	PYTHON = /usr/local/bin/python
	CC = /usr/local/bin/gcc-4.7

For cluster environments, you can also install *Gnu Parallel*:

	brew install parallel
