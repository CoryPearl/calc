import math
import re
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

try:
    import sympy as sp
except ImportError:
    sp = None


class SciCalculatorApp(tk.Tk):
    """
    Dark-themed scientific calculator with:
    - Scrollable history pane (top)
    - Single-line input bar (bottom)
    - Support for scientific functions, (), [], and basic operators
    - Special syntaxes:
        * sqrt(x)      -> √x
        * sin, cos, tan, asin, acos, atan, log, ln, exp, etc.
        * int[a,b] f(x)  -> ∫_a^b f(x) dx (definite integral)
        * der f(x)       -> d/dx f(x)
        * der[y] f(y)    -> d/dy f(y)
    """

    def __init__(self):
        super().__init__()
        self.title("Calc (short for Calculator btw)")
        self.configure(bg="#121212")
        # Taller than wide (20px wider)
        self.geometry("360x540")
        self.minsize(320, 480)

        # App icon (transparent PNG logo)
        try:
            import os
            _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            _icon_path = os.path.join(_project_root, "assets", "logo.png")
            if os.path.exists(_icon_path):
                self._icon_image = tk.PhotoImage(file=_icon_path)
                self.iconphoto(True, self._icon_image)
        except Exception:  # noqa: BLE001
            pass

        # Single math symbol variable (default x)
        self.sym_x = sp.symbols("x") if sp is not None else None
        self.last_result = None
        self.input_history = []
        self.history_index = None

        # Font metrics for full-width divider lines
        self.history_font = tkfont.Font(family="SF Mono", size=12)

        self._build_style()
        self._build_layout()
        self._bind_events()
        self.after(0, self._show_startup_hint)

    # ---------- UI ----------
    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Dark.TFrame",
            background="#121212",
        )
        style.configure(
            "Dark.TEntry",
            fieldbackground="#1E1E1E",
            foreground="#FFFFFF",
            borderwidth=0,
            padding=6,
            insertcolor="#FFFFFF",
        )
        style.configure(
            "History.TFrame",
            background="#121212",
        )

    def _build_layout(self):
        root_frame = ttk.Frame(self, style="Dark.TFrame", padding=10)
        root_frame.pack(fill="both", expand=True)

        # History (top)
        history_frame = ttk.Frame(root_frame, style="History.TFrame")
        history_frame.pack(fill="both", expand=True, side="top")

        # History text: no visible scrollbars; soft wrap instead of horizontal scrolling
        self.history_text = tk.Text(
            history_frame,
            bg="#121212",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            bd=0,
            highlightthickness=0,
            wrap="word",  # wrap long lines; no horizontal scrolling
            state="disabled",
            font=self.history_font,
        )
        self.history_text.pack(fill="both", expand=True)


        # Input (bottom)
        input_frame = ttk.Frame(root_frame, style="Dark.TFrame")
        input_frame.pack(fill="x", side="bottom", pady=(10, 0))

        self.input_var = tk.StringVar()
        # Use tk.Entry so we can fully control the focus/outline (no blue ring)
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg="#1E1E1E",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("SF Mono", 13),
        )
        self.input_entry.pack(side="left", fill="x", expand=True)

        # Tag styles for history
        self.history_text.tag_configure("expr", foreground="#FFFFFF")
        self.history_text.tag_configure("result", foreground="#8BE9FD")
        self.history_text.tag_configure("error", foreground="#FF5555")
        self.history_text.tag_configure("symbol", foreground="#FFB86C")
        self.history_text.tag_configure("divider", foreground="#333333")
        self.history_text.tag_configure("hint", foreground="#777777")

    def _result_display_to_input(self, s: str) -> str:
        """Convert displayed result text back to valid input format (e.g. ² -> **2)."""
        s = s.strip()
        s = s.replace("²", "**2").replace("³", "**3")
        return s

    def _bind_events(self):
        self.input_entry.bind("<Return>", self._on_enter)
        self.history_text.bind("<Button-1>", self._on_history_click)
        self.history_text.bind("<Motion>", self._on_history_motion)
        self.input_entry.bind("<Shift-Return>", self._insert_newline_literal)
        self.input_entry.bind("<Up>", self._history_prev)
        self.input_entry.bind("<Down>", self._history_next)
        self.bind("<Control-l>", self._clear_history)

        # Focus entry on start and when window appears
        self.after(100, lambda: self.input_entry.focus_force())
        self.bind("<Map>", lambda event: self.input_entry.focus_force())

    # ---------- Event handlers ----------
    def _insert_newline_literal(self, event):
        # Prevent adding an actual newline in single-line entry
        return "break"

    def _clear_history(self, event=None):
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        self.history_text.configure(state="disabled")
        return "break"

    def _handle_history_command(self, cmd: str):
        """save / load / export latex / export txt for history."""
        import os

        base_dir = os.getcwd()
        txt_path = os.path.join(base_dir, "history.txt")
        latex_path = os.path.join(base_dir, "history.tex")

        if cmd == "save":
            content = self.history_text.get("1.0", "end-1c")
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._append_history("save", f"History saved to {txt_path}", is_error=False)
            except Exception as exc:  # noqa: BLE001
                self._append_history("save", f"Failed to save history: {exc}", is_error=True)
            return

        if cmd == "load":
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.history_text.configure(state="normal")
                self.history_text.delete("1.0", "end")
                self.history_text.insert("end", content)
                self.history_text.configure(state="disabled")
                self._append_history("load", f"History loaded from {txt_path}", is_error=False)
            except Exception as exc:  # noqa: BLE001
                self._append_history("load", f"Failed to load history: {exc}", is_error=True)
            return

        if cmd == "export latex":
            content = self.history_text.get("1.0", "end-1c")
            try:
                with open(latex_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._append_history("export latex", f"History exported to {latex_path}", is_error=False)
            except Exception as exc:  # noqa: BLE001
                self._append_history("export latex", f"Failed to export LaTeX: {exc}", is_error=True)
            return

        if cmd == "export txt":
            content = self.history_text.get("1.0", "end-1c")
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._append_history("export txt", f"History exported to {txt_path}", is_error=False)
            except Exception as exc:  # noqa: BLE001
                self._append_history("export txt", f"Failed to export text: {exc}", is_error=True)
            return

    def _on_enter(self, event=None):
        expr_raw = self.input_var.get().strip()
        if not expr_raw:
            return "break"

        lowered = expr_raw.lower()

        # Inline help command (with optional section, e.g. "help calc", "help all")
        if lowered in {"help", "?", "h"} or lowered.startswith("help "):
            self.input_var.set("")
            parts = lowered.split(maxsplit=1)
            section = parts[1] if len(parts) > 1 else None
            if section and section.strip().lower() == "all":
                self._show_help_all()
            else:
                self._show_help(section)
            return "break"

        # Clear history via command
        if lowered in {"clear", "clear output", "clearoutputs", "clearhistory"}:
            self.input_var.set("")
            self._clear_history()
            return "break"

        # Clear user variables
        if lowered == "clearvars":
            self.input_var.set("")
            self.user_vars = {}
            self.last_result = None
            self._append_history("clearvars", "Variables cleared.", is_error=False)
            return "break"

        # Save / load / export history
        if lowered in {"save", "load", "export latex", "export txt"}:
            self.input_var.set("")
            self._handle_history_command(lowered)
            return "break"

        # Simple variable assignment: a = expression
        if "=" in expr_raw and not lowered.startswith("zeros"):
            name_part, value_part = expr_raw.split("=", 1)
            var_name = name_part.strip()
            if var_name.isidentifier():
                self.input_var.set("")
                try:
                    # Evaluate right-hand side in the current context
                    value = self._evaluate_expression(value_part.strip())
                    if not hasattr(self, "user_vars"):
                        self.user_vars = {}
                    self.user_vars[var_name] = value
                    self.last_result = value
                    self._append_history(expr_raw, f"{var_name} = {self._format_result(value)}", is_error=False)
                except Exception as exc:  # noqa: BLE001
                    self._append_history(expr_raw, str(exc), is_error=True)
                return "break"

        # Track in input history
        self.input_history.append(expr_raw)
        self.history_index = None

        self.input_var.set("")
        self._evaluate_and_append(expr_raw)
        return "break"

    def _history_prev(self, event=None):
        if not self.input_history:
            return "break"

        if self.history_index is None:
            self.history_index = len(self.input_history) - 1
        else:
            self.history_index = max(0, self.history_index - 1)

        self.input_var.set(self.input_history[self.history_index])
        self.input_entry.icursor("end")
        return "break"

    def _history_next(self, event=None):
        if not self.input_history:
            return "break"

        if self.history_index is None:
            return "break"

        if self.history_index < len(self.input_history) - 1:
            self.history_index += 1
            self.input_var.set(self.input_history[self.history_index])
        else:
            # Past the newest entry: clear input
            self.history_index = None
            self.input_var.set("")

        self.input_entry.icursor("end")
        return "break"

    def _on_history_motion(self, event):
        """Show hand cursor when hovering over a result or error line."""
        try:
            index = self.history_text.index(f"@{event.x},{event.y}")
            tags = self.history_text.tag_names(index)
            if "result" in tags or "error" in tags:
                self.history_text.config(cursor="hand2")
            else:
                self.history_text.config(cursor="")
        except Exception:  # noqa: BLE001
            self.history_text.config(cursor="")

    def _on_history_click(self, event):
        """On click in history: if the click is on a result/error line, append that text to the input (no repeat)."""
        try:
            index = self.history_text.index(f"@{event.x},{event.y}")
            tags = self.history_text.tag_names(index)
            if "result" not in tags and "error" not in tags:
                return
            # Get the full line that was clicked
            line_start = index.split(".")[0] + ".0"
            line_end = index.split(".")[0] + ".end"
            line_text = self.history_text.get(line_start, line_end).strip()
            if not line_text:
                return
            input_form = self._result_display_to_input(line_text)
            current = self.input_var.get()
            # Don't add if input already ends with this text (no repeat)
            if current.rstrip().endswith(input_form):
                return
            if current.strip():
                self.input_var.set(current + " " + input_form)
            else:
                self.input_var.set(input_form)
            self.input_entry.focus_force()
            self.input_entry.icursor("end")
        except Exception:  # noqa: BLE001
            pass

    # ---------- Core evaluation ----------
    def _evaluate_and_append(self, expr_raw: str):
        pretty_expr = self._prettify_expression(expr_raw)

        try:
            result = self._evaluate_expression(expr_raw)
            result_str = self._format_result(result)
            self._append_history(pretty_expr, result_str, is_error=False)
            self.last_result = result
        except Exception as exc:  # noqa: BLE001
            self._append_history(pretty_expr, str(exc), is_error=True)

    def _append_history(self, pretty_expr: str, result: str, is_error: bool):
        self.history_text.configure(state="normal")

        # Expression line (optional)
        start_index = self.history_text.index("end-1c")
        if pretty_expr:
            if start_index != "1.0":
                self.history_text.insert("end", "\n")
            self.history_text.insert("end", f"{pretty_expr}", ("expr",))

        # Result line
        if pretty_expr:
            self.history_text.insert("end", "\n")
        tag = "error" if is_error else "result"
        # No blue arrow / prefix, just the result text
        self.history_text.insert("end", result, (tag,))

        # Divider line between outputs - span (almost) full width
        self.history_text.insert("end", "\n")
        # Calculate full width based on widget width and font
        try:
            self.history_text.update_idletasks()
            width_px = self.history_text.winfo_width()
            if width_px > 1:
                char_width = max(self.history_font.measure("─"), 1)
                # Use slightly less than full width so it doesn't feel too tight
                divider_width = max(1, int(width_px / char_width) - 1)
            else:
                divider_width = 80  # fallback
        except Exception:  # noqa: BLE001
            divider_width = 80  # fallback
        self.history_text.insert("end", "─" * divider_width, ("divider",))

        self.history_text.see("end")
        self.history_text.configure(state="disabled")

    # ---------- Pretty-printing ----------
    def _show_help(self, section: str | None = None):
        """
        Show help. With no section (or with h / ?), show an overview of
        available help categories. With a section, show detailed commands:

          help basic   – arithmetic, constants, functions
          help calc    – integrals, derivatives, zeros, sums
          help vars    – ans, round, base conversion, fib
          help syntax  – notation (powers, brackets, vectors)
          help plot    – graphing functions
          help ui      – shortcuts and behavior
        """
        key = (section or "").strip().lower() if section else ""

        if key == "basic":
            lines = [
                "help basic – arithmetic, constants, functions",
                "",
                "Basic arithmetic:",
                "  1+2, 3*(4+5), [1+2]*3",
                "",
                "Constants & variables:",
                "  pi, e, theta (θ), x",
                "",
                "Functions:",
                "  sin(x), cos(x), tan(x)",
                "  asin(x), acos(x), atan(x)  (arcsin/arccos/arctan also work)",
                "  sinh(x), cosh(x), tanh(x)",
                "  log(x), ln(x), exp(x), sqrt(x)",
            ]
            self._append_history("help basic", "\n".join(lines), is_error=False)
            return

        if key == "calc":
            lines = [
                "help calc – integrals, derivatives, limits, zeros, solve, taylor, sums",
                "",
                "Definite integrals:",
                "  int[a,b] f(x)",
                "  int[0,1] x^2           -> ∫₀¹ x² dx",
                "  int[0,pi] sin(x)       -> ∫₀^π sin(x) dx",
                "",
                "Indefinite integrals:",
                "  int x^2                -> x^3/3 + C",
                "",
                "Derivatives:",
                "  der f(x)               -> derivative wrt x",
                "  der[y] f(y)            -> derivative wrt y",
                "  der x^2                -> d/dx x²",
                "  der[y] y^3             -> d/dy y³",
                "  der x^2 at 3           -> derivative at a point (6)",
                "",
                "Limits:",
                "  lim[x->0] sin(x)/x     -> 1",
                "",
                "Zeros of single-variable functions:",
                "  zeros x^2-4            -> x = {-2, 2}",
                "  zeros[y] y^2-1         -> y = {-1, 1}",
                "",
                "Simplify / expand / factor:",
                "  simp expr              -> simplify",
                "  expand (x+1)^2         -> x^2 + 2x + 1",
                "  factor x^2-4           -> (x-2)*(x+2)",
                "",
                "Solving:",
                "  solve x^2=4            -> solve equation",
                "  solve {x+y=5, x-y=1}   -> system of equations",
                "",
                "Taylor series:",
                "  taylor sin(x) at 0 order 5",
                "",
                "Sums:",
                "  sum[k=1,n] k^2          -> sum from k=1 to n",
                "  sum[i=0,10] 2^i         -> sum from i=0 to 10",
                "",
                "Domain / Range:",
                "  domain sqrt(x)          -> find domain",
                "  range x^2               -> find range",
                "",
                "Substitute:",
                "  subs x=3 in x^2+1       -> substitute x=3",
                "",
                "Steps:",
                "  steps int x^2           -> show step-by-step",
                "  steps solve x^2=4       -> show solving steps",
            ]
            self._append_history("help calc", "\n".join(lines), is_error=False)
            return

        if key == "vars":
            lines = [
                "help vars – ans, round, base conversion, fib, variables, history",
                "",
                "Last answer:",
                "  ans                     -> last successful result",
                "",
                "Rounding:",
                "  round(n)                -> ans rounded to n decimals",
                "  round(0)                -> ans rounded to an integer",
                "  round(2) + 1            -> use rounded ans inside expressions",
                "",
                "Fraction / Decimal conversion:",
                "  frac(num) or frac num   -> convert to fraction (e.g. frac 0.5 -> 1/2)",
                "  dec(num) or dec num     -> convert fraction to decimal",
                "",
                "Base conversion:",
                "  bin(25) or bin 25       -> binary (0b11001)",
                "  hex(255) or hex 255     -> hexadecimal (0xff)",
                "  dec_base(0b1011)        -> decimal from binary/hex",
                "",
                "Fibonacci:",
                "  fib(10) or fib 10       -> 10th Fibonacci number",
                "",
                "User variables:",
                "  a = 5                   -> define variable a",
                "  b = a^2                 -> use variables in expressions",
                "  clearvars               -> clear all user variables",
                "",
                "History:",
                "  Up / Down arrows        -> cycle previous input expressions",
            ]
            self._append_history("help vars", "\n".join(lines), is_error=False)
            return

        if key == "syntax":
            lines = [
                "help syntax – notation and formatting",
                "",
                "Brackets:",
                "  () and [] behave the same ([], for grouping only)",
                "",
                "Powers:",
                "  x^2, x**2, x²           -> all treated as x squared",
                "  sin^2(x), cos^3(x)      -> (sin(x))^2, (cos(x))^3",
                "",
                "Absolute value:",
                "  |x-3|                   -> Abs(x-3)",
                "",
                "Vectors:",
                "  <x,y,z>                 -> vector (Matrix)",
                "  dot <1,2,3> <4,5,6>     -> dot product",
                "  mag <x,y,z>              -> magnitude",
                "  cross <1,2,3> <4,5,6>   -> cross product",
                "",
                "Display prettification (history only):",
                "  sqrt  -> √",
                "  pi    -> π",
                "  theta -> θ",
                "  **2,^2 -> ², **3,^3 -> ³",
            ]
            self._append_history("help syntax", "\n".join(lines), is_error=False)
            return

        if key == "plot":
            lines = [
                "help plot – graphing functions",
                "",
                "Basic plotting:",
                "  plot sin(x)              -> plot function",
                "  plot[x,-5,5] x^2         -> plot with custom range",
                "  plot sin(x), cos(x)       -> plot multiple functions",
                "",
                "Features:",
                "  Dark theme automatically applied",
                "  Auto window sizing",
                "  Grid and axes shown",
            ]
            self._append_history("help plot", "\n".join(lines), is_error=False)
            return

        if key == "ui":
            lines = [
                "help ui – shortcuts and behavior",
                "",
                "Shortcuts:",
                "  Enter                    -> evaluate expression",
                "  Up / Down                -> previous / next input",
                "  Ctrl+L                   -> clear history",
                "  clear / clear output     -> clear history via command",
                "",
                "Input behavior:",
                "  Starting with +,-,*,/,^  -> uses ans as the left operand",
                "",
                "Help:",
                "  help, h, ?               -> this overview",
                "  help all                  -> open full help in new window",
                "  help basic                -> arithmetic, constants, functions",
                "  help calc                 -> integrals, derivatives, zeros, sums",
                "  help vars                 -> ans, round, base conversion, fib",
                "  help syntax               -> notation, vectors, prettification",
                "  help plot                 -> graphing functions",
                "  help ui                   -> shortcuts and behavior",
            ]
            self._append_history("help ui", "\n".join(lines), is_error=False)
            return

        # Overview with sub-menus
        overview = [
            "help – overview of help sections",
            "",
            "Use one of these for details:",
            "  help basic    – arithmetic, constants, functions",
            "  help calc     – integrals, derivatives, zeros, sums",
            "  help vars     – ans, round, base conversion, fib",
            "  help plot     – graphing functions",
            "  help syntax   – notation (powers, sin^2, brackets, symbols)",
            "  help ui       – shortcuts and behavior",
            "  help all      – open full help in new window",
            "",
            "Tip: type h or ? to open this overview quickly.",
        ]
        self._append_history("help", "\n".join(overview), is_error=False)

    def _show_help_all(self):
        """Open a new window showing all help content with formatted titles and bullets."""
        win = tk.Toplevel(self)
        win.title("SciCalc – Help (all)")
        win.configure(bg="#121212")
        win.geometry("520x680")
        win.minsize(400, 400)

        text = tk.Text(
            win,
            bg="#121212",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            wrap="word",
            font=("SF Mono", 11),
            padx=12,
            pady=12,
            state="normal",
        )
        scroll = ttk.Scrollbar(win, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Configure text tags for formatting
        text.tag_configure("title", font=("SF Mono", 13, "bold"), foreground="#FFFFFF", spacing1=8, spacing3=4)
        text.tag_configure("bullet", foreground="#AAAAAA", lmargin1=20, lmargin2=40)

        # Insert formatted content
        def insert_title(title_text):
            text.insert("end", title_text + "\n", "title")

        def insert_bullet(bullet_text):
            text.insert("end", "- " + bullet_text + "\n", "bullet")

        def insert_blank():
            text.insert("end", "\n")

        insert_title("BASIC – arithmetic, constants, functions")
        insert_bullet("1+2, 3*(4+5), [1+2]*3")
        insert_bullet("Constants & variables: pi, e, theta (θ), x")
        insert_bullet("sin(x), cos(x), tan(x), asin, acos, atan, sinh, cosh, tanh")
        insert_bullet("log(x), ln(x), exp(x), sqrt(x)")
        insert_blank()

        insert_title("CALC – integrals, derivatives, limits, zeros, solve, taylor, sums")
        insert_bullet("Definite: int[a,b] f(x)   e.g. int[0,1] x^2")
        insert_bullet("Indefinite: int x^2  ->  x^3/3 + C")
        insert_bullet("der f(x), der[y] f(y), der x^2 at 3")
        insert_bullet("lim[x->0] sin(x)/x")
        insert_bullet("zeros x^2-4, zeros[y] y^2-1")
        insert_bullet("simp expr, expand (x+1)^2, factor x^2-4")
        insert_bullet("solve x^2=4, solve {x+y=5, x-y=1}")
        insert_bullet("taylor sin(x) at 0 order 5")
        insert_bullet("sum[k=1,n] k^2, sum[i=0,10] 2^i")
        insert_bullet("domain sqrt(x), range x^2")
        insert_bullet("subs x=3 in x^2+1")
        insert_bullet("steps int x^2, steps solve x^2=4")
        insert_blank()

        insert_title("VARS – ans, round, frac, dec, base conversion, fib, variables")
        insert_bullet("ans, round(n), round(0), round(2)+1")
        insert_bullet("frac(num) or frac num -> convert to fraction")
        insert_bullet("dec(num) or dec num -> convert to decimal")
        insert_bullet("bin(25), hex(255), dec_base(0b1011)")
        insert_bullet("fib(10) or fib 10 -> Fibonacci number")
        insert_bullet("a = 5, b = a^2, clearvars")
        insert_bullet("Up / Down arrows – cycle previous inputs")
        insert_blank()

        insert_title("SYNTAX – notation, vectors")
        insert_bullet("() and [] for grouping; x^2, sin^2(x)")
        insert_bullet("|x-3| -> Abs(x-3); sqrt->√, pi->π, theta->θ")
        insert_bullet("Vectors: <x,y,z>, dot <1,2,3> <4,5,6>")
        insert_bullet("mag <x,y,z>, cross <1,2,3> <4,5,6>")
        insert_blank()
        
        insert_title("PLOT – graphing")
        insert_bullet("plot sin(x)")
        insert_bullet("plot[x,-5,5] x^2")
        insert_bullet("plot sin(x), cos(x) -> multiple curves")
        insert_bullet("Dark theme, auto window")
        insert_blank()

        insert_title("UI – shortcuts and commands")
        insert_bullet("Enter – evaluate; Ctrl+L, clear / clear output – clear history")
        insert_bullet("+,-,*,/,^ at start – use ans as left operand")
        insert_bullet("help, h, ? – overview; help all – this window")
        insert_bullet("help basic | calc | vars | syntax | plot | ui – section in history")

        text.configure(state="disabled")

    def _show_startup_hint(self):
        """Show initial hint at the very top of the history."""
        self.history_text.configure(state="normal")
        existing = self.history_text.get("1.0", "end-1c").strip()
        if not existing:
            hint = 'enter "help" or "h" for list of commands'
            # Insert as a simple hint line plus divider
            self.history_text.insert("end", hint, ("hint",))
            self.history_text.insert("end", "\n")
            # Divider spans (almost) full width
            try:
                self.history_text.update_idletasks()
                width_px = self.history_text.winfo_width()
                if width_px > 1:
                    char_width = max(self.history_font.measure("─"), 1)
                    # Use slightly less than full width so it doesn't feel too tight
                    divider_width = max(1, int(width_px / char_width) - 1)
                else:
                    divider_width = 80
            except Exception:  # noqa: BLE001
                divider_width = 80
            self.history_text.insert("end", "─" * divider_width, ("divider",))
        self.history_text.configure(state="disabled")

    def _prettify_expression(self, expr: str) -> str:
        # For display only: replace function keywords with Unicode math symbols
        display = expr

        replacements = {
            "sqrt": "√",
            "pi": "π",
            "theta": "θ",
            "**2": "²",
            "**3": "³",
            "^2": "²",
            "^3": "³",
            "int": "∫",
            "der": "d/dx",
            "->": "→",
        }

        for k, v in replacements.items():
            display = display.replace(k, v)

        return display

    # ---------- Expression evaluation ----------
    def _evaluate_expression(self, expr: str):
        if sp is None:
            raise RuntimeError(
                "Sympy is required. Install with `pip install sympy`."
            )

        expr = expr.strip()

        # If the user starts with an operator, assume "ans <op> ..."
        if self.last_result is not None and expr and expr[0] in {"+", "-", "*", "/", "^"}:
            expr = f"ans{expr}"

        # round(n): special handler using last ans when it's the whole expression
        if re.fullmatch(r"\s*round\([^()]*\)\s*", expr):
            return self._eval_round(expr)

        # frac(num) or frac num: convert to fraction
        if expr.startswith("frac"):
            return self._eval_frac(expr)

        # dec(num) or dec num: convert fraction to decimal
        if expr.startswith("dec"):
            return self._eval_dec(expr)

        # Indefinite integral: int f(x)
        if expr.startswith("int ") and "[" not in expr[:8]:
            return self._eval_indef_integral(expr)

        # Simplify / expand / factor
        if expr.startswith("simp "):
            return self._eval_simplify(expr)
        if expr.startswith("expand "):
            return self._eval_expand(expr)
        if expr.startswith("factor "):
            return self._eval_factor(expr)

        # Limit: lim[x->a] expr
        if expr.startswith("lim["):
            return self._eval_limit(expr)

        # Equation solving: solve ...
        if expr.startswith("solve"):
            return self._eval_solve(expr)

        # Taylor series: taylor ...
        if expr.startswith("taylor"):
            return self._eval_taylor(expr)

        # Sum: sum[k=1,n] k^2
        if expr.startswith("sum["):
            return self._eval_sum(expr)

        # Fibonacci: fib(10)
        if expr.startswith("fib"):
            return self._eval_fib(expr)

        # Base conversion: bin(25), hex(255), dec_base(0b1011)
        if expr.startswith("bin(") or expr.startswith("bin "):
            return self._eval_bin(expr)
        if expr.startswith("hex(") or expr.startswith("hex "):
            return self._eval_hex(expr)
        if expr.startswith("dec_base(") or expr.startswith("dec_base "):
            return self._eval_dec_base(expr)

        # Domain / range
        if expr.startswith("domain "):
            return self._eval_domain(expr)
        if expr.startswith("range "):
            return self._eval_range(expr)

        # Substitute: subs x=3 in x^2+1
        if expr.startswith("subs "):
            return self._eval_subs(expr)

        # Show steps: steps int x^2
        if expr.startswith("steps "):
            return self._eval_steps(expr)

        # Vector operations: dot, mag, cross
        if expr.startswith("dot "):
            return self._eval_dot(expr)
        if expr.startswith("mag "):
            return self._eval_mag(expr)
        if expr.startswith("cross "):
            return self._eval_cross(expr)

        # Plotting: plot ...
        if expr.startswith("plot"):
            return self._eval_plot(expr)

        # Zeros of a single-variable function: zeros f(x) or zeros[y] f(y)
        if expr.startswith("zeros") or expr.startswith("zero"):
            return self._eval_zero(expr)

        # Definite integral: int[a,b] f(x)
        if expr.startswith("int"):
            return self._eval_integral(expr)

        # Derivative: der f(x)  or der[y] f(y)
        if expr.startswith("der"):
            return self._eval_derivative(expr)

        # Fallback: numeric/symbolic evaluation (including embedded commands in () or [])
        return self._eval_sympy(expr)

    def _eval_integral(self, expr: str):
        # Expected forms:
        #   int[a,b] f(x)
        #   int[a,b] f(x) dx
        if not expr.startswith("int["):
            raise ValueError("Use syntax: int[a,b] f(x)")

        try:
            bounds_part, func_part = expr[3:].split("]", 1)
        except ValueError:
            raise ValueError("Integral syntax: int[a,b] f(x)") from None

        bounds_part = bounds_part.strip("[ ")
        func_part = func_part.strip()

        if not bounds_part or "," not in bounds_part:
            raise ValueError("Integral bounds must be int[a,b]")

        a_str, b_str = [s.strip() for s in bounds_part.split(",", 1)]

        # Remove trailing 'dx' if provided
        if func_part.endswith("dx"):
            func_part = func_part[:-2].rstrip()

        x = self.sym_x
        local_dict = self._sympy_local_dict()
        a = sp.sympify(self._normalize_basic(a_str), locals=local_dict)
        b = sp.sympify(self._normalize_basic(b_str), locals=local_dict)
        f = sp.sympify(self._normalize_basic(func_part), locals=local_dict)

        integral = sp.integrate(f, (x, a, b))
        return integral

    def _eval_indef_integral(self, expr: str):
        # int f(x)  (indefinite integral)
        body = expr[3:].strip()
        if not body:
            raise ValueError("Indefinite integral syntax: int f(x)")

        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        free = list(f.free_symbols)
        var = free[0] if free else self.sym_x
        res = sp.integrate(f, var)
        return sp.simplify(res) + sp.Symbol("C")

    def _eval_simplify(self, expr: str):
        body = expr[4:].strip()
        if not body:
            raise ValueError("Simplify syntax: simp expr")
        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        return sp.simplify(f)

    def _eval_expand(self, expr: str):
        body = expr[6:].strip()
        if not body:
            raise ValueError("Expand syntax: expand expr")
        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        return sp.expand(f)

    def _eval_factor(self, expr: str):
        body = expr[6:].strip()
        if not body:
            raise ValueError("Factor syntax: factor expr")
        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        return sp.factor(f)

    def _eval_round(self, expr: str):
        """
        round(n) -> use last result (ans) and round it to n decimals.
        round(0) -> no decimals (integer string).
        """
        if not expr.startswith("round"):
            raise ValueError("Use syntax: round(n)")

        # Extract n inside parentheses: round(n)
        if "(" not in expr or ")" not in expr:
            raise ValueError("Use syntax: round(n)")

        start = expr.find("(") + 1
        end = expr.rfind(")")
        if end <= start:
            raise ValueError("Use syntax: round(n)")

        n_str = expr[start:end].strip() or "0"

        value, dec = self._compute_rounded_ans(n_str)

        if dec <= 0:
            return str(int(value))

        # Fixed number of decimals for pure round() display
        return f"{value:.{dec}f}"

    def _compute_rounded_ans(self, n_str: str):
        """Return (rounded_value, decimals) based on last_result and requested n."""
        if self.last_result is None:
            raise ValueError("No previous result to round (ans is undefined).")

        try:
            dec = int(float(n_str))
        except Exception:  # noqa: BLE001
            dec = 0

        val = self.last_result
        # Try to get numeric value from last_result
        try:
            v = float(val)
        except Exception:  # noqa: BLE001
            try:
                v = float(sp.N(val))
            except Exception:  # noqa: BLE001
                v = 0.0

        if dec <= 0:
            return round(v), 0

        return round(v, dec), dec

    def _eval_frac(self, expr: str):
        """
        frac(num) or frac num -> convert number/expression to fraction.
        If conversion fails, return the input as-is.
        """
        body = expr[4:].strip()
        if not body:
            raise ValueError("Fraction syntax: frac(num) or frac num")

        # Handle frac(num) or frac num
        if body.startswith("("):
            # Extract from parentheses
            if ")" not in body:
                raise ValueError("Fraction syntax: frac(num)")
            arg = body[1:body.find(")")].strip()
        else:
            # Space-separated: frac num — take the whole rest so 1/2 is one argument
            arg = body.strip()

        if not arg:
            raise ValueError("Fraction syntax: frac(num) or frac num")

        # Evaluate the argument
        try:
            local_dict = self._sympy_local_dict()
            value = sp.sympify(self._normalize_basic(arg), locals=local_dict)
            # If it's already a Rational or Integer, return as-is
            if isinstance(value, (sp.Rational, sp.Integer)):
                return value
            # Try to convert to fraction
            try:
                # Get numeric value and convert to Rational with limited denominator
                num_val = float(value.evalf()) if hasattr(value, "evalf") else float(value)
                return sp.Rational(num_val).limit_denominator(1000000)
            except Exception:  # noqa: BLE001
                # Fallback: nsimplify to find a nice rational
                try:
                    frac = sp.nsimplify(value, tolerance=1e-9)
                    if isinstance(frac, (sp.Rational, sp.Integer)):
                        return frac
                except Exception:  # noqa: BLE001
                    pass
                # If conversion fails, return the original value
                return value
        except Exception:  # noqa: BLE001
            # If evaluation fails, return as string
            return arg

    def _eval_dec(self, expr: str):
        """
        dec(num) or dec num -> convert fraction/expression to decimal.
        If conversion fails, return the input as-is.
        """
        body = expr[3:].strip()
        if not body:
            raise ValueError("Decimal syntax: dec(num) or dec num")

        # Handle dec(num) or dec num
        if body.startswith("("):
            # Extract from parentheses
            if ")" not in body:
                raise ValueError("Decimal syntax: dec(num)")
            arg = body[1:body.find(")")].strip()
        else:
            # Space-separated: dec num — take the whole rest so 1/2 is one argument
            arg = body.strip()

        if not arg:
            raise ValueError("Decimal syntax: dec(num) or dec num")

        # Evaluate the argument
        try:
            local_dict = self._sympy_local_dict()
            value = sp.sympify(self._normalize_basic(arg), locals=local_dict)
            # Convert to decimal
            try:
                decimal = value.evalf(15)  # 15 decimal places
                # Return as float if it's a simple number
                if isinstance(decimal, (sp.Float, sp.Number)):
                    return float(decimal)
                return decimal
            except Exception:  # noqa: BLE001
                # If conversion fails, return the original value
                return value
        except Exception:  # noqa: BLE001
            # If evaluation fails, return as string
            return arg

    def _eval_zero(self, expr: str):
        """
        Find zeros of a single-variable function.
        Forms:
          zeros x^2-4         (defaults to x)
          zeros[x] x^2-4
          zeros[y] y^2-1
        (alias: zero ... also accepted)
        Works with any single symbol; solves over the reals.
        """
        # Support both "zeros" and legacy "zero"
        if expr.startswith("zeros"):
            body = expr[5:].strip()
        else:
            body = expr[4:].strip()
        if not body:
            raise ValueError("Zero syntax: zeros f(x) or zeros[var] f(var)")

        # Default variable
        var = self.sym_x
        var_explicit = False

        # zero[y] f(y) form
        if body.startswith("["):
            try:
                var_part, func_part = body.split("]", 1)
            except ValueError:
                raise ValueError("Zero syntax: zeros[y] f(y)") from None
            var_name = var_part.strip("[] ")
            if not var_name.isidentifier():
                raise ValueError("Invalid variable name for zero()")
            var = sp.symbols(var_name)
            var_explicit = True
            body = func_part.strip()

        if not body:
            raise ValueError("Zero syntax: zeros f(x) or zeros[var] f(var)")

        local_dict = self._sympy_local_dict()
        # Ensure our variable exists in locals for sympify
        local_dict[str(var)] = var

        f = sp.sympify(self._normalize_basic(body), locals=local_dict)

        # Infer variable if not explicitly set
        free_syms = list(f.free_symbols)
        if not var_explicit:
            if len(free_syms) == 1:
                var = free_syms[0]
            elif len(free_syms) == 0:
                raise ValueError("Expression has no variable to solve for.")
            else:
                raise ValueError("zeros() only supports a single-variable function.")
        else:
            # Explicit variable: ensure we don't have extra ones
            other_syms = [s for s in free_syms if s != var]
            if other_syms:
                raise ValueError("zeros() only supports one variable at a time.")

        sol = sp.solveset(f, var, domain=sp.S.Reals)

        # Finite set of roots -> pretty-print as variable = {r1, r2, ...}
        if isinstance(sol, sp.FiniteSet):
            if not sol:
                return f"No real zeros for {var}."

            roots = []
            for r in sol:
                try:
                    val = r.evalf(12)
                    s = f"{val}"
                    if "." in s:
                        s = s.rstrip("0").rstrip(".")
                    roots.append(s)
                except Exception:  # noqa: BLE001
                    roots.append(str(r))

            return f"{var} = {{{', '.join(roots)}}}"

        # Otherwise, return Sympy's description (intervals, imagesets, etc.)
        return str(sol)

    def _eval_derivative(self, expr: str):
        # Forms:
        #   der f(x)          -> derivative wrt x
        #   der[y] f(y)       -> derivative wrt y
        #   der f(x) at a     -> derivative at point a
        body = expr[3:].strip()
        if not body:
            raise ValueError("Derivative syntax: der f(x) or der[y] f(y)")

        var = self.sym_x

        # Optional "at a" suffix
        at_value = None
        if " at " in body:
            func_part, at_part = body.split(" at ", 1)
            body = func_part.strip()
            at_value = at_part.strip()

        if body.startswith("["):
            try:
                var_part, func_part = body.split("]", 1)
            except ValueError:
                raise ValueError("Derivative syntax: der[y] f(y)") from None
            var_name = var_part.strip("[] ")
            if not var_name.isidentifier():
                raise ValueError("Invalid variable name for derivative")
            var = sp.symbols(var_name)
            body = func_part.strip()

        local_dict = self._sympy_local_dict()
        local_dict["x"] = self.sym_x
        if var != self.sym_x:
            local_dict[str(var)] = var

        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        derivative = sp.diff(f, var)

        if at_value is not None:
            a = sp.sympify(self._normalize_basic(at_value), locals=local_dict)
            return derivative.subs(var, a).evalf(12)

        return derivative

    def _eval_sympy(self, expr: str):
        # First, expand any round(n) calls inside the expression to numeric
        expr_with_rounds = self._replace_round_calls(expr)
        # Replace embedded commands in ( ) or [ ] so e.g. (der x^2 at 3) + 1 works
        expr_with_rounds = self._replace_embedded_commands(expr_with_rounds)

        # Normalize basic syntax: [] -> (), ^ -> **, ln -> log, etc.
        normalized = self._normalize_basic(expr_with_rounds)
        
        # Check for balanced parentheses before sympify
        self._check_balanced_parens(normalized)

        local_dict = self._sympy_local_dict()
        result = sp.sympify(normalized, locals=local_dict)
        result = sp.simplify(result)
        
        # Simplify sqrt(x^2) patterns to Abs(x)
        result = self._simplify_sqrt_powers(result)
        
        return result

    def _check_balanced_parens(self, expr: str):
        """Check if parentheses are balanced and raise a clear error if not."""
        depth = 0
        for i, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    raise ValueError(f"Unmatched closing parenthesis ')' at position {i+1}. Check your expression for extra closing parentheses.")
        if depth > 0:
            raise ValueError(f"Unmatched opening parentheses: {depth} opening parenthesis(es) not closed. Check your expression for missing closing parentheses.")
        if depth < 0:
            raise ValueError(f"Unmatched closing parentheses: {abs(depth)} closing parenthesis(es) without matching opening ones.")

    def _simplify_sqrt_powers(self, expr):
        """
        Simplify patterns like sqrt(x^2) to Abs(x), sqrt(x^4) to x^2, etc.
        Handles both sqrt() function calls and (x^2)**0.5 power forms.
        """
        # Handle sqrt() function calls: sqrt(x^2) -> Abs(x)
        if isinstance(expr, sp.Pow):
            # Check if it's sqrt(something) = something**0.5 or something**(1/2)
            exp_val = expr.exp
            # Normalize exp to compare: could be 0.5, Rational(1,2), or 1/2
            if exp_val == sp.Rational(1, 2) or exp_val == 0.5 or (hasattr(exp_val, 'p') and hasattr(exp_val, 'q') and exp_val.p == 1 and exp_val.q == 2):
                base = expr.base
                # If base is a power, simplify sqrt(x^n)
                if isinstance(base, sp.Pow):
                    inner_base = base.base
                    inner_exp = base.exp
                    # sqrt(x^2) -> Abs(x)
                    if inner_exp == 2 or inner_exp == sp.Integer(2):
                        return sp.Abs(inner_base)
                    # sqrt(x^(2n)) -> Abs(x)^n for even powers
                    if isinstance(inner_exp, (int, sp.Integer)) and inner_exp > 0 and inner_exp % 2 == 0:
                        return sp.Abs(inner_base) ** (inner_exp / 2)
                    # sqrt(x^(2n+1)) -> x^n * sqrt(x) for odd powers > 1
                    if isinstance(inner_exp, (int, sp.Integer)) and inner_exp > 1 and inner_exp % 2 == 1:
                        return (inner_base ** ((inner_exp - 1) / 2)) * sp.sqrt(inner_base)
        
        # Recursively apply to subexpressions
        if hasattr(expr, 'args'):
            new_args = [self._simplify_sqrt_powers(arg) for arg in expr.args]
            if new_args != list(expr.args):
                return expr.func(*new_args)
        
        return expr

    def _result_to_embed(self, result) -> str:
        """Convert an evaluation result to a string that can be embedded in an expression."""
        if isinstance(result, (int, float)):
            return str(int(result)) if result == int(result) else str(result)
        if hasattr(result, "free_symbols"):
            return str(result)
        return str(result)

    def _replace_embedded_commands(self, expr: str) -> str:
        """
        Find subexpressions in ( ) or [ ] that are single commands (int, simp, expand,
        factor, lim, der, taylor, etc.) and replace them with their evaluated value
        so that (der x^2 at 3) + 1 and [simp sin(x)^2+cos(x)^2] * 2 work.
        """
        cmd_prefixes = (
            "int ",
            "int[",
            "simp ",
            "expand ",
            "factor ",
            "lim[",
            "der ",
            "taylor ",
            "frac ",
            "dec ",
            "sum[",
            "domain ",
            "range ",
            "subs ",
            "steps ",
            "dot ",
            "mag ",
            "cross ",
        )

        def find_matching(expr: str, i: int) -> int | None:
            open_ch = expr[i]
            if open_ch not in "([":
                return None
            close_ch = ")" if open_ch == "(" else "]"
            depth = 1
            j = i + 1
            while j < len(expr):
                if expr[j] == open_ch:
                    depth += 1
                elif expr[j] == close_ch:
                    depth -= 1
                    if depth == 0:
                        return j
                j += 1
            return None

        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(expr):
                if expr[i] not in "([":
                    i += 1
                    continue
                j = find_matching(expr, i)
                if j is None:
                    i += 1
                    continue
                content = expr[i + 1 : j].strip()
                if not content:
                    i = j + 1
                    continue
                if not any(content.startswith(p) for p in cmd_prefixes):
                    i = j + 1
                    continue
                try:
                    result = self._evaluate_expression(content)
                    embed_str = self._result_to_embed(result)
                    # Wrap in parens so it parses as one unit
                    replacement = "(" + embed_str + ")"
                    expr = expr[:i] + replacement + expr[j + 1 :]
                    changed = True
                    break  # new pass so indices stay valid
                except Exception:  # noqa: BLE001
                    pass
                i = j + 1

        return expr

    def _eval_limit(self, expr: str):
        # lim[x->a] expr
        if not expr.startswith("lim["):
            raise ValueError("Limit syntax: lim[x->a] expr")

        try:
            header, body = expr.split("]", 1)
        except ValueError:
            raise ValueError("Limit syntax: lim[x->a] expr") from None

        header = header.strip()[4:]  # after 'lim['
        body = body.strip()
        if "->" not in header:
            raise ValueError("Limit syntax: lim[x->a] expr")

        var_name, point = [s.strip() for s in header.split("->", 1)]
        if not var_name.isidentifier():
            raise ValueError("Invalid variable name in limit")

        local_dict = self._sympy_local_dict()
        var = sp.symbols(var_name)
        local_dict[var_name] = var
        x0 = sp.sympify(self._normalize_basic(point), locals=local_dict)
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        return sp.limit(f, var, x0)

    def _eval_solve(self, expr: str):
        # solve expr=0, solve[y] expr=0, or systems with {...}
        body = expr[5:].strip()
        if not body:
            raise ValueError("Solve syntax: solve expr or solve[y] expr")

        local_dict = self._sympy_local_dict()
        var = self.sym_x

        if body.startswith("["):
            try:
                var_part, rest = body.split("]", 1)
            except ValueError:
                raise ValueError("Solve syntax: solve[y] expr") from None
            var_name = var_part.strip("[] ")
            if not var_name.isidentifier():
                raise ValueError("Invalid variable name for solve()")
            var = sp.symbols(var_name)
            local_dict[var_name] = var
            body = rest.strip()

        # System of equations: solve {eq1, eq2, ...}
        if body.startswith("{") and body.endswith("}"):
            inside = body.strip("{} ")
            eq_strs = [s.strip() for s in inside.split(",") if s.strip()]
            equations = []
            symbols = set()
            for s in eq_strs:
                if "=" in s:
                    lhs_str, rhs_str = s.split("=", 1)
                    lhs = sp.sympify(self._normalize_basic(lhs_str), locals=local_dict)
                    rhs = sp.sympify(self._normalize_basic(rhs_str), locals=local_dict)
                    equations.append(sp.Eq(lhs, rhs))
                    symbols |= lhs.free_symbols | rhs.free_symbols
                else:
                    f = sp.sympify(self._normalize_basic(s), locals=local_dict)
                    equations.append(sp.Eq(f, 0))
                    symbols |= f.free_symbols
            if not symbols:
                raise ValueError("System has no variables.")
            sol = sp.solve(equations, list(symbols), dict=True)
            return sol

        # Single equation: expr=0 or lhs=rhs
        if "=" in body:
            lhs_str, rhs_str = body.split("=", 1)
            lhs = sp.sympify(self._normalize_basic(lhs_str), locals=local_dict)
            rhs = sp.sympify(self._normalize_basic(rhs_str), locals=local_dict)
            eq = sp.Eq(lhs, rhs)
        else:
            f = sp.sympify(self._normalize_basic(body), locals=local_dict)
            eq = sp.Eq(f, 0)

        sol = sp.solve(eq, var)
        return sol

    def _eval_taylor(self, expr: str):
        # taylor f(x) at a order n
        body = expr[6:].strip()
        if not body:
            raise ValueError("Taylor syntax: taylor f(x) at a order n")

        parts = body.split(" at ", 1)
        if len(parts) != 2:
            raise ValueError("Taylor syntax: taylor f(x) at a order n")
        func_str, rest = parts[0].strip(), parts[1].strip()

        if "order" not in rest:
            raise ValueError("Taylor syntax: taylor f(x) at a order n")
        point_str, order_str = [s.strip() for s in rest.split("order", 1)]

        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(func_str), locals=local_dict)
        free = list(f.free_symbols)
        var = free[0] if free else self.sym_x
        local_dict[str(var)] = var
        a = sp.sympify(self._normalize_basic(point_str), locals=local_dict)
        n = int(order_str)
        series = sp.series(f, var, a, n + 1).removeO()
        return series

    def _eval_sum(self, expr: str):
        """
        sum[k=1,n] k^2  or  sum[i=0,10] 2^i
        """
        if not expr.startswith("sum["):
            raise ValueError("Sum syntax: sum[k=1,n] expr")
        
        try:
            header, body = expr.split("]", 1)
        except ValueError:
            raise ValueError("Sum syntax: sum[k=1,n] expr") from None
        
        header = header.strip()[4:]  # after 'sum['
        body = body.strip()
        
        # Parse header: k=1,n or k=0,10
        if "," not in header:
            raise ValueError("Sum syntax: sum[k=1,n] expr")
        
        var_part, limit_part = [s.strip() for s in header.split(",", 1)]
        if "=" not in var_part:
            raise ValueError("Sum syntax: sum[k=1,n] expr (need k=1)")
        
        var_name, start_str = [s.strip() for s in var_part.split("=", 1)]
        if not var_name.isidentifier():
            raise ValueError("Invalid variable name in sum")
        
        local_dict = self._sympy_local_dict()
        var = sp.symbols(var_name)
        local_dict[var_name] = var
        start = sp.sympify(self._normalize_basic(start_str), locals=local_dict)
        end = sp.sympify(self._normalize_basic(limit_part), locals=local_dict)
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        
        return sp.Sum(f, (var, start, end)).doit()

    def _eval_fib(self, expr: str):
        """
        fib(10) or fib 10 -> Fibonacci number
        """
        body = expr[3:].strip()
        if body.startswith("("):
            if ")" not in body:
                raise ValueError("Fibonacci syntax: fib(n)")
            arg = body[1:body.find(")")].strip()
        else:
            arg = body.strip()
        
        if not arg:
            raise ValueError("Fibonacci syntax: fib(n)")
        
        try:
            n = int(float(sp.sympify(self._normalize_basic(arg), locals=self._sympy_local_dict())))
            if n < 0:
                raise ValueError("Fibonacci requires non-negative integer")
            # Compute Fibonacci using Sympy
            return sp.fibonacci(n)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Fibonacci syntax: fib(n) where n is an integer. {e}") from e

    def _eval_bin(self, expr: str):
        """
        bin(25) or bin 25 -> binary representation
        """
        body = expr[3:].strip()
        if body.startswith("("):
            if ")" not in body:
                raise ValueError("Binary syntax: bin(n)")
            arg = body[1:body.find(")")].strip()
        else:
            arg = body.strip()
        
        if not arg:
            raise ValueError("Binary syntax: bin(n)")
        
        try:
            local_dict = self._sympy_local_dict()
            n = int(float(sp.sympify(self._normalize_basic(arg), locals=local_dict)))
            return f"0b{bin(n)[2:]}"
        except (ValueError, TypeError) as e:
            raise ValueError(f"Binary syntax: bin(n) where n is an integer. {e}") from e

    def _eval_hex(self, expr: str):
        """
        hex(255) or hex 255 -> hexadecimal representation
        """
        body = expr[3:].strip()
        if body.startswith("("):
            if ")" not in body:
                raise ValueError("Hex syntax: hex(n)")
            arg = body[1:body.find(")")].strip()
        else:
            arg = body.strip()
        
        if not arg:
            raise ValueError("Hex syntax: hex(n)")
        
        try:
            local_dict = self._sympy_local_dict()
            n = int(float(sp.sympify(self._normalize_basic(arg), locals=local_dict)))
            return f"0x{hex(n)[2:]}"
        except (ValueError, TypeError) as e:
            raise ValueError(f"Hex syntax: hex(n) where n is an integer. {e}") from e

    def _eval_dec_base(self, expr: str):
        """
        dec_base(0b1011) or dec_base 0b1011 -> decimal from binary/hex
        """
        body = expr[8:].strip()  # "dec_base" is 8 chars
        if body.startswith("("):
            if ")" not in body:
                raise ValueError("Decimal base syntax: dec_base(0b1011) or dec_base(0xff)")
            arg = body[1:body.find(")")].strip()
        else:
            arg = body.strip()
        
        if not arg:
            raise ValueError("Decimal base syntax: dec_base(0b1011) or dec_base(0xff)")
        
        try:
            # Handle 0b (binary) or 0x (hex) prefixes
            if arg.startswith("0b") or arg.startswith("0B"):
                return int(arg, 2)
            elif arg.startswith("0x") or arg.startswith("0X"):
                return int(arg, 16)
            else:
                # Try to parse as regular number
                local_dict = self._sympy_local_dict()
                return int(float(sp.sympify(self._normalize_basic(arg), locals=local_dict)))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Decimal base syntax: dec_base(0b1011) or dec_base(0xff). {e}") from e

    def _eval_domain(self, expr: str):
        """
        domain sqrt(x) -> find domain of function
        """
        body = expr[7:].strip()
        if not body:
            raise ValueError("Domain syntax: domain f(x)")
        
        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        free = list(f.free_symbols)
        if not free:
            return "Domain: all real numbers (no variables)"
        
        var = free[0] if len(free) == 1 else self.sym_x
        domain = sp.calculus.util.continuous_domain(f, var, sp.S.Reals)
        return f"Domain of {var}: {domain}"

    def _eval_range(self, expr: str):
        """
        range x^2 -> find range of function
        """
        body = expr[6:].strip()
        if not body:
            raise ValueError("Range syntax: range f(x)")
        
        local_dict = self._sympy_local_dict()
        f = sp.sympify(self._normalize_basic(body), locals=local_dict)
        free = list(f.free_symbols)
        if not free:
            return "Range: {f} (constant function)"
        
        var = free[0] if len(free) == 1 else self.sym_x
        try:
            range_set = sp.calculus.util.function_range(f, var, sp.S.Reals)
            return f"Range of {var}: {range_set}"
        except Exception:  # noqa: BLE001
            return f"Range: could not determine (try zeros or limits)"

    def _eval_subs(self, expr: str):
        """
        subs x=3 in x^2+1 -> substitute x=3 into expression
        """
        body = expr[4:].strip()
        if " in " not in body:
            raise ValueError("Substitute syntax: subs x=3 in x^2+1")
        
        sub_part, expr_part = [s.strip() for s in body.split(" in ", 1)]
        if "=" not in sub_part:
            raise ValueError("Substitute syntax: subs x=3 in x^2+1")
        
        var_name, value_str = [s.strip() for s in sub_part.split("=", 1)]
        if not var_name.isidentifier():
            raise ValueError("Invalid variable name in substitute")
        
        local_dict = self._sympy_local_dict()
        var = sp.symbols(var_name)
        local_dict[var_name] = var
        value = sp.sympify(self._normalize_basic(value_str), locals=local_dict)
        f = sp.sympify(self._normalize_basic(expr_part), locals=local_dict)
        
        return f.subs(var, value)

    def _eval_steps(self, expr: str):
        """
        steps int x^2 -> show step-by-step solution
        """
        body = expr[6:].strip()
        if not body:
            raise ValueError("Steps syntax: steps int x^2 or steps solve x^2=4")
        
        # Try to detect what kind of operation
        if body.startswith("int "):
            # Indefinite integral
            func_part = body[3:].strip()
            if not func_part:
                raise ValueError("Steps syntax: steps int <expression> e.g. steps int x^2")
            local_dict = self._sympy_local_dict()
            f = sp.sympify(self._normalize_basic(func_part), locals=local_dict)
            free = sorted(f.free_symbols, key=str)
            var = free[0] if free else self.sym_x
            result = sp.integrate(f, var)
            return f"∫ {f} d{var} = {result} + C"
        elif body.startswith("solve "):
            # Equation solving
            solve_part = body[6:].strip()
            if not solve_part:
                raise ValueError("Steps syntax: steps solve <equation> e.g. steps solve x^2=4")
            local_dict = self._sympy_local_dict()
            if "=" in solve_part:
                lhs_str, rhs_str = solve_part.split("=", 1)
                lhs = sp.sympify(self._normalize_basic(lhs_str), locals=local_dict)
                rhs = sp.sympify(self._normalize_basic(rhs_str), locals=local_dict)
                eq = sp.Eq(lhs, rhs)
            else:
                f = sp.sympify(self._normalize_basic(solve_part), locals=local_dict)
                eq = sp.Eq(f, 0)
            free = sorted(eq.free_symbols, key=str)
            var = free[0] if free else self.sym_x
            sol = sp.solve(eq, var)
            if sol is None or (isinstance(sol, list) and len(sol) == 0):
                sol_str = "No solution"
            elif isinstance(sol, list):
                sol_str = ", ".join(str(s) for s in sol)
            else:
                sol_str = str(sol)
            return f"Solving {eq}\n{var} = {sol_str}"
        else:
            # Generic: just evaluate and show
            local_dict = self._sympy_local_dict()
            result = sp.sympify(self._normalize_basic(body), locals=local_dict)
            return f"Steps for: {body}\nResult: {result}"

    def _eval_plot(self, expr: str):
        """
        plot sin(x)
        plot[x,-5,5] x^2
        plot sin(x), cos(x)
        """
        try:
            import matplotlib
            # Use TkAgg explicitly so plotting works when packaged (PyInstaller)
            matplotlib.use("TkAgg")
            import matplotlib.backends.backend_tkagg  # noqa: F401 - for PyInstaller
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise RuntimeError("Plotting requires matplotlib. Install with: pip install matplotlib")
        
        body = expr[4:].strip()
        if not body:
            raise ValueError("Plot syntax: plot f(x) or plot[x,a,b] f(x)")
        
        # Parse range if present: plot[x,-5,5] f(x)
        x_range = None
        if body.startswith("["):
            try:
                range_part, func_part = body.split("]", 1)
            except ValueError:
                raise ValueError("Plot syntax: plot[x,a,b] f(x)") from None
            range_part = range_part.strip("[ ")
            func_part = func_part.strip()
            if "," in range_part:
                var_name, a_str, b_str = [s.strip() for s in range_part.split(",", 2)]
                x_range = (var_name, float(a_str), float(b_str))
            else:
                raise ValueError("Plot syntax: plot[x,a,b] f(x)")
        else:
            func_part = body
        
        # Check for multiple functions: plot sin(x), cos(x)
        funcs = [f.strip() for f in func_part.split(",")]
        
        local_dict = self._sympy_local_dict()
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor("#121212")
        ax.set_facecolor("#121212")
        ax.spines['bottom'].set_color('#FFFFFF')
        ax.spines['top'].set_color('#FFFFFF')
        ax.spines['right'].set_color('#FFFFFF')
        ax.spines['left'].set_color('#FFFFFF')
        ax.tick_params(colors='#FFFFFF')
        ax.xaxis.label.set_color('#FFFFFF')
        ax.yaxis.label.set_color('#FFFFFF')
        ax.title.set_color('#FFFFFF')
        
        for func_str in funcs:
            f = sp.sympify(self._normalize_basic(func_str), locals=local_dict)
            free = list(f.free_symbols)
            var = free[0] if free else self.sym_x
            
            if x_range:
                var_name, a, b = x_range
                var = sp.symbols(var_name)
                x_vals = np.linspace(a, b, 1000)
            else:
                a, b = -10, 10
                x_vals = np.linspace(a, b, 1000)
            
            # Convert sympy function to numpy-compatible
            f_lambda = sp.lambdify(var, f, "numpy")
            y_vals = f_lambda(x_vals)
            
            ax.plot(x_vals, y_vals, label=str(func_str))
        
        ax.legend(facecolor="#1E1E1E", edgecolor="#333333", labelcolor="#FFFFFF")
        ax.grid(True, color="#333333", alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        return "Plot displayed in new window"

    def _eval_dot(self, expr: str):
        """
        dot <x1,y1,z1> <x2,y2,z2> -> dot product
        """
        body = expr[3:].strip()
        if not body or "<" not in body:
            raise ValueError("Dot product syntax: dot <x1,y1,z1> <x2,y2,z2>")
        
        # Find two vectors
        vecs = []
        i = 0
        while i < len(body):
            if body[i] == "<":
                j = i + 1
                depth = 0
                while j < len(body):
                    if body[j] == "<":
                        depth += 1
                    elif body[j] == ">":
                        if depth == 0:
                            vecs.append(body[i:j+1])
                            i = j + 1
                            break
                        depth -= 1
                    j += 1
                else:
                    i += 1
            else:
                i += 1
        
        if len(vecs) != 2:
            raise ValueError("Dot product requires exactly two vectors: dot <x1,y1,z1> <x2,y2,z2>")
        
        local_dict = self._sympy_local_dict()
        v1 = sp.sympify(self._normalize_basic(vecs[0]), locals=local_dict)
        v2 = sp.sympify(self._normalize_basic(vecs[1]), locals=local_dict)
        
        if isinstance(v1, sp.Matrix) and isinstance(v2, sp.Matrix):
            return v1.dot(v2)
        raise ValueError("Dot product requires Matrix vectors")

    def _eval_mag(self, expr: str):
        """
        mag <x,y,z> -> magnitude of vector
        """
        body = expr[3:].strip()
        if not body or "<" not in body:
            raise ValueError("Magnitude syntax: mag <x,y,z>")
        
        # Find vector
        vec_start = body.find("<")
        if vec_start == -1:
            raise ValueError("Magnitude syntax: mag <x,y,z>")
        
        vec_end = body.find(">", vec_start)
        if vec_end == -1:
            raise ValueError("Magnitude syntax: mag <x,y,z>")
        
        vec_str = body[vec_start:vec_end+1]
        local_dict = self._sympy_local_dict()
        v = sp.sympify(self._normalize_basic(vec_str), locals=local_dict)
        
        if isinstance(v, sp.Matrix):
            return sp.sqrt(v.dot(v))
        raise ValueError("Magnitude requires Matrix vector")

    def _eval_cross(self, expr: str):
        """
        cross <x1,y1,z1> <x2,y2,z2> -> cross product
        """
        body = expr[5:].strip()
        if not body or "<" not in body:
            raise ValueError("Cross product syntax: cross <x1,y1,z1> <x2,y2,z2>")
        
        # Find two vectors
        vecs = []
        i = 0
        while i < len(body):
            if body[i] == "<":
                j = i + 1
                depth = 0
                while j < len(body):
                    if body[j] == "<":
                        depth += 1
                    elif body[j] == ">":
                        if depth == 0:
                            vecs.append(body[i:j+1])
                            i = j + 1
                            break
                        depth -= 1
                    j += 1
                else:
                    i += 1
            else:
                i += 1
        
        if len(vecs) != 2:
            raise ValueError("Cross product requires exactly two vectors: cross <x1,y1,z1> <x2,y2,z2>")
        
        local_dict = self._sympy_local_dict()
        v1 = sp.sympify(self._normalize_basic(vecs[0]), locals=local_dict)
        v2 = sp.sympify(self._normalize_basic(vecs[1]), locals=local_dict)
        
        if isinstance(v1, sp.Matrix) and isinstance(v2, sp.Matrix):
            return v1.cross(v2)
        raise ValueError("Cross product requires Matrix vectors")

    def _rewrite_vectors(self, expr: str) -> str:
        """
        Convert <x,y,z> to Matrix([x,y,z]) for vector support.
        """
        out = []
        i = 0
        n = len(expr)
        
        while i < n:
            if expr[i] == "<":
                # Found start of vector
                j = i + 1
                components = []
                current_comp = []
                depth = 0
                
                while j < n:
                    ch = expr[j]
                    if ch == "<":
                        depth += 1
                        current_comp.append(ch)
                    elif ch == ">":
                        if depth == 0:
                            # End of vector
                            comp_str = "".join(current_comp).strip()
                            if comp_str:
                                components.append(comp_str)
                            break
                        depth -= 1
                        current_comp.append(ch)
                    elif ch == "," and depth == 0:
                        # Component separator
                        comp_str = "".join(current_comp).strip()
                        if comp_str:
                            components.append(comp_str)
                        current_comp = []
                    else:
                        current_comp.append(ch)
                    j += 1
                
                if j < n:
                    # Successfully parsed vector
                    comps_str = ", ".join(components) if components else "0"
                    out.append(f"Matrix([{comps_str}])")
                    i = j + 1
                else:
                    # Unmatched <, just copy it
                    out.append("<")
                    i += 1
            else:
                out.append(expr[i])
                i += 1
        
        return "".join(out)

    def _normalize_basic(self, expr: str) -> str:
        # Rewrite absolute values first: |x-3| -> Abs(x-3)
        expr = self._rewrite_abs(expr)
        
        # Convert vectors <x,y,z> to Matrix([x,y,z]) before other processing
        expr = self._rewrite_vectors(expr)
        
        # Convert function calls without parentheses: sqrt 3 -> sqrt(3)
        expr = self._add_parens_to_func_calls(expr)

        # Rewrite custom integral syntax into a callable helper
        # so it can appear anywhere in expressions, e.g. (int[0,1] x^2) + 8
        out = self._rewrite_integrals(expr)

        # Brackets and simple aliases
        out = out.replace("[", "(").replace("]", ")")
        out = out.replace("ln", "log")

        # Implicit multiplication: 2x, 3sin(x), (x+1)(x-1) etc.
        # Known function names that should NOT get * inserted before (
        func_names = {
            "sin", "cos", "tan", "asin", "acos", "atan", "arcsin", "arccos", "arctan",
            "sinh", "cosh", "tanh", "sqrt", "log", "ln", "exp", "abs", "Abs",
            "gcd", "lcm", "isprime", "factorint", "mod", "to_deg", "to_rad",
            "IntDef", "Matrix", "round", "frac", "dec", "fib", "bin", "hex", "dec_base",
            "sum", "domain", "range", "subs", "steps", "plot",
            "zeros", "zero", "der", "int", "lim", "dot", "mag", "cross"
        }
        
        out = re.sub(r"(\d)([A-Za-z(])", r"\1*\2", out)
        out = re.sub(r"(\))(\()", r"\1*\2", out)
        out = re.sub(r"(\))([A-Za-z])", r"\1*\2", out)
        # Only add * between letters and ( if it's NOT a function name
        def add_mult_if_not_func(match):
            letters = match.group(1)
            # Check if this is a known function name
            if letters in func_names:
                return match.group(0)  # Keep as-is: sqrt( -> sqrt(
            return match.group(1) + "*" + match.group(2)  # Add * for variables: x( -> x*(
        out = re.sub(r"([A-Za-z]+)(\()", add_mult_if_not_func, out)

        # Convert Unicode superscripts back to powers
        out = out.replace("²", "**2").replace("³", "**3")

        # Support patterns like sin^2(x), cos^3(x), etc.
        out = self._normalize_function_powers(out)

        # Finally, caret to power for general cases: x^2 -> x**2
        out = out.replace("^", "**")
        return out

    def _add_parens_to_func_calls(self, expr: str) -> str:
        """
        Convert function calls without parentheses: sqrt 3 -> sqrt(3), sin x -> sin(x)
        """
        func_names = {
            "sin", "cos", "tan", "asin", "acos", "atan", "arcsin", "arccos", "arctan",
            "sinh", "cosh", "tanh", "sqrt", "log", "ln", "exp", "abs", "Abs",
            "gcd", "lcm", "isprime", "factorint", "mod", "to_deg", "to_rad",
            "Matrix", "frac", "dec", "fib", "bin", "hex", "dec_base", "sum", "domain",
            "range", "subs", "steps", "plot", "dot", "mag", "cross"
        }
        
        out = []
        i = 0
        n = len(expr)
        
        while i < n:
            # Look for function name
            matched_func = None
            func_len = 0
            
            for func in sorted(func_names, key=len, reverse=True):  # Longest first to match "arcsin" before "arc"
                # Match function name: at end, or next char is not ( (so we can have space, digit, letter, etc.)
                if expr[i:].startswith(func) and (i + len(func) >= n or expr[i + len(func)] != "("):
                    matched_func = func
                    func_len = len(func)
                    break
            
            if matched_func:
                out.append(matched_func)
                i += func_len
                # If already followed by (, don't add extra parens
                if i < n and expr[i] == "(":
                    pass
                else:
                    out.append("(")
                    # Skip whitespace
                    while i < n and expr[i].isspace():
                        i += 1
                    # Find the argument (until next operator, comma, or end)
                    # Include ^ for powers: sqrt x^2 -> sqrt(x^2)
                    arg_start = i
                    paren_depth = 0
                    while i < n:
                        ch = expr[i]
                        if ch == "(":
                            paren_depth += 1
                        elif ch == ")":
                            if paren_depth == 0:
                                break
                            paren_depth -= 1
                        elif paren_depth == 0:
                            if ch == "^":
                                pass
                            elif ch == "-" and i == arg_start:
                                pass
                            elif ch in "+*/=,;":
                                break
                        i += 1
                    arg = expr[arg_start:i].strip()
                    if arg:
                        out.append(arg)
                    out.append(")")
            else:
                out.append(expr[i])
                i += 1
        
        return "".join(out)

    def _rewrite_abs(self, expr: str) -> str:
        """
        Convert |x-3| into Abs(x-3). Handles absolute values.
        Simple pairing: each | alternates between opening and closing Abs.
        For ||x|| (nested), treat as Abs(Abs(x)).
        """
        out = []
        i = 0
        n = len(expr)
        # Simple state: True = inside Abs, False = outside
        inside_abs = False

        while i < n:
            ch = expr[i]
            if ch == "|":
                if not inside_abs:
                    # Opening bar
                    out.append("Abs(")
                    inside_abs = True
                else:
                    # Closing bar
                    out.append(")")
                    inside_abs = False
            else:
                out.append(ch)
            i += 1

        # Close any unmatched opening bars
        if inside_abs:
            out.append(")")

        return "".join(out)

    def _normalize_function_powers(self, expr: str) -> str:
        """
        Transform patterns like sin^2(x) into (sin(x))**2 so Sympy understands them.
        Only handles powers 2 and 3 for simple function names.
        """
        out = []
        i = 0
        n = len(expr)
        while i < n:
            # Look for a name followed by ^2( or ^3(
            if expr[i].isalpha():
                start = i
                while i < n and expr[i].isalpha():
                    i += 1
                name = expr[start:i]
                if i + 3 <= n and expr[i] == "^" and expr[i + 2] == "(" and expr[i + 1] in {"2", "3"}:
                    power = expr[i + 1]
                    # Find matching closing parenthesis for this "("
                    open_paren_index = i + 2
                    depth = 0
                    j = open_paren_index
                    while j < n:
                        if expr[j] == "(":
                            depth += 1
                        elif expr[j] == ")":
                            depth -= 1
                            if depth == 0:
                                break
                        j += 1
                    if j < n and depth == 0:
                        # We have name^p( ... ) -> (name( ... ))**p
                        inner = expr[open_paren_index : j + 1]
                        out.append(f"({name}{inner})**{power}")
                        i = j + 1
                        continue
                    # If we fail to find a match, fall through and treat normally
                out.append(name)
            else:
                out.append(expr[i])
                i += 1
        return "".join(out)

    def _rewrite_integrals(self, expr: str) -> str:
        """
        Rewrite occurrences of int[a,b] f(x) into IntDef(a,b,f(x)) so that
        definite integrals can be used inside larger expressions:
          (int[0,1] x^2) + 8
        """
        out = []
        i = 0
        n = len(expr)

        while i < n:
            j = expr.find("int[", i)
            if j == -1:
                out.append(expr[i:])
                break

            out.append(expr[i:j])

            # Parse bounds inside [...]
            k = j + 4
            depth = 1
            while k < n and depth > 0:
                if expr[k] == "[":
                    depth += 1
                elif expr[k] == "]":
                    depth -= 1
                k += 1
            if depth != 0:
                # Unbalanced, just copy rest and stop rewriting
                out.append(expr[j:])
                break

            bounds_str = expr[j + 4 : k - 1].strip()

            # Skip whitespace after ]
            func_start = k
            while func_start < n and expr[func_start].isspace():
                func_start += 1

            # Capture integrand up to the next top-level operator or end
            paren_depth = 0
            t = func_start
            while t < n:
                ch = expr[t]
                if ch == "(":
                    paren_depth += 1
                elif ch == ")":
                    if paren_depth == 0:
                        break
                    paren_depth -= 1
                elif ch in "+-*/^" and paren_depth == 0:
                    break
                t += 1

            func_str = expr[func_start:t].strip()
            if not bounds_str or not func_str:
                # Fallback: don't rewrite if something looks wrong
                out.append(expr[j:t])
            else:
                out.append(f"IntDef({bounds_str}, {func_str})")

            i = t

        return "".join(out)

    def _replace_round_calls(self, expr: str) -> str:
        """
        Replace occurrences of round(n) inside a larger expression with the
        numeric value of rounding ans to n decimals, so you can do:
          round(2) + 1
        """
        out = ""
        i = 0
        n = len(expr)
        while i < n:
            if expr.startswith("round(", i):
                # Find matching ')'
                start = i + 6
                depth = 1
                j = start
                while j < n and depth > 0:
                    if expr[j] == "(":
                        depth += 1
                    elif expr[j] == ")":
                        depth -= 1
                    j += 1
                if depth != 0:
                    # Unbalanced, just copy and move on
                    out += expr[i]
                    i += 1
                    continue

                inner = expr[start : j - 1].strip() or "0"
                try:
                    value, _ = self._compute_rounded_ans(inner)
                    out += str(value)
                except Exception:
                    # If rounding fails (e.g. no ans yet), keep original text
                    out += expr[i:j]
                i = j
            else:
                out += expr[i]
                i += 1
        return out

    def _sympy_local_dict(self):
        # Map of safe names used in eval
        x = self.sym_x or sp.symbols("x")
        ans_value = self.last_result if self.last_result is not None else 0
        theta = sp.symbols("theta")

        def round_ans(n):
            """round(ans) to n decimal places; 0 => no decimals (int string)."""
            try:
                dec = int(float(n))
            except Exception:  # noqa: BLE001
                dec = 0

            val = ans_value
            try:
                v = float(val)
            except Exception:  # noqa: BLE001
                try:
                    v = float(sp.N(val))
                except Exception:  # noqa: BLE001
                    v = 0.0

            if dec <= 0:
                # No decimals: integer string
                return str(int(round(v)))
            # Fixed number of decimals
            return f"{round(v, dec):.{dec}f}"

        def IntDef(a, b, expr):
            """
            Helper used by _rewrite_integrals so int[a,b] f(x) can be
            embedded inside larger expressions.
            Chooses the integration variable from expr.free_symbols when possible.
            """
            free = list(expr.free_symbols)
            if free:
                var = free[0]
            else:
                var = x
            return sp.integrate(expr, (var, a, b))

        def to_deg(val):
            return sp.N(val) * 180 / sp.pi

        def to_rad(val):
            return sp.N(val) * sp.pi / 180

        def mod(a, b):
            return a % b

        return {
            "x": x,
            "pi": sp.pi,
            "e": sp.E,
            "C": sp.Symbol("C"),
            "theta": theta,
            "θ": theta,
            "ans": ans_value,
            "gcd": sp.gcd,
            "lcm": sp.lcm,
            "isprime": sp.isprime,
            "factorint": sp.factorint,
            "to_deg": to_deg,
            "to_rad": to_rad,
            "mod": mod,
            "sin": sp.sin,
            "cos": sp.cos,
            "tan": sp.tan,
            "asin": sp.asin,
            "acos": sp.acos,
            "atan": sp.atan,
            "sinh": sp.sinh,
            "cosh": sp.cosh,
            "tanh": sp.tanh,
            "sqrt": sp.sqrt,
            "log": sp.log,
            "exp": sp.exp,
            "Abs": sp.Abs,
            "Matrix": sp.Matrix,
            "IntDef": IntDef,
            # Common aliases
            "arcsin": sp.asin,
            "arccos": sp.acos,
            "arctan": sp.atan,
        }

    def _format_result(self, result):
        # If user-handled string (e.g. from round()), just show as-is
        if isinstance(result, str):
            return self._prettify_result_str(result)

        # Plain Python numbers: no decimal for whole numbers
        if isinstance(result, (int, float)):
            if isinstance(result, int) or result == int(result):
                return str(int(result))
            s = f"{result}"
            if "." in s:
                s = s.rstrip("0").rstrip(".")
            return s

        # Sympy Rational (e.g. from frac): show as fraction (1/2), not 0.5
        if isinstance(result, (sp.Rational, sp.Integer)):
            return str(result)

        # Keep simple sqrt (e.g. sqrt(3)) symbolic to avoid long decimals
        if isinstance(result, sp.Pow) and result.exp == sp.S.Half and result.base.is_number:
            if result.base.is_Integer or result.base.is_Rational:
                return self._prettify_result_str(str(result))

        # Sympy numbers / expressions
        try:
            numeric = result.evalf(12)
            s = f"{numeric}"
            # Whole number: no decimal
            try:
                if float(s) == int(float(s)):
                    s = str(int(float(s)))
                elif "." in s:
                    s = s.rstrip("0").rstrip(".")
            except (ValueError, TypeError):
                pass
            return self._prettify_result_str(s)
        except Exception:  # noqa: BLE001
            s = str(result)
            return self._prettify_result_str(s)

    def _prettify_result_str(self, s: str) -> str:
        """Superscripts, whole numbers without decimal, coefficient*var -> coefficient var, log -> ln."""
        # Whole-number floats: 6.0 -> 6, -2.0 -> -2
        s = re.sub(r"(-?\d+)\.0+(?=\D|$)", r"\1", s)
        # Coefficient * single variable -> implicit: 6*x -> 6x, -2*theta -> -2theta
        s = re.sub(r"(-?\d+)\*([A-Za-z]\w*)", r"\1\2", s)
        # SymPy uses log for natural log; display as ln to match input
        s = s.replace("log(", "ln(")
        return (
            s.replace("**2", "²")
            .replace("**3", "³")
            .replace("^2", "²")
            .replace("^3", "³")
        )


def main():
    app = SciCalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

