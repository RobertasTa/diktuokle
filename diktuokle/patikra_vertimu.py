# -*- coding: utf-8 -*-
"""Patikra: ar kiekvienas lange naudojamas t() raktas turi vertima.

Kodel skriptu, o ne akimis: raktas yra PATS lietuviskas sakinys, tad uztenka
vieno pakeisto kablelio ar tarpo, ir vertimas tyliai nustoja veikti - programa
nesulus, tik parodys lietuviska eilute rusiskoje sasajoje. Toki gedima akimis
pagauna tik tas, kuris ta kalba skaito.

Skaito AST, ne regexp: daugiaeiliai t("..." "...") sulipdomi taip pat, kaip tai
daro pats Python, todel raktas gaunasi tiksliai toks, koks bus vykdymo metu.

Paleidimas:  python patikra_vertimu.py
"""
import ast
import io
import os
import sys

CIA = os.path.dirname(os.path.abspath(__file__))
TIKRINAMI = ["diktuokle.py"]


def surink_raktus(failas):
    """Visi t("...") argumentai faile. Nekonstantinius (t(kintamasis)) praleidzia
    ir apie juos pranesa atskirai - ju patikrinti statiskai neimanoma."""
    su_konstanta, su_kintamuoju = [], []
    medis = ast.parse(io.open(failas, encoding="utf-8").read(), failas)
    for mazgas in ast.walk(medis):
        if not isinstance(mazgas, ast.Call):
            continue
        if not (isinstance(mazgas.func, ast.Name) and mazgas.func.id == "t"):
            continue
        if not mazgas.args:
            continue
        arg = mazgas.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            su_konstanta.append((mazgas.lineno, arg.value))
        else:
            su_kintamuoju.append(mazgas.lineno)
    return su_konstanta, su_kintamuoju


def main():
    sys.path.insert(0, CIA)
    import kalba

    visi, kintami = [], []
    for f in TIKRINAMI:
        k, kt = surink_raktus(os.path.join(CIA, f))
        visi += [(f, eil, r) for eil, r in k]
        kintami += [(f, eil) for eil in kt]

    unikalus = sorted({r for _, _, r in visi})
    print(f"Rasta t() iskvietimu: {len(visi)}, unikaliu raktu: {len(unikalus)}")
    if kintami:
        print(f"⚠️  t() su kintamuoju (statiskai netikrinami): {kintami}")

    blogai = 0
    for kodas in ("ru", "en"):
        zod = kalba._ZODYNAI[kodas]
        truksta = [r for r in unikalus if r not in zod]
        tusti = [r for r in unikalus if zod.get(r, "x").strip() == ""]
        print(f"\n[{kodas}] zodyne {len(zod)} irasu, truksta {len(truksta)}")
        for r in truksta:
            print("   TRUKSTA:", repr(r[:70]))
        for r in tusti:
            print("   TUSCIAS:", repr(r[:70]))
        blogai += len(truksta) + len(tusti)

    # Atvirkscia puse: zodyne guli raktas, kurio kode nebera (liko po pakeitimo).
    for kodas in ("ru", "en"):
        nebenaudojami = [r for r in kalba._ZODYNAI[kodas] if r not in unikalus]
        if nebenaudojami:
            print(f"\n[{kodas}] zodyne yra {len(nebenaudojami)} raktu, kuriu kode NEBERA:")
            for r in nebenaudojami:
                print("   NEBENAUDOJAMAS:", repr(r[:70]))

    print("\n" + ("VISI VERTIMAI VIETOJE" if blogai == 0 else f"PROBLEMU: {blogai}"))
    return 1 if blogai else 0


if __name__ == "__main__":
    sys.exit(main())
