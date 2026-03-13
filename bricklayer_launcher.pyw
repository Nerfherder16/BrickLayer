"""
bricklayer_launcher.pyw — BrickLayer Windows Launcher

Double-click to open. Two tabs:
  New Session  — pick a project, open VSCode + launch Claude in Windows Terminal
  Resume       — pick a project with a saved session ID, resume that Claude session

Session flow:
  1. Select project → click Launch
  2. VSCode opens at autosearch/ root
  3. Windows Terminal opens with `claude --dangerously-skip-permissions`
  4. Starting prompt is auto-copied to clipboard — paste it into Claude
  5. After the session, save the session ID for future resumes
"""

import json
import shutil
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

AUTOSEARCH_ROOT = Path(__file__).parent
PROJECTS_DIR = AUTOSEARCH_ROOT / "projects"
CLAUDE_FLAGS = "--dangerously-skip-permissions"

NEW_SESSION_PROMPT = (
    "Working directory: {autosearch_root}\n\n"
    "You are running BrickLayer against: **{display_name}**\n"
    "Target git: {target_git}\n"
    "Target live service: {target_live_url}\n\n"
    "Read projects/{name}/prepare.md before doing anything else. "
    "Confirm the git boundary rule before proceeding.\n\n"
    "All findings stay in autosearch/projects/{name}/. "
    "Fix agents operate within the target git only. "
    "Cross-project changes go to autosearch/handoffs/ — never applied directly.\n\n"
    "Start by reading your memory, then explore the target before designing questions."
)


def load_projects() -> list[dict]:
    projects = []
    if not PROJECTS_DIR.exists():
        return projects
    for d in sorted(PROJECTS_DIR.iterdir()):
        cfg_path = d / "project.json"
        if d.is_dir() and cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                cfg["_dir"] = str(d)
                projects.append(cfg)
            except Exception as e:
                import sys
                print(f"Warning: could not load project from {cfg_path}: {e}", file=sys.stderr)
    return projects


def save_session_id(project_name: str, session_id: str) -> None:
    cfg_path = PROJECTS_DIR / project_name / "project.json"
    if not cfg_path.exists():
        return
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["claude_session_id"] = session_id.strip()
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def open_vscode(path: str) -> None:
    """Open VSCode at the given path if available."""
    code = shutil.which("code")
    if code:
        subprocess.Popen([code, path])


