# -*- coding: utf-8 -*-
"""cuda.py - vaizdo plokstes bibliotekos, parsisiunciamos pagal poreiki.

Kodel sis modulis egzistuoja (2026-09-11, Roberto testas): pakete CUDA
bibliotekos NEDEDAMOS - 1,6 GB (cuBLAS 736 MB + cuDNN 904 MB), o NVIDIA turi
mazuma. Bet be ju net geriausia plokste yra nematoma: ctranslate2 modeli i ja
UZKRAUNA, o pirmo atpazinimo metu meta "cublas64_12.dll is not found". Robertas
su gera NVIDIA gavo procesoriaus greiti (3 s vietoj 0,15 s) ir teisingai
paklause, kodel.

Sprendimas - tas pats, kaip su kalbu modeliais: programa PATI aptinka plokste,
pasiulo parsisiusti bibliotekas VIENA karta, ir nuo kito paleidimo sukasi ant
plokstes. Kas plokstes neturi, nesiuncia nė megabaito ir apie tai nesuzino.

Is kur imam: tos pacios PyPI pakuotes, kurias naudoja pip (nvidia-cublas-cu12,
nvidia-cudnn-cu12), tik be pip - wheel yra paprastas zip, is jo istraukiam TIK
11 DLL failu. Versijos = tos, kurios veikia Roberto venv'e su ctranslate2 4.7.1.
"""
import ctypes
import io
import json
import os
import urllib.request
import zipfile

# Versijos PRIRISTOS prie ctranslate2 4.7.1 (CUDA 12 + cuDNN 9). Keiciant
# ctranslate2 - tikrinti, ar tinka.
PAKUOTES = (
    ("nvidia-cublas-cu12", "12.9.2.10"),
    ("nvidia-cudnn-cu12", "9.20.0.48"),
)
DYDIS_MB = 1650     # apvalinta i didesne puse, kad zmogus nenustebtu

# Sie 11 failu - VISKAS, ko reikia. Wheel'uose yra ir daugiau (includes, libs),
# bet ctranslate2 kreipiasi tik i DLL.
REIKALINGI_DLL = {
    "cublas64_12.dll", "cublasLt64_12.dll", "nvblas64_12.dll",
    "cudnn64_9.dll", "cudnn_adv64_9.dll", "cudnn_cnn64_9.dll",
    "cudnn_engines_precompiled64_9.dll", "cudnn_engines_runtime_compiled64_9.dll",
    "cudnn_graph64_9.dll", "cudnn_heuristic64_9.dll", "cudnn_ops64_9.dll",
}


def _duomenu_katalogas():
    cia = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(cia, "Diktuokle_portable.txt")):
        return os.path.join(cia, "Diktuokle_data")
    base = os.environ.get("LOCALAPPDATA")
    return os.path.join(base, "Diktuokle") if base else os.path.join(cia, "Diktuokle_data")


CUDA_KATALOGAS = os.path.join(_duomenu_katalogas(), "cuda")


def plokste_yra():
    """Ar kompiuteryje yra NVIDIA tvarkykle. nvcuda.dll ateina su tvarkykle,
    ne su musu programa - jei jo nera, plokstes arba nera, arba ji be tvarkyklių,
    ir abiem atvejais siulyti 1,6 GB butu nesamone."""
    try:
        ctypes.windll.LoadLibrary("nvcuda.dll")
        return True
    except OSError:
        return False


def bibliotekos_yra():
    """Ar visi 11 DLL jau parsisiusti. Tikrinam KIEKVIENA, ne kataloga: pusiau
    parsisiustas rinkinys atrodytu kaip pilnas ir luztu vidury darbo."""
    return all(os.path.isfile(os.path.join(CUDA_KATALOGAS, f)) for f in REIKALINGI_DLL)


def ijunk():
    """Prideda CUDA kataloga ten, kur Windows iesko DLL. Kviesti PRIES kraunant
    modelius. Abu budai, nes ctranslate2 krauna DLL per LoadLibrary (ziuri PATH),
    o Python 3.8+ savo isplėtimams ziuri add_dll_directory."""
    if not bibliotekos_yra():
        return False
    os.environ["PATH"] = CUDA_KATALOGAS + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(CUDA_KATALOGAS)
    except (OSError, AttributeError):
        pass
    return True


def _wheel_url(pakuote, versija):
    with urllib.request.urlopen(f"https://pypi.org/pypi/{pakuote}/{versija}/json",
                                timeout=60) as a:
        d = json.load(a)
    for u in d["urls"]:
        if "win_amd64" in u["filename"]:
            return u["url"], u["size"]
    raise RuntimeError(f"{pakuote} {versija}: Windows wheel nerastas PyPI")


def parsisiusk(pranesk=None):
    """Parsisiunčia abu wheel'us ir istraukia tik DLL. `pranesk(tekstas)` -
    busenos eilutei. Wheel'as krauna i atminti (~700-900 MB) - priimtina
    vienkartiniam veiksmui, uztat diske nelieka 1,6 GB laikinu zip'u."""
    os.makedirs(CUDA_KATALOGAS, exist_ok=True)
    for pakuote, versija in PAKUOTES:
        url, dydis = _wheel_url(pakuote, versija)
        if pranesk:
            pranesk(f"{pakuote} ({dydis / 1e6:.0f} MB)")
        with urllib.request.urlopen(url, timeout=600) as a:
            duomenys = a.read()
        with zipfile.ZipFile(io.BytesIO(duomenys)) as z:
            for narys in z.namelist():
                vardas = os.path.basename(narys)
                if vardas in REIKALINGI_DLL and narys.endswith(".dll"):
                    with z.open(narys) as src, \
                         open(os.path.join(CUDA_KATALOGAS, vardas), "wb") as dst:
                        dst.write(src.read())
    return bibliotekos_yra()
