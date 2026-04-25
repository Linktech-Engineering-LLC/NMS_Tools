# ============================================================
# NMS_Tools Makefile — Fully Dynamic, Zero Maintenance
# Man pages + Suite Build Pipeline
# ============================================================

PREFIX ?= /usr/local
MANDIR ?= $(PREFIX)/share/man

PYTHON := python3
TOOLS := tools
DIST := dist

MAN_SRC := $(wildcard man/*.md)
MAN_OUT_DIR := man/generated
MAN_OUT := $(patsubst man/%.md,$(MAN_OUT_DIR)/%,$(MAN_SRC))

.PHONY: man install-man uninstall-man clean rpm deb packages \
        validate vendor build-suite install-suite all

# ------------------------------------------------------------
# Generate groff man pages from Markdown
# ------------------------------------------------------------
man:
    @echo "Generating man pages..."
    @rm -rf $(MAN_OUT_DIR)
    @mkdir -p $(MAN_OUT_DIR)
    @for src in $(MAN_SRC); do \
        base=$${src##*/}; \
        name=$${base%.md}; \
        section=$${name##*.}; \
        out="$(MAN_OUT_DIR)/$${name}"; \
        echo "  $$src → $$out"; \
        pandoc "$$src" -s -t man -o "$$out"; \
    done

# ------------------------------------------------------------
# Install all generated man pages dynamically
# ------------------------------------------------------------
install-man: man
    @echo "Installing man pages to $(MANDIR)..."
    @install -d $(MANDIR)/man1
    @install -d $(MANDIR)/man7
    @for f in $(MAN_OUT_DIR)/*; do \
        section=$${f##*.}; \
        if [ "$$section" = "1" ]; then \
            install -m 644 "$$f" $(MANDIR)/man1/; \
        elif [ "$$section" = "7" ]; then \
            install -m 644 "$$f" $(MANDIR)/man7/; \
        fi; \
    done
    @echo "Updating man database..."
    @mandb 2>/dev/null || true

# ------------------------------------------------------------
# Uninstall all man pages dynamically
# ------------------------------------------------------------
uninstall-man:
    @echo "Removing installed man pages from $(MANDIR)..."
    @for f in $(MAN_OUT_DIR)/*; do \
        section=$${f##*.}; \
        name=$${f##*/}; \
        if [ "$$section" = "1" ]; then \
            rm -f $(MANDIR)/man1/$$name; \
        elif [ "$$section" = "7" ]; then \
            rm -f $(MANDIR)/man7/$$name; \
        fi; \
    done
    @echo "Updating man database..."
    @mandb 2>/dev/null || true

# ------------------------------------------------------------
# Suite Build Pipeline
# ------------------------------------------------------------
validate:
    $(PYTHON) $(TOOLS)/validate_env.py

vendor:
    $(PYTHON) $(TOOLS)/vendor_builder.py

build-suite:
    $(PYTHON) $(TOOLS)/build_suite.py

install-suite:
    bash $(TOOLS)/install.sh

# ------------------------------------------------------------
# Build RPM package (dynamic)
# ------------------------------------------------------------
rpm: man
    @echo "[NMS_Tools] Building RPM package..."
    @./packaging/build_rpm.sh

# ------------------------------------------------------------
# Build DEB package (dynamic)
# ------------------------------------------------------------
deb: man
    @echo "[NMS_Tools] Building DEB package..."
    @./packaging/build_deb.sh

# ------------------------------------------------------------
# Build both packages
# ------------------------------------------------------------
packages: rpm deb
    @echo "[NMS_Tools] All packages built."

# ------------------------------------------------------------
# Clean generated man pages + suite artifacts
# ------------------------------------------------------------
clean:
    @echo "Cleaning generated man pages and suite artifacts..."
    @rm -rf $(MAN_OUT_DIR)
    @rm -rf libs/
    @rm -rf $(DIST)/

# ------------------------------------------------------------
# Preview suite man page with version injection
# ------------------------------------------------------------
preview-man:
    @echo "Previewing nms_tools.7 with version metadata..."
# ------------------------------------------------------------
# Full build pipeline
# ------------------------------------------------------------
all: validate vendor build-suite man
    @echo "[NMS_Tools] Full build pipeline complete."
# ------------------------------------------------------------
# Release pipeline (requires bump type: major/minor/patch)
# ------------------------------------------------------------
release:
    @if [ -z "$(type)" ]; then \
        echo "ERROR: You must specify a bump type: make release type=patch"; \
        exit 1; \
    fi
    @echo "[release] Validating environment..."
    $(PYTHON) $(TOOLS)/validate_env.py

    @echo "[release] Bumping version ($(type))..."
    $(PYTHON) $(TOOLS)/bump_version.py $(type)

    @echo "[release] Rebuilding vendor libs..."
    $(PYTHON) $(TOOLS)/vendor_builder.py

    @echo "[release] Building suite package..."
    $(PYTHON) $(TOOLS)/build_suite.py

    @echo "[release] Committing version bump..."
    git add VERSION
    git commit -m "Release v$$(cat VERSION)"

    @echo "[release] Tagging release..."
    git tag v$$(cat VERSION)

    @echo "[release] Release v$$(cat VERSION) created."
    @echo "[release] Push with: git push && git push --tags"
