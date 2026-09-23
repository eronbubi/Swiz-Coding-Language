# Swiz – unsere eigene kleine Programmiersprache

**Version 0.0.2** · Lauffähiger Baum-Interpreter in Python (eine Datei, keine Abhängigkeiten).

## Start

```bash
python swiz/swiz.py swiz/beispiel.swz
```

## Beispiel

```swiz
let x = 5
show x + 3

if x > 3 {
  show "x ist gross"
} else {
  show "x ist klein"
}

while x > 0 {
  show x
  let x = x - 1
}

func fak(n) {
  if n <= 1 {
    return 1
  }
  return n * fak(n - 1)
}
show fak(6)
```

## Kann schon

Variablen (`let`), Rechnen (`+ - * / %`), Vergleiche, `&&`/`||`/`!`,
Strings, `if/else`, `while`, Funktionen mit `return` (inkl. Rekursion), `//`-Kommentare.

## Noch nicht (Roadmap)

`for`, Listen, `input`, Datei-I/O, Module, bessere Fehlermeldungen.
