#!/usr/bin/env python3
"""Behavior checks confined to temporary HOME/repo copies and mocked CLIs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


def snapshot(root):
    result = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            result[rel] = ("link", os.readlink(p))
        elif p.is_file():
            result[rel] = ("file", p.read_bytes())
        else:
            result[rel] = ("directory",)
    return result


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mac setup test ")
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.repo = self.root / "repo with spaces"
        shutil.copytree(REPO, self.repo)
        self.bin = self.root / "mock-bin"
        self.bin.mkdir()
        self.log = self.root / "commands.log"
        self.env = {
            "HOME": str(self.home),
            "PATH": str(self.bin) + ":/usr/bin:/bin:/usr/sbin:/sbin",
            "MOCK_LOG": str(self.log),
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        self.mock("brew", """#!/bin/bash
printf '%s\\n' "$*" >> "$MOCK_LOG"
case "$1:$2" in
  --version:) exit 0 ;;
  bundle:install) exit "${MOCK_INSTALL_STATUS:-0}" ;;
  bundle:check) exit "${MOCK_CHECK_STATUS:-0}" ;;
  *) exit 99 ;;
esac
""")
        self.mock("xcode-select", """#!/bin/bash
[ "$1" = -p ] || exit 99
exit "${MOCK_CLT_STATUS:-0}"
""")
        self.mock("git", """#!/bin/bash
