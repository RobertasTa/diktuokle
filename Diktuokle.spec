# -*- mode: python ; coding: utf-8 -*-
"""Diktuokle - PyInstaller receptas.

Statyti IS SIO katalogo ir VISADA per `python -m PyInstaller` (seimos pamoka:
venv shim'ai luzta):

    "..\\..\\Vois ASISTENT piton\\.venv\\Scripts\\python.exe" -m PyInstaller Diktuokle.spec --noconfirm

SPRENDIMAI:
  * ONEDIR, ne onefile (seimos sprendimas 15). onefile kaskart isspakuotu ~900 MB
    i temp - langas atsidarytu ne per sekunde, o per minute.
  * CUDA I PAKETA NEDEDAM. Su ja paketas iseitu +2 GB, o NVIDIA turi mazuma.
    Programa turi automatini kritima i procesoriu (zr. `_krauk_modelius`):
    leciau (~3 s sakiniui pries 0,15 s), bet veikia visiems. Kas turi NVIDIA ir
    nori greicio - README pasako, kaip paleisti is saltiniu.
  * MODELIU PAKETE NERA. Jie sveria 2-5 GB ir parsisiunciami pirmo paleidimo
    metu pagal tai, kurias kalbas zmogus pazymejo diegdamas.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

KATALOGAS = "diktuokle"

# torch itraukiamas VISAS: ji tempia `punctuators` kraunant skyrybos modeli
# (pamatuota 2026-09-11 - `import punctuators` jo neuztraukia, o modelio
# krovimas uztraukia). Diske jis 0,53 GB, ne 2 GB, kaip buvo spėta plane.
torch_d, torch_b, torch_h = collect_all("torch")
punct_d, punct_b, punct_h = collect_all("punctuators")
ct2_d, ct2_b, ct2_h = collect_all("ctranslate2")
ort_d, ort_b, ort_h = collect_all("onnxruntime")
fw_d, fw_b, fw_h = collect_all("faster_whisper")
hf_d, hf_b, hf_h = collect_all("huggingface_hub")
sp_d, sp_b, sp_h = collect_all("sentencepiece")
om_d, om_b, om_h = collect_all("omegaconf")

a = Analysis(
    [f"{KATALOGAS}/diktuokle.py"],
    pathex=[KATALOGAS],
    binaries=torch_b + punct_b + ct2_b + ort_b + fw_b + hf_b + sp_b + om_b,
    datas=[
        (f"{KATALOGAS}/Diktuokle.ico", "."),
        (f"{KATALOGAS}/README.txt", "."),
    ] + torch_d + punct_d + ct2_d + ort_d + fw_d + hf_d + sp_d + om_d,
    hiddenimports=(
        # Musu pačiu moduliai - PyInstaller juos randa per importus, bet
        # `parsisiuntimas` ir `modeliai` kraunami VELAI (funkciju viduje), tad
        # nurodom aiskiai.
        ["kalba", "modeliai", "parsisiuntimas", "punct_restore",
         "lt_dictation_paprika", "cuda"]
        + torch_h + punct_h + ct2_h + ort_h + fw_h + hf_h + sp_h + om_h
        + collect_submodules("pynput")
    ),
    hookspath=[],
    runtime_hooks=[],
    # Ko NEREIKIA: CUDA bibliotekos (zr. auksciai), tkinter (senoji versija jo
    # naudojo, naujasis langas - PyQt6), matplotlib ir kt. moksliniai paketai,
    # kuriuos torch tempia del vidiniu importu.
    excludes=["nvidia", "tkinter", "matplotlib", "scipy", "pandas",
              "PIL", "IPython", "notebook", "pytest", "transformers"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Diktuokle",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX + antivirusai = false positive; seimos taisykle
    console=False,      # langinis; jei krenta be pranesimo - laikinai True
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=f"{KATALOGAS}/Diktuokle.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Diktuokle",
)
