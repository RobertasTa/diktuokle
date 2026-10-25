# -*- coding: utf-8 -*-
"""Ar programa nelustu ne Windows sistemoje (2026-09-12).

Roberto klausimas: *"ta musu diktuokle netycia ant obuolio neveiktu?"*
Atsakymas buvo NE, ir pagrindine priezastis - VIENA eilute: vienintelio
egzemplioriaus uzraktas krepesi i `ctypes.windll`, kurio ne Windows sistemose
NERA IS VISO. Programa mirdavo su AttributeError dar PRIES atsirandant langui,
be jokio zenklo zmogui.

Si patikra saugo butent nuo to. Ji STATINE (skaito koda, nepaleidzia programos),
nes Mac kompiuterio neturim - ant Windows paleisti macOS saku neimanoma.

Tikrinam:
  P1. kiekvienas `ctypes.windll` yra arba `try/except` viduje, arba po
      `if sys.platform == "win32"`;
  P2. kiekvienas modulis, minintis `sys.platform`, ta `sys` ir importuoja;
  P3. paleidiklio klavisas ir iklijavimo klavisas turi macOS saka.

LEISTI: python patikra_platformu.py
"""
import ast
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

CIA = os.path.dirname(os.path.abspath(__file__))
FAILAI = ("diktuokle.py", "cuda.py", "lt_dictation_paprika.py", "kalba.py")

klaidos = []


def _medis(failas):
    with open(os.path.join(CIA, failas), encoding="utf-8") as fh:
        return ast.parse(fh.read()), fh


def _win32_salyga(testas):
    """Ar `if` salyga yra `sys.platform == "win32"` (ar != kitos sistemos)."""
    for mazgas in ast.walk(testas):
        if (isinstance(mazgas, ast.Attribute) and mazgas.attr == "platform"
                and isinstance(mazgas.value, ast.Name) and mazgas.value.id == "sys"):
            return True
    return False


# Ne Windows sistemoje `ctypes.windll` meta AttributeError. Ji pagauna TIK sie:
PLATUS_GAUDYTOJAI = {"Exception", "BaseException", "AttributeError"}


def _tikras_gaudytojas(mazgas):
    """Ar `try` blokas tikrai pagauna AttributeError.

    ⚠️ Cia buvo si patikros versijos klaida: `except OSError` atrodo kaip
    apsauga, bet AttributeError PRALEIDZIA. Butent taip apsirikti lengviausia.
    """
    for tvarkytojas in mazgas.handlers:
        if tvarkytojas.type is None:            # bare `except:`
            return True
        tipai = (tvarkytojas.type.elts if isinstance(tvarkytojas.type, ast.Tuple)
                 else [tvarkytojas.type])
        for tipas in tipai:
            if isinstance(tipas, ast.Name) and tipas.id in PLATUS_GAUDYTOJAI:
                return True
    return False


def _iseina(kunas):
    """Ar sakos kunas BAIGIA funkcija (return / raise / sys.exit)."""
    for dalis in kunas:
        if isinstance(dalis, (ast.Return, ast.Raise)):
            return True
        if (isinstance(dalis, ast.Expr) and isinstance(dalis.value, ast.Call)
                and isinstance(dalis.value.func, ast.Attribute)
                and dalis.value.func.attr == "exit"):
            return True
    return False


def _saugomos_eilutes(medis):
    """Eiluciu numeriai, kurie guli sys.platform sakoje arba try bloke,
    TIKRAI gaudanciame AttributeError."""
    saugios = set()
    for mazgas in ast.walk(medis):
        kunai = []
        if isinstance(mazgas, ast.Try) and _tikras_gaudytojas(mazgas):
            kunai = mazgas.body
        elif isinstance(mazgas, ast.If) and _win32_salyga(mazgas.test):
            kunai = mazgas.body
        for dalis in kunai:
            pr = getattr(dalis, "lineno", None)
            pb = getattr(dalis, "end_lineno", None)
            if pr and pb:
                saugios.update(range(pr, pb + 1))

    # ANKSTYVAS GRIZIMAS: `if sys.platform != "win32": return ...` funkcijos
    # pradzioje saugo VISA likusi funkcijos kuna, nors tas kunas guli UZ `if`.
    # Be sios dalies patikra melagingai kaltintu teisinga koda (taip ir nutiko
    # pirma karta su `cuda.plokste_yra`).
    for mazgas in ast.walk(medis):
        if not isinstance(mazgas, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dalis in mazgas.body:
            if (isinstance(dalis, ast.If) and _win32_salyga(dalis.test)
                    and _iseina(dalis.body)):
                saugios.update(range(dalis.end_lineno + 1, mazgas.end_lineno + 1))
    return saugios


print("P1. Ar kiekvienas `ctypes.windll` apsaugotas")
for failas in FAILAI:
    medis, _ = _medis(failas)
    saugios = _saugomos_eilutes(medis)
    for mazgas in ast.walk(medis):
        if (isinstance(mazgas, ast.Attribute) and mazgas.attr == "windll"):
            if mazgas.lineno in saugios:
                print("   OK   %s:%d" % (failas, mazgas.lineno))
            else:
                klaidos.append("%s:%d - `ctypes.windll` BE APSAUGOS: ne Windows "
                               "sistemoje mes AttributeError" % (failas, mazgas.lineno))
                print("   ⛔   %s:%d BE APSAUGOS" % (failas, mazgas.lineno))

print("\nP2. Ar `sys` importuotas ten, kur minimas `sys.platform`")
for failas in FAILAI:
    medis, _ = _medis(failas)
    tekstas = open(os.path.join(CIA, failas), encoding="utf-8").read()
    if "sys.platform" not in tekstas:
        continue
    importuota = any(
        isinstance(m, ast.Import) and any(a.name == "sys" for a in m.names)
        for m in ast.walk(medis))
    if importuota:
        print("   OK   %s" % failas)
    else:
        klaidos.append("%s - naudoja sys.platform, bet neimportuoja sys" % failas)
        print("   ⛔   %s" % failas)

print("\nP3. Ar yra macOS sakos ten, kur klavisai skiriasi")
tikrinti = {
    "lt_dictation_paprika.py": ("TRIGGER_KEY", "paleidiklio klavisas"),
    "diktuokle.py": ("klijuok", "iklijavimo klavisas"),
}
for failas, (vardas, aprasas) in tikrinti.items():
    tekstas = open(os.path.join(CIA, failas), encoding="utf-8").read()
    if "darwin" in tekstas and vardas in tekstas:
        print("   OK   %-28s %s" % (aprasas, failas))
    else:
        klaidos.append("%s - %s neturi macOS ('darwin') sakos" % (failas, aprasas))
        print("   ⛔   %-28s %s" % (aprasas, failas))

print("\n" + "=" * 70)
if klaidos:
    print("KLAIDU: %d" % len(klaidos))
    for k in klaidos:
        print("  - " + k)
    sys.exit(1)
print("VISOS PLATFORMU PATIKROS PRAEJO")
