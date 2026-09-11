"""
Lithuanian/Russian voice dictation using faster-whisper (Large v3) with GUI.
V2 Modernized: Memory-only processing (no disk I/O), optimized for High-End GPUs.
Hold Right Ctrl to record text, Right Ctrl + Right Alt for numbers mode.
Usage: pythonw lt_dictation_v2.py 
"""

import os
import re
import threading
import time
# tkinter - NEPRIVALOMAS (2026-09-11). Sis failas yra ir SENOJI tkinter sasaja,
# ir variklis, kuri importuoja naujasis PyQt6 langas. Dovanos pakete tkinter
# nera (ismestas is .spec, nes PyQt6 uztenka), tad importas cia nukristu dar
# nepasileidus programai - taip ir nutiko per Roberto testa 2026-09-11:
# "No module named 'tkinter'" tiesiai i veida pirmame paleidime.
# ⚠️ Pamoka: is Python paleistas kodas tkinter turi VISADA, tad tokios klaidos
# testuojant saltiniuose nepagausi - tik surinktame pakete.
try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:          # PyQt6 pakete jo ir neturi buti
    tk = None
    messagebox = None

# Fix CUDA DLL path for faster-whisper
try:
    import nvidia.cublas
    cuda_bin = os.path.join(nvidia.cublas.__path__[0], "bin")
    if os.path.isdir(cuda_bin):
        os.environ["PATH"] = cuda_bin + os.pathsep + os.environ.get("PATH", "")
    import nvidia.cudnn
    cudnn_bin = os.path.join(nvidia.cudnn.__path__[0], "bin")
    if os.path.isdir(cudnn_bin):
        os.environ["PATH"] = cudnn_bin + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    pass

import pyaudio
import pyperclip
import numpy as np # Added for RAM processing
from pynput import keyboard
from faster_whisper import WhisperModel

# --- CONFIG ---
MODEL_SIZE = "large-v3"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

# --- PAPRIKA (lietuviškos ausys) — bandymas 2026-09-08 ---
# Konversija yra int8, todėl GPU reikia "int8_float16". Grėblys iš
# whisper-writer: "int8" + cuda ten priverstinai varomas į CPU, ir atrodo,
# kad kaltas modelis, nors kaltas compute_type.
# 2026-09-11: kelias nebe kietai irasytas - `modeliai.py` iesko keliose vietose
# ir grazina None, jei Paprikos nera (svetimame kompiuteryje taip ir bus, kol
# jos nepadedam). Roberto masinoje rezultatas tas pats, kaip buvo.
try:
    from modeliai import paprikos_kelias
    PAPRIKA_PATH = paprikos_kelias()
except ImportError:          # senoji tkinter versija, paleista atskirai
    PAPRIKA_PATH = r"D:\_Balsas Lietuviksas\_darbal\paprika-ct2-int8"
PAPRIKA_COMPUTE = "int8_float16"

# Skyryba ir didziosios (Kristijono punct_restore + xlm-roberta ONNX).
# Tik lietuviu pusei: large-v3 rusiskai skyryba deda pats.
SKYRYBA = True

# Langas (2026-09-08): juodos zurnalo dezes nebeliko, todel viskas telpa i tris
# eilutes. Zurnalas rasomas i faila salia programos.
BANGOS_STULPELIAI = 22
BANGOS_DAZNIS = 60          # ms tarp perpiesimu
# Zurnalas gyvena NE salia programos (Roberto 09-08: instaliuojama programa i
# Program Files rasyti negali), o seimos konvencija is SDF/FOTO namu
# `saugykla.py`: %LOCALAPPDATA%\Diktuokle; jei salia exe guli zymeklis
# Diktuokle_portable.txt (flesiukas) - Diktuokle_data salia. Vardai
# PREFIKSUOTI programos vardu (seimos kolizijos pamoka 2026-08-07/24: dvi
# dovanos flesiuke dalinosi portable.txt ir _darbal - viena issivesdavo kitos
# duomenis). Be diakritiku: FAT32 + svetima koduote = beda.
def _duomenu_katalogas():
    cia = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(cia, "Diktuokle_portable.txt")):
        return os.path.join(cia, "Diktuokle_data")
    base = os.environ.get("LOCALAPPDATA")
    return os.path.join(base, "Diktuokle") if base else os.path.join(cia, "Diktuokle_data")


ZURNALO_FAILAS = os.path.join(_duomenu_katalogas(), "diktuokle.log")
ZURNALO_RIBA_B = 1_000_000     # ~2 500 diktavimu; diske niekada > ~2 MB

# --- Nustatymai (dovanos versija, 2026-09-11) ---------------------------------
# Roberto sprendimas: dovanoje zurnalas NERASOMAS is viso, kol zmogus pats
# neijungia. Priezastis ne vieta diske, o turinys: siame zurnale guli PATS
# PADIKTUOTAS TEKSTAS - laiskai, ligos istorijos, balsu pasakytas slaptazodis.
# Programa, zadanti "garsas niekur nesiunciamas", negali tyliai kaupti viso to
# nesifruoto archyvo. Kitose dovanose zurnale guli failu keliai; cia - gyvenimas.
#
# Du lygiai, ne vienas jungiklis:
#   zurnalas        - technika (irenginys, laikai, klaidos). Tokia zurnala zmogus
#                     gali drasiai nusiusti bet kam, prasydamas pagalbos.
#   zurnale_tekstas - PLIUS pats tekstas. Sito bet kam siusti negalima, todel jis
#                     atskirai ir ijungiamas tik sazinigai zinant, kas i ji pateks.
NUSTATYMU_FAILAS = os.path.join(_duomenu_katalogas(), "nustatymai.json")