printf 'git %s\\n' "$*" >> "$MOCK_LOG"
[ "$1" = clone ] || exit 99
[ "$2" = --depth=1 ] || exit 99
[ "$3" = https://github.com/ohmyzsh/ohmyzsh.git ] || exit 99
mkdir -p "$4"
[ "${MOCK_CLONE_STATUS:-0}" = 0 ] || exit "$MOCK_CLONE_STATUS"
printf '# Mock Oh My Zsh\\n' > "$4/oh-my-zsh.sh"
""")

    def tearDown(self):
        self.temp.cleanup()

    def mock(self, name, text):
        p = self.bin / name
        p.write_text(text)
        p.chmod(0o755)

    def run_setup(self, *args, success=True):
        p = subprocess.run(
            ["/bin/bash", str(self.repo / "bootstrap.sh"), *args],
            env=self.env, text=True, capture_output=True, timeout=10,
        )
        if success:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def commands(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def write_home(self, name, data):
        p = self.home / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)
        return p

    def test_default_preview_no_writes_or_commands(self):
        before = snapshot(self.home)
        p = self.run_setup()
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])
        self.assertIn("Brewfile.cli", p.stdout)
        self.assertNotIn("Brewfile.optional", p.stdout)

    def test_all_preview_with_conflict_is_nonmutating(self):
        self.write_home(".config/mac-setup/gitconfig", "local override")
        before = snapshot(self.home)
        p = self.run_setup("--dry-run", "--all")
        self.assertIn("Would back up", p.stdout)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])

    def test_configs_only_apply_and_rerun(self):
        self.run_setup("--apply", "--dotfiles", "--editors")
        self.assertTrue((self.home / ".config/mac-setup/gitconfig").is_symlink())
        self.assertFalse((self.home / ".gitconfig").is_symlink())
        before = snapshot(self.home)
        self.run_setup("--apply", "--dotfiles", "--editors")
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])
        self.assertFalse((self.home / ".local/state/mac-setup/backups").exists())

    def test_preserve_existing_entrypoints(self):
        names = [".zshrc", ".gitconfig",
                 "Library/Application Support/com.mitchellh.ghostty/config",
                 "Library/Application Support/Code/User/settings.json",
                 "Library/Application Support/Cursor/User/settings.json",
                 ".config/zed/settings.json"]
        for name in names:
            self.write_home(name, "machine-local settings")
        self.run_setup("--apply", "--dotfiles", "--editors")
        for name in names:
            self.assertEqual((self.home / name).read_text(), "machine-local settings")

    def test_preserve_entrypoint_symlink_and_external_content(self):
        external = self.root / "external"
        external.write_text("original")
        (self.home / ".zshrc").symlink_to(external)
        self.run_setup("--apply", "--dotfiles")
        self.assertEqual(os.readlink(self.home / ".zshrc"), str(external))
        self.assertEqual(external.read_text(), "original")

    def test_preserve_dangling_entrypoint(self):
        (self.home / ".gitconfig").symlink_to(self.root / "absent")
        self.run_setup("--apply", "--dotfiles")
        self.assertTrue((self.home / ".gitconfig").is_symlink())

    def test_regular_managed_conflict_backup_and_rerun(self):
        self.write_home(".config/mac-setup/gitconfig", "original managed conflict")
        self.run_setup("--apply", "--dotfiles")
        backups = list((self.home / ".local/state/mac-setup/backups").glob("*/.config/mac-setup/gitconfig"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "original managed conflict")
        before = snapshot(self.home)
        self.run_setup("--apply", "--dotfiles")
        self.assertEqual(snapshot(self.home), before)

    def test_dangling_managed_link_backup(self):
        target = self.home / ".config/mac-setup/portable.zsh"
        target.parent.mkdir(parents=True)
        target.symlink_to(self.root / "absent")
        self.run_setup("--apply", "--dotfiles")
        backups = list((self.home / ".local/state/mac-setup/backups").glob("*/.config/mac-setup/portable.zsh"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(os.readlink(backups[0]), str(self.root / "absent"))
        self.assertEqual(os.readlink(target), str(self.repo / "dotfiles/zsh/portable.zsh"))

    def test_directory_conflict_backup(self):
        p = self.write_home(".config/mac-setup/ghostty.conf/child", "preserved child")
        self.run_setup("--apply", "--dotfiles")
        backups = list((self.home / ".local/state/mac-setup/backups").glob("*/.config/mac-setup/ghostty.conf/child"))
        self.assertEqual(backups[0].read_text(), "preserved child")
        self.assertTrue(p.parent.is_symlink())

    def test_symlink_parent_refused_before_package_commands(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.home / ".config").symlink_to(outside)
        before = snapshot(self.home)
        self.run_setup("--apply", "--all", success=False)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])
        self.assertEqual(list(outside.iterdir()), [])

    def test_nondirectory_parent_refused(self):
        self.write_home(".config", "not a directory")
        before = snapshot(self.home)
        self.run_setup("--apply", "--dotfiles", success=False)
        self.assertEqual(snapshot(self.home), before)

    def test_missing_brew_no_config_writes(self):
        (self.bin / "brew").unlink()
        before = snapshot(self.home)
        self.run_setup("--apply", success=False)
        self.assertEqual(snapshot(self.home), before)

    def test_missing_clt_no_config_writes(self):
        self.env["MOCK_CLT_STATUS"] = "1"
        before = snapshot(self.home)
        self.run_setup("--apply", success=False)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])

    def test_failed_install_stops_before_configs(self):
        self.env["MOCK_INSTALL_STATUS"] = "1"
        self.run_setup("--apply", "--all", success=False)
        self.assertEqual(snapshot(self.home), {})
        self.assertEqual(sum("bundle install" in x for x in self.commands()), 1)

    def test_all_apply_selects_exactly_three_manifests(self):
        self.run_setup("--apply", "--all")
        installs = [x for x in self.commands() if x.startswith("bundle install")]
        self.assertEqual(len(installs), 3)
        for name, line in zip(["Brewfile", "Brewfile.cli", "Brewfile.optional"], installs):
            self.assertIn("--file=" + str(self.repo / name), line)
            self.assertIn("--no-upgrade", line)
        self.assertTrue((self.home / ".zshrc").exists())
        self.assertTrue((self.home / ".oh-my-zsh/oh-my-zsh.sh").exists())

    def test_oh_my_zsh_apply_and_rerun_preserve_framework(self):
        self.run_setup("--apply", "--oh-my-zsh")
        installs = [x for x in self.commands() if x.startswith("bundle install")]
        self.assertEqual(len(installs), 1)
        self.assertIn("Brewfile.optional", installs[0])
        self.assertTrue((self.home / ".config/mac-setup/shell.zsh").is_symlink())
        self.write_home(".oh-my-zsh/custom/local.zsh", "local changes")
        before = snapshot(self.home)
        self.run_setup("--apply", "--oh-my-zsh")
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(sum(x.startswith("git clone") for x in self.commands()), 1)

    def test_oh_my_zsh_preserves_existing_zshrc(self):
        rc = self.write_home(".zshrc", "# my existing framework and plugins\n")
        self.run_setup("--apply", "--oh-my-zsh")
        self.assertEqual(rc.read_text(), "# my existing framework and plugins\n")

    def test_oh_my_zsh_clone_failure_leaves_no_configs_and_can_retry(self):
        self.env["MOCK_CLONE_STATUS"] = "1"
        self.run_setup("--apply", "--oh-my-zsh", success=False)
        self.assertEqual(snapshot(self.home), {})
        self.env["MOCK_CLONE_STATUS"] = "0"
        self.run_setup("--apply", "--oh-my-zsh")
        self.assertTrue((self.home / ".oh-my-zsh/oh-my-zsh.sh").exists())

    def test_oh_my_zsh_incomplete_directory_refused_before_packages(self):
        self.write_home(".oh-my-zsh/custom.zsh", "keep me")
        before = snapshot(self.home)
        self.run_setup("--apply", "--oh-my-zsh", success=False)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])

    def test_oh_my_zsh_symlink_refused_before_packages(self):
        (self.home / ".oh-my-zsh").symlink_to(self.root / "absent")
        before = snapshot(self.home)
        self.run_setup("--apply", "--oh-my-zsh", success=False)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), [])

    def test_oh_my_zsh_check_requires_framework_without_writes(self):
        p = self.run_setup("--check", "--oh-my-zsh", success=False)
        self.assertIn("Missing Oh My Zsh", p.stdout)
        self.assertEqual(snapshot(self.home), {})
        self.write_home(".oh-my-zsh/oh-my-zsh.sh", "# existing installation")
        before = snapshot(self.home)
        self.run_setup("--check", "--oh-my-zsh")
        self.assertEqual(snapshot(self.home), before)
        self.assertFalse(any(x.startswith("git ") for x in self.commands()))

    def test_dotfiles_only_does_not_install_shell_profile(self):
        self.run_setup("--apply", "--dotfiles")
        self.assertFalse((self.home / ".config/mac-setup/shell.zsh").exists())
        self.assertFalse((self.home / ".oh-my-zsh").exists())
        self.assertEqual(self.commands(), [])

    def run_zsh(self, script, interactive=True):
        return subprocess.run(
            ["/bin/zsh", "-d", "-f", *( ["-i"] if interactive else []), "-c", script],
            env={**self.env, "TERM": "xterm-256color"},
            text=True, capture_output=True, timeout=10,
        )

    def test_shell_profile_load_order_bindings_and_local_overrides(self):
        self.run_setup("--apply", "--oh-my-zsh")
        self.env["HOMEBREW_PREFIX"] = str(self.home / "brew")
        self.write_home(".oh-my-zsh/oh-my-zsh.sh", "events+=(omz); PROMPT=default\n")
        self.mock("fzf", "#!/bin/sh\n[ \"$1\" = --zsh ] || exit 99\nprintf 'events+=(fzf)\\n'\n")
        self.mock("zoxide", "#!/bin/sh\n[ \"$*\" = 'init zsh' ] || exit 99\nprintf 'events+=(zoxide)\\n'\n")
        for path, content in {
            "opt/fzf-tab/share/fzf-tab/fzf-tab.zsh": "events+=(tab)",
            "share/zsh-autosuggestions/zsh-autosuggestions.zsh":
                "events+=(suggestions); autosuggest-accept() { :; }; zle -N autosuggest-accept",
            "share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh": "events+=(highlighting)",
        }.items():
            self.write_home("brew/" + path, content + "\n")
        self.write_home(".zshrc.local", "events+=(local); PROMPT=local\n")
        p = self.run_zsh('''typeset -a events
source "$HOME/.zshrc"
source "$HOME/.config/mac-setup/shell.zsh"
print -r -- "${(j:,:)events}"
print -r -- "$PROMPT|$ZSH_THEME|$plugins|$HISTSIZE|$SAVEHIST"
bindkey '^F'
[[ -o sharehistory && -o histignorespace ]]
''')
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stderr, "")
        self.assertIn("omz,fzf,tab,zoxide,suggestions,local,highlighting", p.stdout)
        self.assertIn("local|robbyrussell|git|50000|50000", p.stdout)
        self.assertIn('"^F" autosuggest-accept', p.stdout)

    def test_shell_profile_without_optional_binaries(self):
        self.run_setup("--apply", "--oh-my-zsh")
        self.env["HOMEBREW_PREFIX"] = str(self.home / "empty-brew")
        p = self.run_zsh('source "$HOME/.zshrc"; print shell-ready')
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stderr, "")
        self.assertIn("shell-ready", p.stdout)

    def test_shell_profile_noninteractive_does_nothing(self):
        self.run_setup("--apply", "--oh-my-zsh")
        before = snapshot(self.home)
        commands = self.commands()
        p = self.run_zsh('source "$HOME/.config/mac-setup/shell.zsh"', interactive=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(self.commands(), commands)

    def test_check_is_readonly_and_collects_failures(self):
        self.env["MOCK_CHECK_STATUS"] = "1"
        before = snapshot(self.home)
        self.run_setup("--check", "--all", success=False)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(sum(x.startswith("bundle check") for x in self.commands()), 3)
        self.assertFalse(any("install" in x for x in self.commands()))

    def test_configs_only_check_needs_no_brew(self):
        (self.bin / "brew").unlink()
        self.run_setup("--check", "--dotfiles")
        self.assertEqual(snapshot(self.home), {})

    def test_invalid_modes_and_options_do_nothing(self):
        for args in [("--apply", "--dry-run"), ("--invalid",)]:
            self.run_setup(*args, success=False)
        self.assertEqual(snapshot(self.home), {})
        self.assertEqual(self.commands(), [])

    def test_missing_template_preflight_does_nothing(self):
        (self.repo / "dotfiles/zsh/portable.zsh").unlink()
        self.run_setup("--apply", "--all", success=False)
        self.assertEqual(snapshot(self.home), {})
        self.assertEqual(self.commands(), [])

    def test_existing_ghostty_xdg_preserved(self):
        self.write_home(".config/ghostty/config.ghostty", "local Ghostty")
        self.run_setup("--apply", "--dotfiles")
        self.assertFalse((self.home / "Library/Application Support/com.mitchellh.ghostty/config").exists())
        self.assertEqual((self.home / ".config/ghostty/config.ghostty").read_text(), "local Ghostty")

    def test_git_local_override_precedence(self):
        self.run_setup("--apply", "--dotfiles")
        self.write_home(".gitconfig.local", "\n".join(["[init]", " defaultBranch = local-branch", "[fetch]", " prune = false", ""]))
        for key, expected in [("init.defaultBranch", "local-branch"), ("fetch.prune", "false")]:
            p = subprocess.run(["/usr/bin/git", "config", "--global", "--includes", "--get", key],
                               env=self.env, text=True, capture_output=True, check=True)
            self.assertEqual(p.stdout.strip(), expected)

    def test_ghostty_relative_include_and_editor_json(self):
        self.run_setup("--apply", "--dotfiles", "--editors")
        config = self.home / "Library/Application Support/com.mitchellh.ghostty/config"
        include = config.parent / "../../../.config/mac-setup/ghostty.conf"
        self.assertEqual(include.read_text(), (self.repo / "dotfiles/ghostty/portable.conf").read_text())
        for product in ["Code", "Cursor"]:
            value = json.loads((self.home / f"Library/Application Support/{product}/User/settings.json").read_text())
            self.assertTrue(value["editor.formatOnSave"])
        zed = json.loads((self.home / ".config/zed/settings.json").read_text())
        self.assertEqual(zed["auto_install_extensions"], {
            "catppuccin-icons": True, "csv": True, "dockerfile": True,
            "html": True, "rose-pine-theme": True, "svelte": True, "toml": True,
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
