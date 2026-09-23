"""Swiz - kleine eigene Programmiersprache. Interpreter in Python.
Start: python swiz.py beispiel.swz
Keywords: let, show, if, else, while, func, return, true, false
"""
import sys

SWIZ_VERSION = "0.0.2"

# ---------- Lexer ----------
KEYWORDS = {"let", "show", "if", "else", "while", "func", "return", "true", "false"}

class Tok:
    def __init__(self, kind, val, line):
        self.kind, self.val, self.line = kind, val, line
    def __repr__(self):
        return f"Tok({self.kind},{self.val!r})"

def lex(src):
    toks, i, line, n = [], 0, 1, len(src)
    while i < n:
        c = src[i]
        if c == "\n":
            toks.append(Tok("NL", c, line)); line += 1; i += 1
        elif c in " \t\r;":
            i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == '"':
            j = i + 1; s = ""
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    s += {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(src[j + 1], src[j + 1])
                    j += 2
                else:
                    s += src[j]; j += 1
            j += 1
            toks.append(Tok("STR", s, line)); i = j
        elif c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."):
                j += 1
            t = src[i:j]
            toks.append(Tok("NUM", float(t) if "." in t else int(t), line)); i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            w = src[i:j]
            toks.append(Tok("ID" if w not in KEYWORDS else w.upper(), w, line)); i = j
        elif src[i:i + 2] in ("==", "!=", "<=", ">=", "&&", "||"):
            toks.append(Tok("OP", src[i:i + 2], line)); i += 2
        elif c in "+-*/%=<>(){},!":
            toks.append(Tok("OP" if c in "+-*/%=<>!" else c, c, line)); i += 1
        else:
            raise SyntaxError(f"Zeichen '{c}' unerwartet (Zeile {line})")
    toks.append(Tok("EOF", None, line))
    return toks

# ---------- Parser ----------
class P:
    def __init__(self, toks):
        self.t, self.i = toks, 0
    def pk(self):
        return self.t[self.i]
    def nx(self):
        t = self.t[self.i]; self.i += 1; return t
    def exp(self, kind, val=None):
        t = self.nx()
        if t.kind != kind or (val is not None and t.val != val):
            raise SyntaxError(f"{val or kind} erwartet, {t.val!r} gefunden (Zeile {t.line})")
        return t
    def skip_nl(self):
        while self.pk().kind == "NL":
            self.nx()

    def program(self):
        self.skip_nl(); ss = []
        while self.pk().kind != "EOF":
            ss.append(self.stmt()); self.skip_nl()
        return ("prog", ss)

    def stmt(self):
        k = self.pk()
        if k.kind == "LET":
            self.nx(); name = self.exp("ID").val; self.exp("OP", "="); e = self.expr()
            return ("let", name, e)
        if k.kind == "SHOW":
            self.nx(); return ("show", self.expr())
        if k.kind == "IF":
            self.nx(); c = self.expr(); a = self.block()
            b = None
            self.skip_nl()
            if self.pk().kind == "ELSE":
                self.nx(); b = self.block()
            return ("if", c, a, b)
        if k.kind == "WHILE":
            self.nx(); c = self.expr(); return ("while", c, self.block())
        if k.kind == "FUNC":
            self.nx(); name = self.exp("ID").val; self.exp("(", "(")
            ps = []
            if self.pk().kind != ")":
                ps.append(self.exp("ID").val)
                while self.pk().kind == ",":
                    self.nx(); ps.append(self.exp("ID").val)
            self.exp(")", ")")
            return ("func", name, ps, self.block())
        if k.kind == "RETURN":
            self.nx(); return ("ret", self.expr())
        e = self.expr()
        return ("expr", e)

    def block(self):
        self.skip_nl(); self.exp("{", "{"); self.skip_nl(); ss = []
        while self.pk().kind != "}":
            ss.append(self.stmt()); self.skip_nl()
        self.exp("}", "}")
        return ss

    def expr(self):
        return self.logic_or()
    def logic_or(self):
        return self.binop(self.logic_and, ("||",))
    def logic_and(self):
        return self.binop(self.equality, ("&&",))
    def equality(self):
        return self.binop(self.compare, ("==", "!="))
    def compare(self):
        return self.binop(self.add, ("<", ">", "<=", ">="))
    def add(self):
        return self.binop(self.mul, ("+", "-"))
    def mul(self):
        return self.binop(self.unary, ("*", "/", "%"))
    def binop(self, sub, ops):
        left = sub()
        while self.pk().kind == "OP" and self.pk().val in ops:
            op = self.nx().val; left = ("bin", op, left, sub())
        return left
    def unary(self):
        if self.pk().kind == "OP" and self.pk().val in ("-", "!"):
            op = self.nx().val; return ("un", op, self.unary())
        return self.call()
    def call(self):
        node = self.atom()
        while self.pk().kind == "(":
            self.nx(); args = []
            if self.pk().kind != ")":
                args.append(self.expr())
                while self.pk().kind == ",":
                    self.nx(); args.append(self.expr())
            self.exp(")", ")")
            node = ("call", node, args)
        return node
    def atom(self):
        t = self.nx()
        if t.kind in ("NUM", "STR"):
            return ("lit", t.val)
        if t.kind == "TRUE":
            return ("lit", True)
        if t.kind == "FALSE":
            return ("lit", False)
        if t.kind == "ID":
            return ("var", t.val)
        if t.kind == "(":
            e = self.expr(); self.exp(")", ")"); return e
        raise SyntaxError(f"Ausdruck erwartet, {t.val!r} gefunden (Zeile {t.line})")

# ---------- Interpreter ----------
class Return(Exception):
    def __init__(self, val):
        self.val = val

class Env:
    def __init__(self, parent=None):
        self.v, self.p = {}, parent
    def get(self, n):
        if n in self.v:
            return self.v[n]
        if self.p:
            return self.p.get(n)
        raise NameError(f"Unbekannte Variable '{n}'")
    def set(self, n, v):
        self.v[n] = v

def truthy(v):
    return v not in (False, 0, "", None)

def ev(node, env):
    k = node[0]
    if k == "prog":
        for s in node[1]:
            ev(s, env)
    elif k == "let":
        env.set(node[1], ev(node[2], env))
    elif k == "show":
        v = ev(node[1], env)
        print(v if not isinstance(v, bool) else str(v).lower())
    elif k == "if":
        if truthy(ev(node[1], env)):
            run_block(node[2], env)
        elif node[3] is not None:
            run_block(node[3], env)
    elif k == "while":
        while truthy(ev(node[1], env)):
            run_block(node[2], env)
    elif k == "func":
        env.set(node[1], ("fn", node[2], node[3], env))
    elif k == "ret":
        raise Return(ev(node[1], env))
    elif k == "expr":
        ev(node[1], env)
    elif k == "lit":
        return node[1]
    elif k == "var":
        return env.get(node[1])
    elif k == "un":
        v = ev(node[2], env)
        return -v if node[1] == "-" else (not truthy(v))
    elif k == "bin":
        a, b = ev(node[2], env), ev(node[3], env); op = node[1]
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        if op == "%":
            return a % b
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        if op == "&&":
            return truthy(a) and truthy(b)
        if op == "||":
            return truthy(a) or truthy(b)
    elif k == "call":
        fn = ev(node[1], env)
        if not (isinstance(fn, tuple) and fn[0] == "fn"):
            raise TypeError("Nicht aufrufbar")
        _, ps, body, clo = fn
        args = [ev(a, env) for a in node[2]]
        if len(args) != len(ps):
            raise TypeError(f"{len(ps)} Argumente erwartet, {len(args)} gegeben")
        local = Env(clo)
        for p, a in zip(ps, args):
            local.set(p, a)
        try:
            run_block(body, local)
        except Return as r:
            return r.val
        return None

def run_block(stmts, env):
    for s in stmts:
        ev(s, env)

def run_file(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    ev(P(lex(src)).program(), Env())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Start: python swiz.py <datei.swz>")
    elif sys.argv[1] in ("--version", "-v"):
        print(f"Swiz {SWIZ_VERSION}")
    else:
        run_file(sys.argv[1])