NUSTATYMAI_PAGAL_NUTYLEJIMA = {
    # Kurios kalbos IDIEGTOS - ta pati eile, kuria zmogus pazymejo varneles
    # diegiant. Lange mygtukai atsiranda TIK sitoms: kam reikia vien lietuviu,
    # tam rusiskas mygtukas yra ne pasirinkimas, o siukslė ekrane.
    # PIRMOJI sio sarasO kalba duoda ir sasajos kalba (Roberto taisykle 09-11).
    "kalbos": ["lt"],
    "kalba": "lt",             # kuria kalba diktuota paskutini karta
    "sasajos_kalba": "lt",     # lango ir meniu kalba; nustatoma diegiant
    "skyryba": True,
    "virsuje": True,
    "zurnalas": False,         # DOVANOJE ISJUNGTA: nieko i diska
    "zurnale_tekstas": False,  # ir tuo labiau ne tekstas
}

# Kurios kalbos apskritai galimos ir kuo jos atpazistamos.
#   modelis="paprika" - lietuviskos ausys (Kristijono fine-tune);
#   modelis="bendras" - large-v3, kuris moka IR rusu, IR anglu (tas pats failas).
# skaiciai=False reiskia, kad "123" rezimas tai kalbai neveikia: skaiciu
# pletiklis turi tik LT ir RU zodynus, o tyliai blogai geriau nei nieko.
KALBU_SAVYBES = {
    "lt": {"modelis": "paprika", "skaiciai": True,  "skyryba": True},
    "ru": {"modelis": "bendras", "skaiciai": True,  "skyryba": False},
    "en": {"modelis": "bendras", "skaiciai": False, "skyryba": False},
}


# Instaliatorius kalbu pasirinkima raso i ATSKIRA faila, ne i nustatymai.json.
# Priezastis (Roberto testas 2026-09-11): perdiegus su viena kalba jis gavo dvi,
# nes nustatymai.json jau buvo, o instaliatorius jo "nelietė", kad neprarastu
# skyrybos ir zurnalo nustatymu. Dabar: instaliatorius VISADA raso
# diegimo_kalbos.json, programa paleidziant ji ISIURBIA i nustatymus (tik kalbu
# laukus!) ir istrina. Kiti nustatymai lieka kokie buvo.
DIEGIMO_KALBU_FAILAS = os.path.join(_duomenu_katalogas(), "diegimo_kalbos.json")


def skaityk_nustatymus():
    """Grazina nustatymus; jei failo nera ar jis sugadintas - numatytuosius.
    Nekritine vieta: programa turi pakilti net su tusciu disku."""
    nust = dict(NUSTATYMAI_PAGAL_NUTYLEJIMA)
    try:
        import json
        with open(NUSTATYMU_FAILAS, encoding="utf-8") as f:
            issaugoti = json.load(f)
        if isinstance(issaugoti, dict):
            # Tik zinomi raktai - kad senas ar svetimas failas neistemptu siuksliu.
            nust.update({k: v for k, v in issaugoti.items() if k in nust})
    except Exception:
        pass

    # Ka tik diegta? Kalbos is instaliatoriaus LAIMI pries senas, kiti laukai ne.
    try:
        import json
        with open(DIEGIMO_KALBU_FAILAS, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("kalbos"), list) and d["kalbos"]:
            nust["kalbos"] = d["kalbos"]
            nust["kalba"] = d["kalbos"][0]
            nust["sasajos_kalba"] = d.get("sasajos_kalba") or d["kalbos"][0]
            rasyk_nustatymus(nust)
        os.remove(DIEGIMO_KALBU_FAILAS)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return nust