def open_claude_terminal(cwd: str, cmd: str) -> None:
    """Open Claude in Windows Terminal (preferred) or cmd fallback."""
    wt = shutil.which("wt")
    if wt:
        # Windows Terminal: new tab, cmd.exe, run command
        full = f'wt.exe new-tab --title "BrickLayer" -- cmd.exe /k "cd /d \\"{cwd}\\" && {cmd}"'
        subprocess.Popen(full, shell=True)
    else:
        # cmd.exe fallback
        full = f'start cmd.exe /k "cd /d \\"{cwd}\\" && {cmd}"'
        subprocess.Popen(full, shell=True)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BrickLayer Launcher")
        self.resizable(False, False)

        # Colors
        self.BG = "#1e1b2e"
        self.CARD = "#252236"
        self.ELEVATED = "#2d2a3e"
        self.ACCENT = "#38bdf8"
        self.TEXT = "#e5e7eb"
        self.MUTED = "#9ca3af"
        self.BTN_FG = "#0f0d1a"

        self.configure(bg=self.BG)
        # Style the Combobox dropdown listbox (native widget — must use option_add)
        self.option_add("*TCombobox*Listbox.background", self.CARD)
        self.option_add("*TCombobox*Listbox.foreground", self.TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", self.ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", self.BTN_FG)
        self.projects: list[dict] = []
        self._build_ui()
        self._refresh()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(
            "TCombobox",
            fieldbackground=self.CARD,
            background=self.CARD,
            foreground=self.TEXT,
            selectbackground=self.CARD,
            selectforeground=self.TEXT,
            arrowcolor=self.MUTED,
        )
        s.configure(
            "TNotebook",
            background=self.BG,
            borderwidth=0,
            tabmargins=[0, 0, 0, 0],
        )
        s.configure(
            "TNotebook.Tab",
            background=self.CARD,
            foreground=self.MUTED,
            padding=(14, 7),
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        s.map(
            "TNotebook.Tab",
            background=[("selected", self.ELEVATED)],
            foreground=[("selected", self.TEXT)],
        )

    def _btn(self, parent, text, command, primary=False, **kwargs):
        bg = self.ACCENT if primary else self.CARD
        fg = self.BTN_FG if primary else self.TEXT
        font_weight = "bold" if primary else "normal"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 10, font_weight),
            relief="flat",
            cursor="hand2",
            activebackground=self.ELEVATED,
            activeforeground=self.TEXT,
            **kwargs,
        )

    def _label(self, parent, text, size=9, fg=None, **kwargs):
        return tk.Label(
            parent,
            text=text,
            bg=self.BG,
            fg=fg or self.MUTED,
            font=("Segoe UI", size),
            **kwargs,
        )

    def _build_ui(self):
        self._style()
        PAD = 16

        # Header
        hdr = tk.Frame(self, bg=self.BG, padx=PAD, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⬡ BrickLayer", bg=self.BG, fg=self.ACCENT,
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  autoresearch launcher", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left", pady=2)

        tk.Frame(self, bg=self.ELEVATED, height=1).pack(fill="x")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", padx=PAD, pady=PAD)

        self._build_new_tab(nb)
        self._build_resume_tab(nb)
        self._build_projects_tab(nb)

        self.geometry("420x500")

    def _build_new_tab(self, nb):
        tab = tk.Frame(nb, bg=self.BG, padx=14, pady=14)
        nb.add(tab, text="  New Session  ")

        self._label(tab, "Project").grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.new_var = tk.StringVar()
        self.new_combo = ttk.Combobox(tab, textvariable=self.new_var,
                                      state="readonly", width=40)
        self.new_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.new_combo.bind("<<ComboboxSelected>>", lambda _: self._update_new_info())

        self.new_info = self._label(tab, "", wraplength=360, justify="left")
        self.new_info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._btn(tab, "Copy starting prompt to clipboard",
                  self._copy_prompt, padx=8, pady=4
                  ).grid(row=3, column=0, sticky="w", pady=(0, 10))

        self._btn(tab, "Launch  →  VSCode + Claude", self._launch_new,
                  primary=True, padx=16, pady=9
                  ).grid(row=4, column=0, columnspan=2, sticky="ew")

        sep = tk.Frame(tab, bg=self.ELEVATED, height=1)
        sep.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 8))

        self._label(tab, "Save session ID after first run:").grid(
            row=6, column=0, sticky="w", pady=(0, 3))
        row7 = tk.Frame(tab, bg=self.BG)
        row7.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.session_entry = tk.Entry(
            row7, bg=self.CARD, fg=self.TEXT, insertbackground=self.TEXT,
            relief="flat", font=("Segoe UI", 9), width=32)
        self.session_entry.pack(side="left")
        self._btn(row7, "Save", self._save_session, padx=10, pady=4
                  ).pack(side="left", padx=(6, 0))

    def _build_resume_tab(self, nb):
        tab = tk.Frame(nb, bg=self.BG, padx=14, pady=14)
        nb.add(tab, text="  Resume Session  ")

        self._label(tab, "Project (with saved session)").grid(
            row=0, column=0, sticky="w", pady=(0, 3))
        self.resume_var = tk.StringVar()
        self.resume_combo = ttk.Combobox(tab, textvariable=self.resume_var,
                                         state="readonly", width=40)
        self.resume_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.resume_combo.bind("<<ComboboxSelected>>", lambda _: self._update_resume_info())

        self.resume_info = self._label(tab, "", wraplength=360, justify="left")
        self.resume_info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self._btn(tab, "Resume  →  Claude session", self._launch_resume,
                  primary=True, padx=16, pady=9
                  ).grid(row=3, column=0, columnspan=2, sticky="ew")

        self._label(
            tab,
            "\nResume opens Claude with --resume {session_id}.\n"
            "No starting prompt needed — Claude remembers the context.",
            wraplength=360, justify="left"
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        sep = tk.Frame(tab, bg=self.ELEVATED, height=1)
        sep.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 8))

        self._btn(tab, "End Session  →  Run Retrospective", self._launch_retro,
                  padx=16, pady=9
                  ).grid(row=6, column=0, columnspan=2, sticky="ew")

        self._label(
            tab,
            "\nRuns structured reflection + improvement agent.\n"
            "BrickLayer improves itself from session learnings.",
            wraplength=360, justify="left"
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_projects_tab(self, nb):
        tab = tk.Frame(nb, bg=self.BG, padx=14, pady=14)
        nb.add(tab, text="  Projects  ")

        self.projects_text = tk.Text(
            tab, bg=self.CARD, fg=self.TEXT,
            font=("Consolas", 9), relief="flat",
            width=48, height=12, state="disabled", wrap="none",
        )
        self.projects_text.pack(fill="both")

        btns = tk.Frame(tab, bg=self.BG)
        btns.pack(anchor="w", pady=(8, 0))
        self._btn(btns, "Refresh", self._refresh, padx=10, pady=4).pack(side="left")
        self._btn(btns, "New Project (onboard.py)",
                  self._open_onboard, padx=10, pady=4).pack(side="left", padx=(6, 0))
        self._btn(btns, "Run Scout \u21bb", self._run_scout,
                  padx=10, pady=4).pack(side="left", padx=(6, 0))

        sep2 = tk.Frame(tab, bg=self.ELEVATED, height=1)
        sep2.pack(fill="x", pady=(10, 6))

        qrow = tk.Frame(tab, bg=self.BG)
        qrow.pack(anchor="w")
        self._label(qrow, "Run question:", fg=self.MUTED).pack(side="left")
        self.q_entry = tk.Entry(
            qrow, bg=self.CARD, fg=self.TEXT, insertbackground=self.TEXT,
            relief="flat", font=("Segoe UI", 9), width=10)
        self.q_entry.pack(side="left", padx=(6, 0))
        self.q_entry.insert(0, "Q1.1")
        self._btn(qrow, "Run", self._run_question, padx=10, pady=4).pack(side="left", padx=(6, 0))

    # ---- Data helpers ----

    def _refresh(self):
        self.projects = load_projects()
        names = [f"{p['display_name']}  ({p['name']})" for p in self.projects]
        self.new_combo["values"] = names
        if names:
            self.new_combo.current(0)
            self._update_new_info()

        resume_projects = [p for p in self.projects if p.get("claude_session_id")]
        resume_names = [f"{p['display_name']}  ({p['name']})" for p in resume_projects]
        self.resume_combo["values"] = resume_names
        if resume_names:
            self.resume_combo.current(0)
            self._update_resume_info()

        self.projects_text.config(state="normal")
        self.projects_text.delete("1.0", "end")
        for p in self.projects:
            sid = p.get("claude_session_id") or "—"
            self.projects_text.insert("end", f"  {p['name']}  ({p['display_name']})\n")
            self.projects_text.insert("end", f"    target:  {p['target_git']}\n")
            self.projects_text.insert("end", f"    session: {sid}\n\n")
        self.projects_text.config(state="disabled")

    def _selected_new(self) -> dict | None:
        i = self.new_combo.current()
        return self.projects[i] if 0 <= i < len(self.projects) else None

    def _selected_resume(self) -> dict | None:
        rp = [p for p in self.projects if p.get("claude_session_id")]
        i = self.resume_combo.current()
        return rp[i] if 0 <= i < len(rp) else None

    def _update_new_info(self):
        p = self._selected_new()
        if p:
            stack = ", ".join(p.get("stack", [])) or "—"
            live = p.get("target_live_url", "none")
            self.new_info.config(
                text=f"Target: {p['target_git']}\nStack:  {stack}\nLive:   {live}"
            )

    def _update_resume_info(self):
        p = self._selected_resume()
        if p:
            self.resume_info.config(
                text=f"Session: {p.get('claude_session_id')}\nTarget:  {p['target_git']}"
            )

    def _build_prompt(self, p: dict) -> str:
        return NEW_SESSION_PROMPT.format(
            autosearch_root=str(AUTOSEARCH_ROOT),
            display_name=p["display_name"],
            target_git=p["target_git"],
            target_live_url=p.get("target_live_url", "none"),
            name=p["name"],
        )

    def _copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    # ---- Actions ----

    def _copy_prompt(self):
        p = self._selected_new()
        if not p:
            messagebox.showwarning("No project", "Select a project first.")
            return
        self._copy_to_clipboard(self._build_prompt(p))
        messagebox.showinfo("Copied", "Starting prompt copied to clipboard.")

    def _launch_new(self):
        p = self._selected_new()
        if not p:
            messagebox.showwarning("No project", "Select a project first.")
            return

        # 1. Copy starting prompt to clipboard
        self._copy_to_clipboard(self._build_prompt(p))

        # 2. Open VSCode at autosearch root
        open_vscode(str(AUTOSEARCH_ROOT))

        # 3. Open Claude in Windows Terminal
        open_claude_terminal(
            cwd=str(AUTOSEARCH_ROOT),
            cmd=f"claude {CLAUDE_FLAGS}",
        )

        messagebox.showinfo(
            "Launched",
            f"VSCode opened at autosearch/\n"
            f"Claude launched in Windows Terminal.\n\n"
            f"Starting prompt is in your clipboard — paste it into Claude.\n\n"
            f"After the session, copy your session ID and save it in the New Session tab."
        )

    def _save_session(self):
        p = self._selected_new()
        sid = self.session_entry.get().strip()
        if not p:
            messagebox.showwarning("No project", "Select a project first.")
            return
        if not sid:
            messagebox.showwarning("No session ID", "Paste the session ID first.")
            return
        save_session_id(p["name"], sid)
        self.session_entry.delete(0, "end")
        self._refresh()
        messagebox.showinfo("Saved", f"Session ID saved for {p['display_name']}.")

    def _launch_resume(self):
        p = self._selected_resume()
        if not p:
            messagebox.showwarning("No session", "No project with a saved session ID.")
            return
        sid = p["claude_session_id"]
        open_vscode(str(AUTOSEARCH_ROOT))
        open_claude_terminal(
            cwd=str(AUTOSEARCH_ROOT),
            cmd=f"claude --resume {sid} {CLAUDE_FLAGS}",
        )

    def _launch_retro(self):
        p = self._selected_resume()
        if not p:
            messagebox.showwarning("No session", "No project with a saved session ID.")
            return
        open_claude_terminal(
            cwd=str(AUTOSEARCH_ROOT),
            cmd=f"python simulate.py --project {p['name']} --retro",
        )

    def _open_onboard(self):
        onboard = AUTOSEARCH_ROOT / "onboard.py"
        if onboard.exists():
            wt = shutil.which("wt")
            if wt:
                subprocess.Popen(
                    f'wt.exe new-tab -- python "{onboard}"', shell=True
                )
            else:
                subprocess.Popen(
                    f'start cmd.exe /k "python \\"{onboard}\\""', shell=True
                )
        else:
            messagebox.showerror("Not found", f"onboard.py not found at {onboard}")

    def _run_scout(self):
        p = self._selected_new()
        if not p:
            messagebox.showwarning("No project", "Select a project in New Session first.")
            return
        open_claude_terminal(
            cwd=str(AUTOSEARCH_ROOT),
            cmd=f"python simulate.py --project {p['name']} --scout",
        )

    def _run_question(self):
        p = self._selected_new()
        qid = self.q_entry.get().strip()
        if not p:
            messagebox.showwarning("No project", "Select a project in New Session first.")
            return
        if not qid:
            messagebox.showwarning("No question", "Enter a question ID (e.g. Q1.1).")
            return
        open_claude_terminal(
            cwd=str(AUTOSEARCH_ROOT),
            cmd=f"python simulate.py --project {p['name']} --question {qid}",
        )


def main():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    App().mainloop()


if __name__ == "__main__":
    main()
