# Calc – Short for Calculator

A small, dark-themed scientific calculator written in Python with a history pane and an input bar at the bottom. It supports scientific functions, brackets, integrals (definite and indefinite), derivatives, limits, equation solving, user variables, and compact math-like syntax that is rendered as pretty symbols in the history.

## Setup

From the `calculator` folder:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The app opens a compact dark window:

- Top: history of past calculations (auto-scrolls as you compute).
- Bottom: single-line text input (auto-focused; press Enter to evaluate).

**Project layout:** `main.py` (entry), `src/` (app code), `assets/` (logo), `scripts/` (icon build), `packaging/` (PyInstaller), `docs/` (e.g. [docs/BUILD.md](docs/BUILD.md) for packaging).

## Input syntax

You can type expressions using a Python-like syntax:

- **Basic arithmetic**: `1+2`, `3*(4+5)`, `2^3`, `2**3`
- **Brackets**: `()`, `[]` (square brackets behave like parentheses)
- **Implicit multiplication**: `2x`, `3sin(x)`, `(x+1)(x-1)` → automatically becomes `2*x`, `3*sin(x)`, `(x+1)*(x-1)`
- **Absolute value**: `|x-3|` → `Abs(x-3)`
- **Variables**: default variable `x`; you can also use `theta` / `θ`
- **Constants**: `pi`, `e`, `theta` / `θ`, `C` (constant of integration)
- **Functions**:
  - `sqrt(2)`, `sin(pi/2)`, `cos(x)`, `tan(x)`
  - inverse trig: `asin(x)`, `acos(x)`, `atan(x)` (also `arcsin`, `arccos`, `arctan`)
  - hyperbolic: `sinh(x)`, `cosh(x)`, `tanh(x)`
  - logs/exp: `log(x)`, `ln(x)`, `exp(x)`
- **Power notation**:
  - `x^2` or `x**2`
  - `sin^2(x)`, `cos^3(x)` (parsed as \((\sin(x))^2\), \((\cos(x))^3\))

In the history view, some tokens are rendered with symbols:

- `sqrt` → `√`
- `pi` → `π`
- `theta` → `θ`
- `**2`, `^2` → `²`
- `**3`, `^3` → `³`
- `int` → `∫`
- `der` → `d/dx`

## Integrals

### Definite integrals

Syntax:

- `int[a,b] f(x)`
- optional `dx` at the end is allowed: `int[0,1] x^2 dx`
- Can be embedded in expressions: `(int[0,1] x^2) + 8`

Examples:

- `int[0,1] x^2` → computes \(\int_0^1 x^2 dx\)
- `int[0,pi] sin(x)` → computes \(\int_0^\pi \sin(x) dx\)

### Indefinite integrals

Syntax:

- `int f(x)` → returns antiderivative + C

Examples:

- `int x^2` → `x^3/3 + C`
- `int sin(x)` → `-cos(x) + C`
- Can be embedded: `(int x^2) + 1` → `x^3/3 + C + 1`

## Derivatives

Syntax:

- `der f(x)` – derivative with respect to \(x\)
- `der[y] f(y)` – derivative with respect to a custom variable (e.g. \(y\))
- `der f(x) at a` – evaluate derivative at a point

Examples:

- `der x^2` → computes \(\frac{d}{dx} x^2\)
- `der[x] sin(x)` → \(\frac{d}{dx} \sin(x)\)
- `der[y] y^3` → \(\frac{d}{dy} y^3\)
- `der x^2 at 3` → `6` (derivative evaluated at x=3)
- Can be embedded: `(der x^2 at 3) + 1` → `7`

## Limits

Syntax:

- `lim[x->a] expr` – limit as x approaches a

Examples:

- `lim[x->0] sin(x)/x` → `1`
- `lim[x->infinity] 1/x` → `0`
- Can be embedded: `(lim[x->0] sin(x)/x) + 1` → `2`

## Simplify, expand, and factor

- **Simplify**: `simp expr` – simplifies expressions
  - Example: `simp sin(x)^2 + cos(x)^2` → `1`
- **Expand**: `expand expr` – expands expressions
  - Example: `expand (x+1)^2` → `x^2 + 2*x + 1`
- **Factor**: `factor expr` – factors expressions
  - Example: `factor x^2-4` → `(x - 2)*(x + 2)`
