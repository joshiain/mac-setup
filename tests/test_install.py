#!/usr/bin/env python3
"""Remote entrypoint checks with temporary homes and no network or installs."""
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mac setup installer ")
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "commands.log"
        self.env = {
            "HOME": str(self.home),
            "PATH": str(self.bin) + ":/usr/bin:/bin:/usr/sbin:/sbin",
            "MOCK_LOG": str(self.log),
        }
        self.mock("brew", "#!/bin/bash\nexit 0\n")
        self.mock("xcode-select", "#!/bin/bash\nexit \"${MOCK_CLT_STATUS:-0}\"\n")
        self.mock("git", '''#!/bin/bash
set -eu
[ "$GIT_TERMINAL_PROMPT" = 0 ]
[ "$1" = -c ] && [ "$2" = credential.helper= ] && [ "$3" = clone ]
[ "$4" = --depth=1 ] && [ "$5" = --branch ] && [ "$6" = main ]
[ "$7" = https://github.com/joshiain/mac-setup.git ]
printf 'clone\\n' >> "$MOCK_LOG"
mkdir -p "$8"
[ "${MOCK_CLONE_STATUS:-0}" = 0 ] || exit 1
[ "${MOCK_MISSING_BOOTSTRAP:-0}" = 0 ] || exit 0
cat > "$8/bootstrap.sh" <<'SCRIPT'
#!/bin/bash
printf 'bootstrap cwd=%s\\n' "$PWD" >> "$MOCK_LOG"
printf 'arg=%s\\n' "$@" >> "$MOCK_LOG"
exit "${MOCK_BOOTSTRAP_STATUS:-0}"
SCRIPT
''')

    def tearDown(self):
        self.temp.cleanup()

    def mock(self, name, content):
        p = self.bin / name
        p.write_text(content)
        p.chmod(0o755)

    def run_installer(self, *args, success=True):
        # Match the README's bash -c invocation without downloading any code.
        p = subprocess.run(
            ["/bin/bash", "-c", (REPO / "install.sh").read_text(), "--", *args],
            env=self.env, cwd=self.root, capture_output=True, text=True, timeout=10,
        )
        if success:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(list(self.home.glob("dev/.mac-setup-download.*")), [])
        return p

    def test_default_downloads_then_previews_all(self):
        self.run_installer()
        self.assertEqual(self.log.read_text().splitlines(), [
            "clone", f"bootstrap cwd={self.home}/dev/mac-setup",
            "arg=--dry-run", "arg=--all",
        ])

    def test_explicit_apply_arguments_forwarded(self):
        self.run_installer("--apply", "--all")
        self.assertIn("arg=--apply\narg=--all\n", self.log.read_text())

    def test_existing_checkout_preserved_without_commands(self):
        repo = self.home / "dev/mac-setup"
        repo.mkdir(parents=True)
        original = repo / "local-work"
        original.write_text("uncommitted work")
        self.run_installer("--apply", "--all", success=False)
        self.assertEqual(original.read_text(), "uncommitted work")
        self.assertEqual(list(repo.iterdir()), [original])
        self.assertFalse(self.log.exists())

    def test_symlinked_destination_parent_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / "dev").symlink_to(outside)
        self.run_installer(success=False)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(self.log.exists())

    def test_failed_download_and_missing_bootstrap_cleaned_up(self):
        for flag in ["MOCK_CLONE_STATUS", "MOCK_MISSING_BOOTSTRAP"]:
            with self.subTest(flag=flag):
                self.env[flag] = "1"
                self.run_installer(success=False)
                self.assertFalse((self.home / "dev/mac-setup").exists())
                self.assertNotIn("bootstrap cwd=", self.log.read_text())
                del self.env[flag]

    def test_missing_prerequisites_stop_before_download(self):
        self.env["MOCK_CLT_STATUS"] = "1"
        self.run_installer(success=False)
        self.env["MOCK_CLT_STATUS"] = "0"
        (self.bin / "brew").unlink()
        self.run_installer(success=False)
        self.assertFalse(self.log.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_bootstrap_failure_keeps_checkout_for_retry(self):
        self.env["MOCK_BOOTSTRAP_STATUS"] = "42"
        p = self.run_installer("--apply", "--all", success=False)
        self.assertEqual(p.returncode, 42)
        self.assertTrue((self.home / "dev/mac-setup/bootstrap.sh").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