def rasyk_nustatymus(nust):
    """Issaugo nustatymus. Klaida nutylima - nepavykes irasymas negali sugriauti
    diktavimo, tik reiskia, kad kita karta bus numatytieji."""
    try:
        import json
        os.makedirs(os.path.dirname(NUSTATYMU_FAILAS), exist_ok=True)
        with open(NUSTATYMU_FAILAS, "w", encoding="utf-8") as f:
            json.dump(nust, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def apkarpyk_zurnala():
    """Kvieciama paleidziant (Roberto 09-08: "kad log failas benaudojant
    neissipustu"). Ne pagal laika, o pagal dydi: virsijus riba senasis tampa
    diktuokle.old.log (viena atsarga, ankstesne perrasoma), naujas - tuscias.
    Klaida nutylima - programa turi startuoti."""
    try:
        if os.path.getsize(ZURNALO_FAILAS) > ZURNALO_RIBA_B:
            senas = ZURNALO_FAILAS[:-4] + ".old.log"
            os.replace(ZURNALO_FAILAS, senas)
    except OSError:
        pass

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
TRIGGER_KEY = keyboard.Key.ctrl_r
# --- END CONFIG ---

# --- SKYRYBOS SUTVARKYMAS PO MODELIO ---
def tvarkyk_po_skyrybos(text):
    """Du pataisymai po punct_restore, matuoti 2026-09-08:

    1. Modelis kartais palieka dvi didziasias zodzio pradzioje
       ("JAnkauskiene"). Visai didziosiomis rasomi zodziai (ABS, LDSP, MDF)
       nekeiciami - ten didziosios teisingos.
    2. Sakinio gale visada uzdedamas taskas. Diktuojant dalimis tai reikstu
       taska vidury minties, todel ji nuimam - sakinio pabaiga vartotojas
       sako balsu. Klaustukas ir sauktukas paliekami: ju modelis be reikalo
       nededa.
    """
    def _mazink(m):
        w = m.group(0)
        return w if w.isupper() else w[0] + w[1].lower() + w[2:]

    text = re.sub(r"\b[A-ZĄČĘĖĮŠŲŪŽ]{2}[a-ząčęėįšųūž]+", _mazink, text)
    if text.endswith("."):
        text = text[:-1]
    return text


# --- NUMBER CONVERSION ---
LT_NUMBERS = {
    "nulis": "0", "nuliai": "0", "nuli": "0",
    "vienas": "1", "viena": "1", "vieną": "1",
    "du": "2", "dvi": "2", "do": "2", "dvie": "2",
    "trys": "3", "tris": "3", "tri": "3",
    "keturi": "4", "keturios": "4", "keturis": "4",
    "penki": "5", "penkios": "5", "penkis": "5",
    "šeši": "6", "šešios": "6", "šešis": "6",
    "septyni": "7", "septynios": "7", "septynis": "7",
    "aštuoni": "8", "aštuonios": "8", "aštuonis": "8", "aštuonė": "8",
    "astuoni": "8", "astuone": "8",
    "devyni": "9", "devynios": "9", "devynis": "9",
    "kablelis": ",", "kablys": ",", "taškas": ".", "brūkšnys": "-",
    "pliusas": "+", "lygu": "=", "procentas": "%", "procentai": "%",
}

RU_NUMBERS = {
    "ноль": "0", "нуль": "0",
    "один": "1", "одна": "1", "одно": "1", "раз": "1",
    "два": "2", "две": "2",
    "три": "3",
    "четыре": "4", "четыри": "4",
    "пять": "5",
    "шесть": "6",
    "семь": "7",
    "восемь": "8",
    "девять": "9",
    "запятая": ",", "точка": ".", "тире": "-",
    "плюс": "+", "равно": "=", "процент": "%",
}

# --- SUDETINIAI SKAICIAI (2026-09-08) ---
# LT_NUMBERS/RU_NUMBERS moka tik atskirus skaitmenis, todel "dvidesimt penki"
# virsdavo i "dvidesimt 5" - puse zodziu, puse skaitmenu. Cia zodziai, kurie
# tai uzdaro. Reiksme: (tipas, skaicius)
#   "pridek"  - 11..19 ir desimtys: dvidesimt + penki = 25
#   "daugink" - simtas: du simtai = 200
#   "grupe"   - tukstantis ir daugiau: uzdaro grupe (du tukstanciai dvidesimt penki)
LT_SUDETINIAI = {
    "dešimt": ("pridek", 10), "desimt": ("pridek", 10), "dešimties": ("pridek", 10),
    "vienuolika": ("pridek", 11), "vienuolikos": ("pridek", 11),
    "dvylika": ("pridek", 12), "dvylikos": ("pridek", 12),
    "trylika": ("pridek", 13), "trylikos": ("pridek", 13),
    "keturiolika": ("pridek", 14), "keturiolikos": ("pridek", 14),
    "penkiolika": ("pridek", 15), "penkiolikos": ("pridek", 15),
    "šešiolika": ("pridek", 16), "šešiolikos": ("pridek", 16),
    "sesiolika": ("pridek", 16),
    "septyniolika": ("pridek", 17), "septyniolikos": ("pridek", 17),
    "aštuoniolika": ("pridek", 18), "aštuoniolikos": ("pridek", 18),
    "astuoniolika": ("pridek", 18),
    "devyniolika": ("pridek", 19), "devyniolikos": ("pridek", 19),
    "dvidešimt": ("pridek", 20), "dvidesimt": ("pridek", 20),
    "dvidešimties": ("pridek", 20),
    "trisdešimt": ("pridek", 30), "trisdesimt": ("pridek", 30),
    "keturiasdešimt": ("pridek", 40), "keturiasdesimt": ("pridek", 40),
    "penkiasdešimt": ("pridek", 50), "penkiasdesimt": ("pridek", 50),
    "šešiasdešimt": ("pridek", 60), "sesiasdesimt": ("pridek", 60),
    "septyniasdešimt": ("pridek", 70), "septyniasdesimt": ("pridek", 70),
    "aštuoniasdešimt": ("pridek", 80), "astuoniasdesimt": ("pridek", 80),
    "devyniasdešimt": ("pridek", 90), "devyniasdesimt": ("pridek", 90),
    # Snekamoji kalba: "t" gale nukrenta, ir Paprika taip ir raso -
    # 2026-09-08 "du simtai penkiasdesim sesi" virto "200 penkiasdesim 6".
    "dešim": ("pridek", 10), "desim": ("pridek", 10),
    "dvidešim": ("pridek", 20), "dvidesim": ("pridek", 20),
    "trisdešim": ("pridek", 30), "trisdesim": ("pridek", 30),
    "keturiasdešim": ("pridek", 40), "keturiasdesim": ("pridek", 40),
    "penkiasdešim": ("pridek", 50), "penkiasdesim": ("pridek", 50),
    "šešiasdešim": ("pridek", 60), "sesiasdesim": ("pridek", 60),
    "septyniasdešim": ("pridek", 70), "septyniasdesim": ("pridek", 70),
    "aštuoniasdešim": ("pridek", 80), "astuoniasdesim": ("pridek", 80),
    "devyniasdešim": ("pridek", 90), "devyniasdesim": ("pridek", 90),
    "šimtas": ("daugink", 100), "šimtai": ("daugink", 100),
    "šimtų": ("daugink", 100), "šimto": ("daugink", 100),
    "simtas": ("daugink", 100), "simtai": ("daugink", 100),
    "tūkstantis": ("grupe", 1000), "tūkstančiai": ("grupe", 1000),
    "tūkstančių": ("grupe", 1000), "tūkstančio": ("grupe", 1000),
    "tukstantis": ("grupe", 1000), "tukstanciai": ("grupe", 1000),
    "milijonas": ("grupe", 1000000), "milijonai": ("grupe", 1000000),
    "milijonų": ("grupe", 1000000),
}

RU_SUDETINIAI = {
    "десять": ("pridek", 10), "десяти": ("pridek", 10),
    "одиннадцать": ("pridek", 11), "двенадцать": ("pridek", 12),
    "тринадцать": ("pridek", 13), "четырнадцать": ("pridek", 14),
    "пятнадцать": ("pridek", 15), "шестнадцать": ("pridek", 16),
    "семнадцать": ("pridek", 17), "восемнадцать": ("pridek", 18),
    "девятнадцать": ("pridek", 19),
    "двадцать": ("pridek", 20), "тридцать": ("pridek", 30),
    "сорок": ("pridek", 40), "пятьдесят": ("pridek", 50),
    "шестьдесят": ("pridek", 60), "семьдесят": ("pridek", 70),
    "восемьдесят": ("pridek", 80), "девяносто": ("pridek", 90),
    "сто": ("daugink", 100), "ста": ("daugink", 100),
    "сотня": ("daugink", 100), "сотни": ("daugink", 100),
    "двести": ("pridek", 200), "триста": ("pridek", 300),
    "четыреста": ("pridek", 400), "пятьсот": ("pridek", 500),
    "шестьсот": ("pridek", 600), "семьсот": ("pridek", 700),
    "восемьсот": ("pridek", 800), "девятьсот": ("pridek", 900),
    "тысяча": ("grupe", 1000), "тысячи": ("grupe", 1000),
    "тысяч": ("grupe", 1000), "тысячу": ("grupe", 1000),
    "миллион": ("grupe", 1000000), "миллиона": ("grupe", 1000000),
}

# --- TARIMAS -> RASYBA (Roberto principas 2026-09-08) ---
# "Isgirsti gali klaidingai, bet parasyti turi pagal lietuviu kalbos
# standartus." Snekamojoje kalboje galunes nukrenta ("penkiasdesim"), Paprika
# uzraso kaip girdi. Skaitmenu rezime tai jau tvarko LT_SUDETINIAI; sis zodynas
# tvarko ZODZIU rezima - kad tekste liktu taisyklinga forma.
# Tik ZODYNAS, ne spejimas: ko cia nera, tas nelieciamas.
LT_TARIMAS_I_RASYBA = {
    "dešim": "dešimt", "dvidešim": "dvidešimt", "trisdešim": "trisdešimt",
    "keturiasdešim": "keturiasdešimt", "penkiasdešim": "penkiasdešimt",
    "šešiasdešim": "šešiasdešimt", "septyniasdešim": "septyniasdešimt",
    "aštuoniasdešim": "aštuoniasdešimt", "devyniasdešim": "devyniasdešimt",
}


def tarimas_i_rasyba(text, lang="lt"):
    """Zodziu rezime pakeicia snekamasias formas taisyklingomis pagal zodyna.
    Pirma didzioji raide islaikoma ("Penkiasdesim" -> "Penkiasdesimt")."""
    if lang != "lt":
        return text
    zodynas = LT_TARIMAS_I_RASYBA

    def _keisk(m):
        z = m.group(0)
        taisyklingas = zodynas.get(z.lower())
        if not taisyklingas:
            return z
        return taisyklingas.capitalize() if z[0].isupper() else taisyklingas

    return re.sub(r"[A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž]+", _keisk, text)


# --- VISA SKAICIU EILE: linksniai + tarimo variantai + be diakritiku ---------
# Roberto uzduotis 2026-09-08: "pagalvok apie visus skaitmenis, kas gali buti
# ne visai gerai istarta". Generuojam is baziniu formu, ne rasom rankomis.
# Esami zodynai NELIECIAMI - tik papildomi (.update), kad kas veike, veiktu.
_DIAKRITIKAI = str.maketrans("ąčęėįšųūž", "aceeisuuz")


def _be_diakritiku(z):
    return z.translate(_DIAKRITIKAI)


def _su_variantais(zodziai):
    """Kiekvienam zodziui prideda ir forma be diakritiku."""
    visi = set()
    for z in zodziai:
        visi.add(z)
        visi.add(_be_diakritiku(z))
    return visi


# Vienetai su linksniais (vyr. ir mot. gimine). Reiksme - skaitmuo.
LT_VIENETAI_LINKSNIAI = {}
for _skaitmuo, _formos in {
    "0": "nulis nulio nuliui nulį nuliu nuliai nulių",
    "1": "vienas viena vieną vieno vienos vienam vienai vienu vienoje vieni vienos",
    "2": "du dvi dviejų dviem dvejų dvejus dvejais dvejos dveji",
    "3": "trys tris trijų trims trimis trejos treji trejų",
    "4": "keturi keturios keturių keturis keturias keturiems keturioms keturiais",
    "5": "penki penkios penkių penkis penkias penkiems penkioms penkiais",
    "6": "šeši šešios šešių šešis šešias šešiems šešioms šešiais",
    "7": "septyni septynios septynių septynis septynias septyniems septynioms",
    "8": "aštuoni aštuonios aštuonių aštuonis aštuonias aštuoniems aštuonioms",
    "9": "devyni devynios devynių devynis devynias devyniems devynioms",
}.items():
    for _z in _su_variantais(_formos.split()):
        LT_VIENETAI_LINKSNIAI[_z] = _skaitmuo

# Sudetiniai: bazine forma -> (tipas, reiksme). Linksniai ir tarimo variantai
# generuojami zemiau.
_SUDETINIU_BAZES = {
    10: ("pridek", "dešimt dešimties dešimčiai dešimtį dešimtimi dešim"),
    11: ("pridek", "vienuolika vienuolikos vienuolikai vienuoliką vienolika vienuolka"),
    12: ("pridek", "dvylika dvylikos dvylikai dvyliką dvylka"),
    13: ("pridek", "trylika trylikos trylikai tryliką trylka"),
    14: ("pridek", "keturiolika keturiolikos keturiolikai keturioliką keturolika"),
    15: ("pridek", "penkiolika penkiolikos penkiolikai penkioliką penkiolka"),
    16: ("pridek", "šešiolika šešiolikos šešiolikai šešioliką šešiolka"),
    17: ("pridek", "septyniolika septyniolikos septyniolikai septynioliką septyniolka"),
    18: ("pridek", "aštuoniolika aštuoniolikos aštuoniolikai aštuonioliką aštuoniolka"),
    19: ("pridek", "devyniolika devyniolikos devyniolikai devynioliką devyniolka"),
    20: ("pridek", "dvidešimt dvidešimties dvidešimčiai dvidešim"),
    30: ("pridek", "trisdešimt trisdešimties trisdešimčiai trisdešim"),
    40: ("pridek", "keturiasdešimt keturiasdešimties keturiasdešimčiai keturiasdešim"),
    50: ("pridek", "penkiasdešimt penkiasdešimties penkiasdešimčiai penkiasdešim"),
    60: ("pridek", "šešiasdešimt šešiasdešimties šešiasdešimčiai šešiasdešim"),
    70: ("pridek", "septyniasdešimt septyniasdešimties septyniasdešimčiai septyniasdešim"),
    80: ("pridek", "aštuoniasdešimt aštuoniasdešimties aštuoniasdešimčiai aštuoniasdešim"),
    90: ("pridek", "devyniasdešimt devyniasdešimties devyniasdešimčiai devyniasdešim"),
    100: ("daugink", "šimtas šimto šimtui šimtą šimtu šimte šimtai šimtų šimtams šimtus"),
    1000: ("grupe", "tūkstantis tūkstančio tūkstančiui tūkstantį tūkstančiu tūkstančiai "
                    "tūkstančių tūkstančiams tūkstančius tūkstants"),
    1000000: ("grupe", "milijonas milijono milijonui milijoną milijonu milijonai "
                       "milijonų milijonams milijonus"),
}
for _verte, (_tipas, _formos) in _SUDETINIU_BAZES.items():
    for _z in _su_variantais(_formos.split()):
        LT_SUDETINIAI.setdefault(_z, (_tipas, _verte))

# Tarimas -> rasyba zodziu rezimui: nukritusios galunes ir suspausti "-olika".
LT_TARIMAS_I_RASYBA.update({
    "vienolika": "vienuolika", "vienuolka": "vienuolika", "dvylka": "dvylika",
    "trylka": "trylika", "keturolika": "keturiolika", "penkiolka": "penkiolika",
    "šešiolka": "šešiolika", "septyniolka": "septyniolika",
    "aštuoniolka": "aštuoniolika", "devyniolka": "devyniolika",
    "tūkstants": "tūkstantis",
})


LT_DIGITS_TO_WORDS = {
    "0": "nulis", "1": "vienas", "2": "du", "3": "trys",
    "4": "keturi", "5": "penki", "6": "šeši", "7": "septyni",
    "8": "aštuoni", "9": "devyni",
}

RU_DIGITS_TO_WORDS = {
    "0": "ноль", "1": "один", "2": "два", "3": "три",
    "4": "четыре", "5": "пять", "6": "шесть", "7": "семь",
    "8": "восемь", "9": "девять",
}

def _surink_grupe(zodziai, vienetai, sudetiniai):
    """Vienos gretimu skaiciu zodziu grupes reiksme.

    Viena taisykle sprendzia abu naudojimo budus:
      * VIEN vienetai is eiles -> skaitmenu eile: "vienas nulis nulis" -> "100"
        (telefono numeris, kodas - Roberto atvejis 2026-09-08);
      * atsiranda desimtis, paauglys ar simtas -> skaiciuojam kaip skaiciu:
        "dvidesimt penki" -> "25", "simtas dvidesimt penki" -> "125".
    """
    if all(z in vienetai for z in zodziai):
        return "".join(vienetai[z] for z in zodziai)

    viso, einamas = 0, 0
    for z in zodziai:
        if z in vienetai:
            einamas += int(vienetai[z])
            continue
        tipas, verte = sudetiniai[z]
        if tipas == "pridek":
            einamas += verte
        elif tipas == "daugink":
            einamas = (einamas or 1) * verte
        else:  # grupe: tukstantis, milijonas
            viso += (einamas or 1) * verte
            einamas = 0
    return str(viso + einamas)


def words_to_numbers(text, lang="lt"):
    num_map = LT_NUMBERS if lang == "lt" else RU_NUMBERS
    sudetiniai = LT_SUDETINIAI if lang == "lt" else RU_SUDETINIAI
    # LT_NUMBERS laiko ir zenklus (taskas, kablelis) - skaiciu grupei tinka
    # tik tie irasai, kuriu reiksme yra skaitmuo.
    vienetai = {k: v for k, v in num_map.items() if v.isdigit()}
    if lang == "lt":
        vienetai = {**LT_VIENETAI_LINKSNIAI, **vienetai}

    text = re.sub(r'[.,!?;:]', '', text)
    result = []
    grupe = []

    def _uzdaryk():
        if grupe:
            result.append(_surink_grupe(grupe, vienetai, sudetiniai))
            grupe.clear()

    for word in text.split():
        clean = word.lower().strip()
        if clean in vienetai or clean in sudetiniai:
            grupe.append(clean)
        else:
            _uzdaryk()
            if clean in num_map:      # zenklas: taskas, kablelis, bruksnys
                result.append(num_map[clean])
            elif clean:
                result.append(word)
    _uzdaryk()

    return " ".join(result)

def numbers_to_words(text, lang="lt"):
    digit_map = LT_DIGITS_TO_WORDS if lang == "lt" else RU_DIGITS_TO_WORDS
    def replace_number(match):
        num = match.group(0)
        if num in digit_map:
            return digit_map[num]
        return " ".join(digit_map.get(d, d) for d in num)
    return re.sub(r'\d+', replace_number, text)

class DictationApp:
    def __init__(self):
        self.recording = False
        self.number_mode = False
        self.language = "lt"
        self.lang_name = "Lietuviu"
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.record_thread = None
        self.model = None
        self.listener = None
        self._last_ralt_press = 0

        # --- GUI ---
        self.root = tk.Tk()
        self.root.title("Vois Asistent V2 — Lietuviu [lt]")
        self.root.geometry("620x108")
        self.root.minsize(520, 108)
        self.root.resizable(True, False)

        # Dantracio jungikliai.
        self.v_skyryba = tk.IntVar(value=1 if SKYRYBA else 0)
        self.v_virsuje = tk.IntVar(value=1)
        self.root.configure(bg="#1e1e1e")
        self.root.attributes("-topmost", True)

        # Ikona (2026-09-08). Jei failo nebutu - langas tiesiog liks su
        # numatytaja tkinter ikona, programa del to nekris.
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "Diktuotojas.ico"))
        except Exception:
            pass

        self.top_frame = tk.Frame(self.root, bg="#2d2d2d")
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        self.btn_lt = tk.Button(self.top_frame, text=" Lietuviu ", command=lambda: self._switch_lang("lt", "Lietuviu"),
                                bg="#2980b9", fg="white", relief=tk.FLAT,
                                font=("Segoe UI", 9, "bold"),
                                activebackground="#3498db", cursor="hand2")
        self.btn_lt.pack(side=tk.LEFT, padx=(8, 4), pady=4)

        self.btn_ru = tk.Button(self.top_frame, text=" Rusu ", command=lambda: self._switch_lang("ru", "Rusu"),
                                bg="#444444", fg="#cccccc", relief=tk.FLAT,
                                font=("Segoe UI", 9, "bold"),
                                activebackground="#666666", cursor="hand2")
        self.btn_ru.pack(side=tk.LEFT, padx=(0, 8), pady=4)

        tk.Label(self.top_frame, text="|", fg="#555555", bg="#2d2d2d",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.btn_abc = tk.Button(self.top_frame, text=" ABC ", command=lambda: self._switch_mode(False),
                                 bg="#2980b9", fg="white", relief=tk.FLAT,
                                 font=("Segoe UI", 9, "bold"),
                                 activebackground="#3498db", cursor="hand2")
        self.btn_abc.pack(side=tk.LEFT, padx=(8, 4), pady=4)

        self.btn_123 = tk.Button(self.top_frame, text=" 123 ", command=lambda: self._switch_mode(True),
                                 bg="#444444", fg="#cccccc", relief=tk.FLAT,
                                 font=("Segoe UI", 9, "bold"),
                                 activebackground="#666666", cursor="hand2")
        self.btn_123.pack(side=tk.LEFT, padx=(0, 4), pady=4)

        self.hint_label = tk.Label(self.top_frame,
                                   text="Laikyk R-Ctrl=diktuoti | laikant:  ← ABC/123   → kalba",
                                   fg="#aaaaaa", bg="#2d2d2d",
                                   font=("Segoe UI", 8))
        self.hint_label.pack(side=tk.LEFT, expand=True)

        # --- Busenos eilute: taskas, zodis, GYVA BANGA, dantratis, klaustukas ---
        # Juodos zurnalo dezes nebeliko (Roberto sprendimas 2026-09-08): ji
        # uzeme ~80 % lango, o tekstas ir taip krenta i kursoriaus vieta.
        # Zurnalas dabar rasomas i faila, klaidos - i sia eilute.
        self.status_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.status_frame.pack(fill=tk.X, padx=10, pady=(6, 10))

        self.status_dot = tk.Label(self.status_frame, text="●", fg="#888888",
                                   bg="#1e1e1e", font=("Segoe UI", 12))
        self.status_dot.pack(side=tk.LEFT)

        self.status_label = tk.Label(self.status_frame, text="Kraunu...",
                                     fg="#cccccc", bg="#1e1e1e", width=11,
                                     anchor="w", font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT, padx=(6, 0))

        # ⭐ Banga - vienintele priezastis, del ko si vieta lange verta ka nors
        # laikyti. "Ready" yra tik pazadas: jei mikrofonas isjungtas arba garsas
        # eina i kita irengini, uzrasas vis tiek sako "Ready", ir tai suzinai po
        # 10 s negaves teksto. Banga pasako tiesa iskart.
        self.banga = tk.Canvas(self.status_frame, height=26, bg="#1e1e1e",
                               highlightthickness=0)
        self.banga.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self._lygiai = [0.0] * BANGOS_STULPELIAI
        self._piesk_banga()

        self.help_btn = tk.Button(self.status_frame, text=" ? ", command=self._rodyk_komandas,
                                  bg="#3c3c3c", fg="#dddddd", relief=tk.FLAT,
                                  font=("Segoe UI", 9, "bold"),
                                  activebackground="#555555", cursor="hand2")
        self.help_btn.pack(side=tk.RIGHT)

        self.cog_btn = tk.Button(self.status_frame, text=" ⚙ ", command=self._rodyk_nustatymus,
                                 bg="#3c3c3c", fg="#dddddd", relief=tk.FLAT,
                                 font=("Segoe UI", 9, "bold"),
                                 activebackground="#555555", cursor="hand2")
        self.cog_btn.pack(side=tk.RIGHT, padx=(0, 6))

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        threading.Thread(target=self._load_model, daemon=True).start()

    # --- Banga ---------------------------------------------------------------
    def _piesk_banga(self):
        """Perpiesia stulpelius kas BANGOS_DAZNIS ms. Garso lygi mataojam ir taip -
        irasymo cikle, todel tai kainuoja tik piesima."""
        self.banga.delete("all")
        p = self.banga.winfo_width() or 200
        a = self.banga.winfo_height() or 26
        n = len(self._lygiai)
        plotis, tarpas = 3, 4
        x = max(0, (p - n * (plotis + tarpas)) // 2)
        for lygis in self._lygiai:
            h = max(2, min(a - 2, int(lygis * (a - 4))))
            y = (a - h) // 2
            spalva = "#E8B84B" if lygis > 0.02 else "#3a3a2a"
            self.banga.create_rectangle(x, y, x + plotis, y + h,
                                        fill=spalva, outline="")
            x += plotis + tarpas
        self.root.after(BANGOS_DAZNIS, self._piesk_banga)

    # --- Dantratis ir klaustukas ---------------------------------------------
    def _rodyk_nustatymus(self):
        meniu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#dddddd",
                        activebackground="#2980b9", activeforeground="white")
        meniu.add_checkbutton(label="  Skyryba ir didziosios",
                              variable=self.v_skyryba, command=self._perjunk_skyryba)
        meniu.add_checkbutton(label="  Visada virsuje",
                              variable=self.v_virsuje, command=self._perjunk_virsuje)
        meniu.add_separator()
        meniu.add_command(label="  Zurnalas: " + os.path.basename(ZURNALO_FAILAS),
                          state=tk.DISABLED)
        meniu.add_separator()
        meniu.add_command(label="  Viskas lieka siame kompiuteryje", state=tk.DISABLED)
        meniu.add_command(label="  Ausys: Paprika (Kristijonas Jakubsonas)", state=tk.DISABLED)
        try:
            meniu.tk_popup(self.cog_btn.winfo_rootx(),
                           self.cog_btn.winfo_rooty() + self.cog_btn.winfo_height())
        finally:
            meniu.grab_release()

    def _perjunk_skyryba(self):
        self._log(f"Skyryba: {'ijungta' if self.v_skyryba.get() else 'isjungta'}", "info")

    def _perjunk_virsuje(self):
        self.root.attributes("-topmost", bool(self.v_virsuje.get()))

    def _rodyk_komandas(self):
        messagebox.showinfo(
            "Komandos",
            "DIKTAVIMAS\n"
            "  Laikyk desini Ctrl - diktuoji, paleidi - tekstas irasomas\n\n"
            "LAIKANT DESINI Ctrl\n"
            "  ←   ABC / 123 (zodziai arba skaitmenys)\n"
            "  →   lietuviu / rusu\n"
            "  Perjungus kalbeti galima toliau - galioja visam tam sakiniui.\n\n"
            "  2x desinys Shift - taip pat ABC / 123\n\n"
            "REZIME 123 GALIMA SAKYTI\n"
            "  taskas  kablelis  bruksnys  pliusas  lygu  procentas\n\n"
            "SKAICIAI\n"
            "  Po viena: \"vienas nulis nulis\" -> 100\n"
            "  Sudetiniai: \"simtas dvidesimt penki\" -> 125",
            parent=self.root)

    def _switch_mode(self, numbers):
        self.number_mode = numbers
        if numbers:
            self.btn_123.configure(bg="#e67e22", fg="white")
            self.btn_abc.configure(bg="#444444", fg="#cccccc")
            self._log("Rezimas: SKAICIAI [123]", "num")
        else:
            self.btn_abc.configure(bg="#2980b9", fg="white")
            self.btn_123.configure(bg="#444444", fg="#cccccc")
            self._log("Rezimas: TEKSTAS [ABC]", "lang")

    def _switch_lang(self, code, name):
        self.language = code
        self.lang_name = name
        # Kalba matoma antrasteje ir mygtuko spalva - atskiro uzraso lange
        # nebereikia (2026-09-08, langas be zurnalo).
        self.root.title(f"Vois Asistent V2 — {name} [{code}]")
        self._log(f"Kalba: {name} [{code}]", "lang")
        if code == "lt":
            self.btn_lt.configure(bg="#2980b9", fg="white")
            self.btn_ru.configure(bg="#444444", fg="#cccccc")
        else:
            self.btn_ru.configure(bg="#2980b9", fg="white")
            self.btn_lt.configure(bg="#444444", fg="#cccccc")

    def _log(self, text, tag="info"):
        """Zurnalas keliauja i faila, ne i langa (2026-09-08).

        Lange jo nebeliko, todel klaidos ("warn") dar parodomos ir busenos
        eiluteje raudonai - kitaip apie jas nesuzinotum.
        """
        try:
            os.makedirs(os.path.dirname(ZURNALO_FAILAS), exist_ok=True)
            with open(ZURNALO_FAILAS, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{tag}] {text}\n")
        except Exception:
            pass
        if tag == "warn":
            self._set_status(text[:40], "#ff6a6a")

    def _set_status(self, text, color="#888888"):
        self.root.after(0, self._set_status_gui, text, color)

    def _set_status_gui(self, text, color):
        self.status_label.configure(text=text)
        self.status_dot.configure(fg=color)

    def _load_model(self):
        self.model_lt = None
        self.punct = None
        self._log(f"Loading Whisper {MODEL_SIZE}... (Optimized)", "info")
        try:
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            self._log("Model loaded! Ready.", "ok")
            # Paprika kraunama atskirai: jei ji nepakiltų, rusų pusė turi likti
            # veikianti, o ne nuversti visą programą.
            try:
                self._log(f"Kraunu Papriką ({PAPRIKA_COMPUTE})...", "info")
                t0 = time.time()
                self.model_lt = WhisperModel(PAPRIKA_PATH, device=DEVICE,
                                             compute_type=PAPRIKA_COMPUTE)
                self._log(f"Paprika uzkrauta per {time.time() - t0:.1f} s - lietuviu puse eina per ja.", "ok")
            except Exception as pe:
                self.model_lt = None
                self._log(f"PAPRIKA NEPAKILO: {pe}", "warn")
                self._log("Lietuviu puse lieka ant large-v3.", "warn")
            # Skyryba - irgi atskirai: jos nebuvimas neturi nuversti diktavimo.
            if SKYRYBA:
                try:
                    self._log("Kraunu skyrybos modeli...", "info")
                    t0 = time.time()
                    from punct_restore import Punctuator
                    self.punct = Punctuator()
                    self.punct.restore("apsilimas")  # pirmas paleidimas letesnis
                    self._log(f"Skyryba paruosta per {time.time() - t0:.1f} s.", "ok")
                except Exception as se:
                    self.punct = None
                    self._log(f"SKYRYBA NEPAKILO: {se}", "warn")
            self._set_status("Pasiruoses", "#6aff6a")
            self._start_listener()
        except Exception as e:
            self._log(f"ERROR: {e}", "warn")
            self._set_status("Modelis nepakilo", "#ff6a6a")

    def _start_listener(self):
        self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.listener.daemon = True
        self.listener.start()

    def _on_press(self, key):
        if key == TRIGGER_KEY:
            self.start_recording()
            return

        # --- Komandos LAIKANT R-Ctrl (Roberto sprendimas 2026-09-08) ---
        # Rodykles yra po pat pirstu, todel perjungti galima neatleidus klavisо
        # ir kalbeti toliau: rezimas ir kalba nuskaitomi irasa BAIGIANT, tad
        # paskutinis paspaudimas galioja visam tam gabalui.
        #   <-  ABC / 123     ->  lietuviu / rusu
        if self.recording and key in (keyboard.Key.left, keyboard.Key.right):
            if key == keyboard.Key.left:
                self.root.after(0, lambda: self._switch_mode(not self.number_mode))
            else:
                kita = ("ru", "Rusu") if self.language == "lt" else ("lt", "Lietuviu")
                self.root.after(0, lambda: self._switch_lang(*kita))
            # Nepraleidziam rodykles toliau: svetimame lange Ctrl+rodykle
            # perkeltu zymekli per zodi. Jei sis pynput backendas suppress
            # nepalaiko - nieko baisaus, tik zymeklis pajudes.
            try:
                self.listener.suppress_event()
            except Exception:
                pass
            return

        if key == keyboard.Key.shift_r:
            now = time.time()
            if now - self._last_ralt_press < 0.4:
                self._last_ralt_press = 0
                self.root.after(0, lambda: self._switch_mode(not self.number_mode))
            else:
                self._last_ralt_press = now

    def _on_release(self, key):
        if key == TRIGGER_KEY:
            if self.recording:
                threading.Thread(target=self.stop_recording_and_transcribe, daemon=True).start()

    def start_recording(self):
        if self.recording or self.model is None:
            return
        self.recording = True
        self.frames = []
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, frames_per_buffer=CHUNK
            )
            self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.record_thread.start()
            self._log("[REC] Recording...", "rec")
            self._set_status("Klausau", "#ff6a6a")
        except Exception as e:
            self.recording = False
            self._log(f"Mic error: {e}", "warn")

    def _record_loop(self):
        while self.recording:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                # Garso lygis bangai. Skaiciuojam cia, nes duomenys jau rankose;
                # kvadratine saknis is vidutinio kvadrato, normuota i 0..1.
                imtis = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                lygis = float(np.sqrt(np.mean(imtis * imtis))) / 3000.0
                self._lygiai = self._lygiai[1:] + [min(1.0, lygis)]
            except Exception:
                break
        # Paleidus klavisa banga nuslugsta, o ne sustingsta pakelta.
        self._lygiai = [0.0] * BANGOS_STULPELIAI

    def stop_recording_and_transcribe(self):
        if not self.recording:
            return
        self.recording = False
        use_numbers = self.number_mode
        if self.record_thread:
            self.record_thread.join(timeout=2)
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if not self.frames:
            self._log("[!] No audio", "warn")
            self._set_status("Pasiruoses", "#6aff6a")
            return

        self._set_status("Verciu", "#ffaa00")
        self._log("[...] Transcribing (RAM mode)...", "info")

        # --- MODERNIZED PART: RAM Processing instead of Disk I/O ---
        try:
            # Convert byte frames to float32 numpy array normalized between -1.0 and 1.0
            audio_data = np.frombuffer(b"".join(self.frames), dtype=np.int16).astype(np.float32) / 32768.0

            # beam_size=5 weighs several guesses -> fewer Lithuanian misspellings.
            # initial_prompt nudges the model toward correct, clean spelling.
            prompt = "Tai taisyklinga lietuvių kalba su skyryba." if self.language == "lt" else "Это правильная русская речь."
            # Lietuviams - Paprika (jei pakilo), rusams - large-v3, kaip buvo.
            model = self.model_lt if (self.language == "lt" and self.model_lt) else self.model
            t_start = time.time()
            segments, info = model.transcribe(
                audio=audio_data,
                language=self.language,
                beam_size=5,
                vad_filter=True,
                initial_prompt=prompt
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            which = "Paprika" if model is self.model_lt else MODEL_SIZE
            self._log(f"[{which}] {time.time() - t_start:.2f} s", "info")

            if text:
                if use_numbers:
                    original = text
                    text = words_to_numbers(text, self.language)
                    self._log(f"[123] {original} -> {text}", "num")
                else:
                    original = text
                    text = numbers_to_words(text, self.language)
                    if text != original:
                        self._log(f"[ABC] {original} -> {text}", "ok")
                    else:
                        self._log(f"[OK] {text}", "ok")

                # Skyryba tik lietuviams ir tik po skaiciu tvarkymo: modelis
                # tada mato ta pati teksta, kuris keliaus i dokumenta.
                if self.punct and self.language == "lt" and self.v_skyryba.get():
                    try:
                        t_p = time.time()
                        restored, st = self.punct.restore(text)
                        restored = tvarkyk_po_skyrybos(restored)
                        if st["refused"]:
                            self._log(f"[skyryba] atmesta {st['refused']} - zodziai apsaugoti", "warn")
                        self._log(f"[skyryba] {(time.time() - t_p) * 1000:.0f} ms -> {restored}", "ok")
                        text = restored
                    except Exception as pe:
                        self._log(f"[skyryba] nepavyko: {pe}", "warn")

                pyperclip.copy(text)
                time.sleep(0.05)
                ctrl = keyboard.Controller()
                ctrl.press(keyboard.Key.ctrl_l)
                ctrl.tap("v")
                ctrl.release(keyboard.Key.ctrl_l)
            else:
                self._log("[!] Nothing recognized", "warn")
        except Exception as e:
            self._log(f"Error: {e}", "warn")

        self._set_status("Pasiruoses", "#6aff6a")

    def quit_app(self):
        if self.listener:
            self.listener.stop()
        self.audio.terminate()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DictationApp()
    app.run()
