# ============================================================
# NMS_Tools Makefile — Fully Dynamic, Zero Maintenance
# Generates, installs, and packages man pages and tools.
# ============================================================

PREFIX ?= /usr/local
MANDIR ?= $(PREFIX)/share/man

MAN_SRC := $(wildcard man/*.md)
MAN_OUT_DIR := man/generated
MAN_OUT := $(patsubst man/%.md,$(MAN_OUT_DIR)/%,$(MAN_SRC))

.PHONY: man install-man uninstall-man clean rpm deb packages

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
# Clean generated man pages
# ------------------------------------------------------------
clean:
	@echo "Cleaning generated man pages..."
	@rm -rf $(MAN_OUT_DIR)

# ------------------------------------------------------------
# Preview suite man page with version injection
# ------------------------------------------------------------
preview-man:
	@echo "Previewing nms_tools.7 with version metadata..."
	@BASE_VERSION=$$(grep -m1 "^Version:" packaging/debian/control | awk '{print $$2}'); \
	DATESTAMP=$$(date +%Y%m%d); \
	GIT_HASH=$$(git rev-parse --short HEAD); \
	if [ "$${NIGHTLY:-0}" = "1" ]; then \
		VERSION="$${BASE_VERSION}+$$DATESTAMP.git$$GIT_HASH"; \
		BUILD_TYPE="Nightly"; \
	else \
		VERSION="$$BASE_VERSION"; \
		BUILD_TYPE="Standard"; \
	fi; \
	\
	rm -rf man/generated && mkdir -p man/generated; \
	for md in man/*.md; do \
		base=$${md##*/}; \
		name=$${base%.md}; \
		section=$${name##*.}; \
		out="man/generated/$${name}"; \
		pandoc -s -t man "$$md" -o "$$out"; \
	done; \
	\
	sed -i \
		-e "s/{{VERSION}}/$$VERSION/" \
		-e "s/{{BUILD_TYPE}}/$$BUILD_TYPE/" \
		-e "s/{{BUILD_DATE}}/$$DATESTAMP/" \
		-e "s/{{GIT_HASH}}/$$GIT_HASH/" \
		man/generated/nms_tools.7; \
	\
	man -l man/generated/nms_tools.7
