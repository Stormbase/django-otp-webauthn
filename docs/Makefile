# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
SPELLING_CONFIG = spellingcheck.yaml

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "Additional spelling targets:"
	@echo "  install-spelling-deps  Install pyspelling and aspell dependencies"
	@echo "  run                    Build docs and run pyspelling"
	@echo "  spelling               Run pyspelling on existing build"

.PHONY: help Makefile install-spelling-deps spelling run

# Check if required dependencies are installed, install if missing
check-spelling-deps:
	@echo "Checking for required spelling dependencies..."
	@if ! command -v aspell >/dev/null 2>&1; then \
		echo "aspell is not installed. Installing dependencies..."; \
		$(MAKE) install-spelling-deps; \
	elif ! python3 -c "import pyspelling" 2>/dev/null; then \
		echo "pyspelling is not installed. Installing dependencies..."; \
		$(MAKE) install-spelling-deps; \
	else \
		echo "All spelling dependencies are installed."; \
	fi

# Install spelling dependencies
install-spelling-deps:
	@echo "Installing spelling dependencies..."
	@echo "Detecting operating system..."
	@if command -v apt-get >/dev/null 2>&1; then \
		echo "Detected Debian/Ubuntu system"; \
		echo "Installing aspell and aspell-en..."; \
		sudo apt-get update && sudo apt-get install -y aspell aspell-en; \
	elif command -v yum >/dev/null 2>&1; then \
		echo "Detected RHEL/CentOS system"; \
		echo "Installing aspell and aspell-en..."; \
		sudo yum install -y aspell aspell-en; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "Detected Fedora system"; \
		echo "Installing aspell and aspell-en..."; \
		sudo dnf install -y aspell aspell-en; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "Detected Arch Linux system"; \
		echo "Installing aspell and aspell-en..."; \
		sudo pacman -S --noconfirm aspell aspell-en; \
	elif [ "$$(uname)" = "Darwin" ]; then \
		echo "Detected macOS system"; \
		if command -v brew >/dev/null 2>&1; then \
			echo "Found Homebrew, installing aspell..."; \
			brew install aspell; \
		elif command -v port >/dev/null 2>&1; then \
			echo "Found MacPorts, installing aspell..."; \
			sudo port install aspell aspell-dict-en; \
		else \
			echo "Neither Homebrew nor MacPorts found."; \
			echo "Please install aspell manually:"; \
			echo "  - Install Homebrew: https://brew.sh"; \
			echo "  - Then run: brew install aspell"; \
			echo "  - Or install MacPorts: https://www.macports.org"; \
			echo "  - Then run: sudo port install aspell aspell-dict-en"; \
			exit 1; \
		fi \
	else \
		echo "Could not detect package manager."; \
		echo "Please manually install aspell and aspell-en for your system."; \
		echo "Common package names: aspell, aspell-en"; \
		exit 1; \
	fi
	@echo "Installing pyspelling via pip..."
	@python3 -m pip install pyspelling
	@echo "Spelling dependencies installed successfully!"
	@echo "You can now run 'make run' to build docs and check spelling."

# Check dependencies, install if needed, build HTML documentation, run pyspelling, then serve
run: check-spelling-deps
	@echo "Building HTML documentation..."
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Running spelling check..."
	@if [ ! -f "$(SPELLING_CONFIG)" ]; then \
		echo "Error: Spelling config file '$(SPELLING_CONFIG)' not found."; \
		exit 1; \
	fi
	pyspelling -c $(SPELLING_CONFIG)
	@echo "Press Ctrl+C to stop the server"
	sphinx-autobuild -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Run pyspelling on existing build
spelling: check-spelling-deps
	@echo "Running pyspelling with config: $(SPELLING_CONFIG)"
	@if [ ! -f "$(SPELLING_CONFIG)" ]; then \
		echo "Error: Spelling config file '$(SPELLING_CONFIG)' not found."; \
		exit 1; \
	fi
	@if [ ! -d "$(BUILDDIR)/html" ]; then \
		echo "Error: HTML build directory '$(BUILDDIR)/html' not found."; \
		echo "Please run 'make html' first to build the documentation."; \
		exit 1; \
	fi
	pyspelling -c $(SPELLING_CONFIG) -j 8

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