- All can be embedded: `(simp sin(x)^2+cos(x)^2) * 2` → `2`

## Zeros of functions

Syntax (one variable only):

- `zeros x^2-4` – find real zeros of \(x^2 - 4\) (defaults to variable \(x\))
- `zeros[y] y^2-1` – find real zeros of \(y^2 - 1\)

Results are printed as e.g. `x = {-2, 2}`. If there are no real zeros, you'll see a message like `No real zeros for x.`.

## Equation solving

- **Single equation**: `solve expr=0` or `solve expr=value`
  - Example: `solve x^2=4` → `[-2, 2]`
- **System of equations**: `solve {eq1, eq2, ...}`
  - Example: `solve {x+y=5, x-y=1}` → solution set
- **With variable**: `solve[y] y^3-2=0`

## Taylor series

Syntax:

- `taylor f(x) at a order n` – Taylor series expansion

Example:

- `taylor sin(x) at 0 order 5` → polynomial expansion around 0

## User variables

You can define and use variables:

- `a = 5` – define variable `a`
- `b = a^2` – use variables in expressions
- `clearvars` – clear all user variables

Variables persist until cleared or the app is closed.

## Last answer and rounding

- **Last answer**: `ans` is always set to the last successful result.
  - Example: `2+3` → `5`, then `ans*4` → `20`.
- **Rounding**: `round(n)` rounds `ans` to exactly `n` decimal places.
  - `round(0)` → integer string with no decimals.
  - `round(2)` → two decimal places (e.g. `0.33`).
  - Can be embedded: `round(2) + 1` → uses rounded ans in expression

## Number theory functions

- `gcd(a, b)` – greatest common divisor
- `lcm(a, b)` – least common multiple
- `isprime(n)` – check if number is prime
- `factorint(n)` – prime factorization
- `mod(a, b)` – modulo operation

Examples:

- `gcd(48, 18)` → `6`
- `lcm(6, 15)` → `30`
- `isprime(97)` → `True`

## Unit conversion

- `to_deg(x)` – convert radians to degrees
- `to_rad(x)` – convert degrees to radians

Examples:

- `to_deg(pi/2)` → `90.0`
- `to_rad(90)` → `π/2`

## Embedded commands

Any command that returns a numeric or symbolic result can be embedded inside parentheses or brackets in larger expressions:

- `(der x^2 at 3) + 1` → `7`
- `(int[0,1] x^2) + 8` → `8.333...`
- `(simp sin(x)^2+cos(x)^2) * 2` → `2`
- `(lim[x->0] sin(x)/x) + 1` → `2`
- `[expand (x+1)^2] - x^2` → `2*x + 1`

## Commands and shortcuts

### Keyboard shortcuts

- **Enter**: evaluate the current expression.
- **Up / Down arrows**: cycle through previous input expressions (like shell history).
- **Ctrl+L**: clear the history pane.

### Text commands

- **`clear`** or **`clear output`**: clear the history pane (same as Ctrl+L)
- **`clearvars`**: clear all user variables
- **`save`**: save history to `history.txt` in the current directory
- **`load`**: load history from `history.txt`
- **`export latex`**: export history to `history.tex`
- **`export txt`**: export history to `history.txt`

### Help system

- **`help`** / **`h`** / **`?`**: show overview of help sections
- **`help basic`**: arithmetic, constants, functions
- **`help calc`**: integrals, derivatives, limits, zeros, solve, taylor
- **`help vars`**: ans, round, variables, history
- **`help syntax`**: notation (powers, sin^2, brackets, symbols)
- **`help ui`**: shortcuts and behavior
- **`help all`**: open full help in a new window with all features

## Input behavior

- **Starting with operator**: if you type `+2`, `-3`, `*4`, `/2`, or `^2`, it automatically uses `ans` as the left operand (e.g. `+2` becomes `ans+2`)
- **Whole numbers**: results that are whole numbers display without decimals (e.g. `6` instead of `6.0`)
- **Coefficient formatting**: expressions like `6*x` display as `6x` in results

## Output formatting

- Whole numbers display without decimals: `6` not `6.0`
- Coefficients with variables: `6*x` → `6x` in output
- Powers in output: `x**2` → `x²`, `x**3` → `x³`
- Trailing zeros are automatically trimmed from decimal results
