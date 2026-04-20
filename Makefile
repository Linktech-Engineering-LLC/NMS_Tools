# ============================================================
# NMS_Tools Makefile
# Portable by default, distro-aware when DISTRO_MODE=1
# ============================================================

# Markdown man-page sources
MAN_MD := $(wildcard man/*.md)

# Output groff man pages (.1 and .7)
MAN_OUT := $(MAN_MD:.md=)

# Default man directory (portable mode)
PREFIX ?= /usr/local
MANDIR ?= $(PREFIX)/share/man

# Detect distro when DISTRO_MODE=1
ifeq ($(DISTRO_MODE),1)
    OS := $(shell . /etc/os-release && echo $$ID)

    # Debian / Ubuntu
    ifeq ($(OS),debian)
        MANDIR=/usr/share/man
    endif
    ifeq ($(OS),ubuntu)
        MANDIR=/usr/share/man
    endif

    # RHEL / Rocky / Alma / CentOS / Fedora
    ifeq ($(OS),rhel)
        MANDIR=/usr/share/man
    endif
    ifeq ($(OS),rocky)
        MANDIR=/usr/share/man
    endif
    ifeq ($(OS),almalinux)
        MANDIR=/usr/share/man
    endif
    ifeq ($(OS),centos)
        MANDIR=/usr/share/man
    endif
    ifeq ($(OS),fedora)
        MANDIR=/usr/share/man
    endif

    # openSUSE / SUSE
    ifeq ($(OS),opensuse)
        MANDIR=/usr/share/man
    endif
    ifeq ($(OS),sles)
        MANDIR=/usr/share/man
    endif

    # Arch Linux
    ifeq ($(OS),arch)
        MANDIR=/usr/share/man
    endif
endif

# ============================================================
# Targets
# ============================================================

.PHONY: man install-man uninstall-man clean

# Generate groff man pages from Markdown
man:
    @echo "Generating man pages..."
    @for src in $(MAN_MD); do \
        out=$${src%.md}; \
        echo "  $$src → $$out"; \
        pandoc "$$src" -s -t man -o "$$out"; \
    done

# Install man pages to correct system path
install-man: man
    @echo "Installing man pages to $(MANDIR)..."
    install -d $(MANDIR)/man1
    install -d $(MANDIR)/man7
    install -m 644 man/*.1 $(MANDIR)/man1/
    install -m 644 man/*.7 $(MANDIR)/man7/
    @echo "Updating man database..."
    @mandb 2>/dev/null || true

# Remove installed man pages
uninstall-man:
    @echo "Removing installed man pages from $(MANDIR)..."
    rm -f $(MANDIR)/man1/check_ports.1
    rm -f $(MANDIR)/man1/check_weather.1
    rm -f $(MANDIR)/man1/check_cert.1
    rm -f $(MANDIR)/man1/check_html.1
    rm -f $(MANDIR)/man1/check_interfaces.1
    rm -f $(MANDIR)/man7/nms_tools.7
    @echo "Updating man database..."
    @mandb 2>/dev/null || true

# Clean generated man pages (not the Markdown sources)
clean:
    @echo "Cleaning generated man pages..."
    rm -f man/*.1 man/*.7
