# -*- coding: utf-8 -*-
"""parsisiuntimas.py - ko truksta ir kaip tai atsiranda.

Kodel NE instaliatoriuje (2026-09-11 sprendimas): modeliai sveria gigabaitais,
o Inno Setup dideliems parsisiuntimams netinka - nutrukus rysiui ties 700-uoju
megabaitu zlunga visas diegimas. Programa gali pasakyti, kiek reikes, parodyti
progresa ir pakartoti nepavykus. Instaliatoriaus varneles todel daro viena
paprasta dalyka: irasо i `nustatymai.json`, kuriu kalbu zmogus nori.

Kas is kur (patikrinta per HF API 2026-09-11):
  Paprika  - musu CT2 konversija; be jos lietuviu kalba suktusi ant bendrojo
             modelio (25,95 % WER vietoj 7,63 %).
  large-v3 - `Systran/faster-whisper-large-v3`, MIT. Reikalingas rusu IR anglu
             kalboms - tas pats failas abiem.
  skyryba  - xlm-roberta ONNX, Apache-2.0. Reikalingas TIK lietuviu kalbai:
             large-v3 rusiskai ir angliskai skyryba deda pats.
"""
import os

# Langineje programoje sys.stderr gali buti None - tqdm juosta tada nuvercia
# snapshot_download (2026-09-11). diktuokle.py stderr uzkamso pirmas; sis
# kintamasis - antra apsauga, jei moduli kas nors panaudotu atskirai.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

PAPRIKA_REPO = "RobertasTa/paprika-whisper-lt-v3-ct2-int8"
LARGE_REPO = "Systran/faster-whisper-large-v3"
SKYRYBOS_REPO = "1-800-BAD-CODE/xlm-roberta_punctuation_fullstop_truecase"

# Dydziai zmogui - apvalinti i didesne puse, kad nebutu nemalonaus siurprizo.
DYDZIAI_MB = {"paprika": 820, "large": 3100, "skyryba": 1100}


def _duomenu_katalogas():
    cia = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(cia, "Diktuokle_portable.txt")):
        return os.path.join(cia, "Diktuokle_data")
    base = os.environ.get("LOCALAPPDATA")
    return os.path.join(base, "Diktuokle") if base else os.path.join(cia, "Diktuokle_data")


MODELIU_KATALOGAS = os.path.join(_duomenu_katalogas(), "modeliai")


def _yra_kese(repo):
    """Ar HF kese jau guli visas repo. local_files_only nieko nesiuncia i tinkla,
    tad tinka tikrinimui pries klausiant zmogaus."""
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(repo, local_files_only=True)
        return True
    except Exception:
        return False


def ko_truksta(kalbos):
    """Grazina sarasa [(raktas, repo, MB), ...] - ko reikia parsisiusti butent
    sitoms kalboms. Tuscias sarasas reiskia, kad viskas vietoje."""
    reikia = []

    if "lt" in kalbos:
        from modeliai import paprikos_kelias
        k = paprikos_kelias()
        # Rasta 2026-09-11 per "nuo nulio" testa: kai PAPRIKA_HF uzpildytas,
        # paprikos_kelias() grazina HF varda ir tai atrode kaip "yra" - dialogas
        # rode ~4,2 GB vietoj 5, o 814 MB siustusi tyliai per "Kraunu...".
        # Vietinis katalogas = yra; HF vardas = yra tik jei jau kese.
        if k is None or (not os.path.isdir(k) and not _yra_kese(k)):
            reikia.append(("paprika", PAPRIKA_REPO, DYDZIAI_MB["paprika"]))
        # Skyryba tik lietuviu kalbai - kitoms modelis skyrybos neprimeta.
        if not _yra_kese(SKYRYBOS_REPO):
            reikia.append(("skyryba", SKYRYBOS_REPO, DYDZIAI_MB["skyryba"]))

    # Vienas failas dviem kalbom: jei pazymeta bent viena is ju, reikia karta.
    if ("ru" in kalbos or "en" in kalbos) and not _yra_kese(LARGE_REPO):
        reikia.append(("large", LARGE_REPO, DYDZIAI_MB["large"]))

    return reikia


def parsisiusk(raktas, repo, pranesk=None):
    """Parsisiunčia viena modeli. `pranesk(tekstas)` - eilute busenai lange.

    Paprika keliauja i musu kataloga (`modeliai\\paprika-ct2-int8`), nes ten jos
    iesko `modeliai.py`; kiti - i HF kesa, is kur juos pasiima pacios bibliotekos.
    """
    from huggingface_hub import snapshot_download
    if pranesk:
        pranesk(repo)
    if raktas == "paprika":
        vieta = os.path.join(MODELIU_KATALOGAS, "paprika-ct2-int8")
        os.makedirs(vieta, exist_ok=True)
        snapshot_download(repo, local_dir=vieta)
        return vieta
    return snapshot_download(repo)
