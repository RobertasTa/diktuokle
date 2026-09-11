# -*- coding: utf-8 -*-
r"""Diktuokle - lietuviskas diktavimas be interneto (PyQt6 langas).

Vardas (Robertas, 2026-09-08): "diktuoti -> diktuokle" tuo paciu modeliu kaip
"skaiciuoti -> skaiciuokle" (VLKK irankiu priesaga -uokle). "Diktuotojas" buvo
klaida dviem atzvilgiais: -tojas daro VEIKEJU, ne irankiu pavadinimus, ir tai
bendrinis zodis - Google atiduoda zodynus, ne dovana. "Diktuokle" Google tuscia.

Variklis ir visa teksto logika paimta is `lt_dictation_paprika.py` - ten ji
istestuota 2026-09-08 ir dubliuoti jos nera prasmes. Sitame faile TIK langas.

Kodel PyQt6, o ne tkinter: langas turi atrodyti kaip dovanu seimos narys -
apvalinti mygtukai, svarus sriftas, lietuviski rasmenys. Tkinter to neduoda.

PyQt6 taisykles paimtos is `\\NAS-Rtrob\OKF_Zinios\OKF_PyQt6_GUI`:
  * enum'ai VISADA pilnu keliu: Qt.AlignmentFlag.AlignCenter (ne Qt.AlignCenter);
  * QAction ir kitos - is QtGui, ne QtWidgets;
  * exec() be pabraukimo;
  * spalvos piesime - QColor(r, g, b) skaiciais (vardu ir hex spastai);
  * fono gijos NELIECIA lango: viskas eina per pyqtSignal i bound method slota.
"""
import ctypes
import os
import sys
import threading
import time
import urllib.parse
import webbrowser

import numpy as np
import pyaudio
import pyperclip
from pynput import keyboard
from faster_whisper import WhisperModel

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QMenu,
                             QMessageBox, QPlainTextEdit, QPushButton,
                             QVBoxLayout, QWidget)

# Sasajos kalba: t() grazina lietuviska rakta arba jo vertima. Importuojam
# moduli, ne funkcija - kad kalba.nustatyk() pakeistu ja VISIEM iskvietimam.
import kalba
from kalba import KALBU_VARDAI, t

# Variklio dalis - is istestuoto failo, kad butu vienas tiesos saltinis.
from lt_dictation_paprika import (CHANNELS, CHUNK, COMPUTE_TYPE, DEVICE,
                                  KALBU_SAVYBES, MODEL_SIZE, PAPRIKA_COMPUTE,
                                  PAPRIKA_PATH, SAMPLE_RATE, TRIGGER_KEY,
                                  ZURNALO_FAILAS, apkarpyk_zurnala,
                                  numbers_to_words, rasyk_nustatymus,
                                  skaityk_nustatymus, tarimas_i_rasyba,
                                  tvarkyk_po_skyrybos, words_to_numbers)

CIA = os.path.dirname(os.path.abspath(__file__))
IKONA = os.path.join(CIA, "Diktuokle.ico")
README = os.path.join(CIA, "README.txt")
VERSIJA = "0.1"
KUREJO_PUSLAPIS = "https://github.com/RobertasTa/diktuokle"
BRIEF_URL = "https://raw.githubusercontent.com/RobertasTa/diktuokle/main/AI_CONSULTANT_BRIEF.md"

# --cpu [gijos]: viskas ant procesoriaus (Roberto 09-08: "padarai antra
# programa, kuri suksis ant procesoriaus, ir pamatuosim" - ar tinka eiliniam
# pilieciui be NVIDIA). Giju skaicius leidzia imituoti 4-8 branduoliu masina
# ant 32 branduoliu stoties (netiksliai, bet arciau tiesos nei 32).
CPU_REZIMAS = "--cpu" in sys.argv
CPU_GIJOS = os.cpu_count() or 4
if CPU_REZIMAS:
    i = sys.argv.index("--cpu")
    if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
        CPU_GIJOS = int(sys.argv[i + 1])
IRENGINYS = "cpu" if CPU_REZIMAS else DEVICE
CT_LARGE = "int8" if CPU_REZIMAS else COMPUTE_TYPE
CT_PAPRIKA = "int8" if CPU_REZIMAS else PAPRIKA_COMPUTE
LANGO_VARDAS = f"Diktuoklė [CPU {CPU_GIJOS}]" if CPU_REZIMAS else "Diktuoklė"

STULPELIU = 14               # trumpa: matytis, kad balsas eina, ne oscilografas
PIESIMO_DAZNIS = 60          # ms
STULPELIO_PLOTIS, STULPELIO_TARPAS = 5, 3
BANGOS_AUKSTIS = 28
# Jautrumas ADAPTYVUS: pilnas stulpelis = garsiausias paskutiniu ~2 s skiemuo.
# Spejimai (3000, paskui 1200) abu buvo per dideli Roberto mikrofonui - banga
# liko taskeliais. Grindys, zemiau kuriu pikas nekrenta, kad tyla nekiltu.
PIKO_GRINDYS = 50.0         # 150 buvo per daug: tyliai diktuojant banga liko zema
PIKO_KRITIMAS = 0.985       # per viena 64 ms imti (~2 s iki grindu)

# Spalvos skaiciais - OKF pyqt6_colors_guard: vardu ir hex be groteles spastai.
GINTARAS = QColor(232, 184, 75)
GINTARAS_BLANKUS = QColor(58, 58, 42)

STILIUS = """
QWidget#saknis { background: #1b1b1b; }
QLabel { color: #d8d8d8; font-family: 'Segoe UI'; font-size: 13px; }
QLabel#busena { color: #e6e6e6; font-size: 13px; }
QLabel#uzuomina { color: #7d7d7d; font-size: 11px; }
QPushButton {
    background: #343434; color: #c8c8c8; border: none; border-radius: 5px;
    padding: 7px 15px; font-family: 'Segoe UI'; font-size: 13px;
}
QPushButton:hover { background: #444444; }
QPushButton[aktyvus="taip"] { background: #1668C1; color: #ffffff; }
QPushButton#ikona { padding: 6px 9px; font-size: 14px; }
QPushButton#ikona::menu-indicator { image: none; width: 0px; }
QDialog, QMessageBox { background: #1b1b1b; }
QPlainTextEdit {
    background: #242424; color: #d8d8d8; border: 1px solid #3d3d3d;
    border-radius: 5px; padding: 6px;
}
QMenu { background: #2b2b2b; color: #dddddd; border: 1px solid #3d3d3d; }
QMenu::item { padding: 6px 26px 6px 22px; }
QMenu::item:selected { background: #1668C1; color: #ffffff; }
QMenu::separator { height: 1px; background: #3d3d3d; margin: 4px 8px; }
"""


class Banga(QWidget):
    """Gyva garso banga.

    Vienintele priezastis, del ko si vieta lange verta ka nors laikyti:
    "Pasiruoses" yra tik pazadas, o jei mikrofonas isjungtas arba garsas eina
    i kita irengini, uzrasas vis tiek melagingai ramina. Banga rodo tiesa.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Fiksuotas plotis - banga netempia lango (Roberto pastaba 09-08).
        self.setFixedSize(STULPELIU * (STULPELIO_PLOTIS + STULPELIO_TARPAS), BANGOS_AUKSTIS)
        self.lygiai = [0.0] * STULPELIU

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        plotis, tarpas = STULPELIO_PLOTIS, STULPELIO_TARPAS
        x = 0
        vidurys = self.height() / 2
        for lygis in self.lygiai:
            # Tylos stulpelis irgi matomas (6 px), ne taskelis - kaip eskize.
            h = max(6.0, min(self.height() - 2.0, lygis * (self.height() - 2)))
            p.setBrush(GINTARAS if lygis > 0.03 else GINTARAS_BLANKUS)
            p.drawRoundedRect(int(x), int(vidurys - h / 2), plotis, int(h), 2.0, 2.0)
            x += plotis + tarpas
        p.end()


class Diktuokle(QWidget):
    # Fono gijos (modeliu krovimas, transkripcija, klavisu klausytojas) lango
    # NELIECIA - jos siuncia signalus, o Qt juos pristato GUI gijoje.
    busena_sig = pyqtSignal(str, str)      # tekstas, spalva
    komanda_sig = pyqtSignal(str)          # "abc123" arba "kalba"

    def __init__(self):
        super().__init__()
        self.recording = False
        self.number_mode = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.model = None
        self.model_lt = None
        self.punct = None
        self.listener = None
        # Nustatymai issaugomi tarp paleidimu (2026-09-11): su dviem kalbomis be
        # to erzina - kiekvienas startas grazintu ne ta kalba ir ne ta skyryba.
        self.nust = skaityk_nustatymus()
        # Sasajos kalba PRIES kuriant langa - kitaip mygtukai spetu atsirasti
        # lietuviski. Jei diegiant nenurodyta, imam is Windows kalbos.
        kalba.nustatyk(self.nust["sasajos_kalba"] or kalba.os_kalba())
        self.skyryba_on = bool(self.nust["skyryba"])
        # Idiegtos kalbos - is nustatymu, isvalytos nuo nezinomu. Tuscias sarasas
        # (sugadintas failas) negali palikti lango be nė vieno mygtuko.
        # ⛔ DAUGIAUSIA DVI (Roberto sprendimas 2026-09-11). Riba kartojama CIA,
        # o ne tik instaliatoriuje, nes `nustatymai.json` yra paprastas tekstinis
        # failas - be sios eilutes ranka iraso trecia kalba ji apeitu.
        self.kalbos = ([k for k in self.nust["kalbos"] if k in KALBU_SAVYBES]
                       or ["lt"])[:2]
        self.language = (self.nust["kalba"] if self.nust["kalba"] in self.kalbos
                         else self.kalbos[0])
        self._paskutinis_shift = 0.0
        self._pikas = PIKO_GRINDYS

        self._kurk_langa()
        self.busena_sig.connect(self._nustatyk_busena)
        self.komanda_sig.connect(self._vykdyk_komanda)

        self.laikmatis = QTimer(self)
        self.laikmatis.timeout.connect(self.banga.update)
        self.laikmatis.start(PIESIMO_DAZNIS)

        # Klausimai apie trukstamus modelius ir CUDA - CIA, GUI gijoje, pries
        # paleidziant krovima. Pats siuntimas vyksta fono gijoje, be jokiu langu.
        self._klausk_apie_modelius()
        self._klausk_apie_plokste()
        threading.Thread(target=self._krauk_modelius, daemon=True).start()

    # --- Langas ------------------------------------------------------------
    def _kurk_langa(self):
        self.setObjectName("saknis")
        self.setStyleSheet(STILIUS)
        self.setWindowTitle(f"{LANGO_VARDAS} — {KALBU_VARDAI[self.language]} [{self.language}]")
        if os.path.exists(IKONA):
            self.setWindowIcon(QIcon(IKONA))
        # Is nustatymu, ne kietai: zmogus nuemes "visada virsuje" tikisi, kad
        # kita karta programa pakils taip, kaip jis paliko.
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(self.nust["virsuje"]))
        # Dydi uzfiksuojam PO isdestymo - zr. _kurk_langa pabaiga.

        # Kalbu mygtukai kuriami PAGAL IDIEGTAS kalbas (2026-09-11). Vardai -
        # endonimai ("Lietuvių", "Русский"), NEVERCIAMI: kiekviena kalba vadinasi
        # savo pacia kalba, tad atpazistama bet kurioje sasajoje.
        # partial, ne lambda: uzdarymo grėblys (visos lambdos rodytu i paskutine
        # ciklo reiksme) cia realus, nes ciklas sukasi per kintama sarasa.
        from functools import partial
        self.kalbu_mygtukai = {}
        for kodas in self.kalbos:
            b = QPushButton(KALBU_VARDAI[kodas])
            b.clicked.connect(partial(self._nustatyk_kalba, kodas))
            self.kalbu_mygtukai[kodas] = b

        self.b_abc = QPushButton("ABC")
        self.b_123 = QPushButton("123")
        self.b_abc.clicked.connect(lambda: self._nustatyk_rezima(False))
        self.b_123.clicked.connect(lambda: self._nustatyk_rezima(True))

        skirtukas = QLabel("|")
        skirtukas.setStyleSheet("color: #4a4a4a;")

        virsus = QHBoxLayout()
        virsus.setSpacing(6)
        # Be tempiklio: mygtukai uzpildo visa ploti, tad "123" baigiasi ten,
        # kur langas, o "?" apacioje atsiduria tiesiai po juo (eskizas).
        for kodas in self.kalbos:
            virsus.addWidget(self.kalbu_mygtukai[kodas])
        # Skirtukas tik tada, kai yra ka skirti - su viena kalba jis kabotu
        # vienas prie krasto.
        if len(self.kalbos) > 1:
            virsus.addWidget(skirtukas)
        for w in (self.b_abc, self.b_123):
            virsus.addWidget(w)

        self.taskas = QLabel("●")
        self.taskas.setStyleSheet("color: #888888; font-size: 15px;")
        self.busena = QLabel(t("Kraunu…"))
        self.busena.setObjectName("busena")
        self.busena.setFixedWidth(84)

        self.banga = Banga()

        self.b_nust = QPushButton("⚙")
        self.b_nust.setObjectName("ikona")
        self.b_nust.clicked.connect(self._rodyk_nustatymus)
        # "?" - seimos standartas (PLANAS sprendimas 37, SDF etalonas):
        # meniu su trim punktais, instrukcija gyvena PACIOJE programoje.
        self.b_pag = QPushButton("?")
        self.b_pag.setObjectName("ikona")
        self.b_pag.setToolTip(t("Pagalba"))
        pagalba = QMenu(self.b_pag)
        pagalba.addAction(t("Apie..."), self._rodyk_apie)
        pagalba.addAction(t("Instrukcija"), self._rodyk_instrukcija)
        pagalba.addAction(t("Neradote atsakymo? Klauskite DI"), self._klausk_di)
        self.b_pag.setMenu(pagalba)

        # Be klaviaturos fokuso: kitaip paskutinis paspaustas (ar rodykle
        # perjungtas) mygtukas lieka su punktyriniu remeliu (Roberto pastaba
        # 09-08). Lange klaviatura vaiksciot nereikia - viska valdo pele ir R-Ctrl.
        for b in (list(self.kalbu_mygtukai.values())
                  + [self.b_abc, self.b_123, self.b_nust, self.b_pag]):
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        apacia = QHBoxLayout()
        apacia.setSpacing(8)
        apacia.addWidget(self.taskas)
        apacia.addWidget(self.busena)
        apacia.addWidget(self.banga)
        apacia.addStretch(1)
        apacia.addWidget(self.b_nust)
        apacia.addWidget(self.b_pag)

        visas = QVBoxLayout(self)
        visas.setContentsMargins(12, 10, 12, 10)
        visas.setSpacing(8)
        visas.addLayout(virsus)
        visas.addLayout(apacia)

        self._perpiesk_mygtukus()
        # Plotis - kiek reikia turiniui, ne is akies. Tada uzfiksuojam, kad
        # langas nei tempytusi, nei trauktusi.
        self.adjustSize()
        self.setFixedSize(self.sizeHint())

    def _perpiesk_mygtukus(self):
        """Aktyvumas per savybe + polish: QSS taisykle [aktyvus="taip"] pati
        parenka spalva, todel spalvos kode nekartojamos."""
        poros = [(b, self.language == k) for k, b in self.kalbu_mygtukai.items()]
        poros += [(self.b_abc, not self.number_mode), (self.b_123, self.number_mode)]
        for mygtukas, aktyvus in poros:
            mygtukas.setProperty("aktyvus", "taip" if aktyvus else "ne")
            mygtukas.style().unpolish(mygtukas)
            mygtukas.style().polish(mygtukas)

        # "123" anglu kalbai neveikia: skaiciu pletiklis turi tik LT ir RU
        # zodynus. Geriau pilkas mygtukas, nei tylus blogas rezultatas.
        yra_skaiciai = KALBU_SAVYBES[self.language]["skaiciai"]
        self.b_123.setEnabled(yra_skaiciai)
        if not yra_skaiciai and self.number_mode:
            self.number_mode = False
            self.b_abc.setProperty("aktyvus", "taip")
            self.b_123.setProperty("aktyvus", "ne")
            for b in (self.b_abc, self.b_123):
                b.style().unpolish(b)
                b.style().polish(b)

    # --- Busena ir komandos (slotai; kviecia signalai is fono gijų) ---------
    def _nustatyk_busena(self, tekstas, spalva):
        self.busena.setText(tekstas)
        self.taskas.setStyleSheet(f"color: {spalva}; font-size: 15px;")

    def _vykdyk_komanda(self, kuri):
        if kuri == "abc123":
            self._nustatyk_rezima(not self.number_mode)
        else:
            # Ciklas, ne apvertimas: su dviem kalbomis elgiasi lygiai taip pat
            # kaip anksciau ("spusteli - apsivertė"), su trimis sukasi ratu.
            # Sitai buvo numatyta dar 09-08: "atsiradus treciai kalbai apvertimas
            # savaime tampa ciklu - sprendimo keisti nereikes".
            if len(self.kalbos) > 1:
                i = self.kalbos.index(self.language)
                self._nustatyk_kalba(self.kalbos[(i + 1) % len(self.kalbos)])

    def _nustatyk_rezima(self, skaiciai):
        # Kalbai be skaiciu zodyno "123" neijungiamas net klavisu - kitaip
        # rodykle apeitu pilka mygtuka ir zmogus gautu tyliai bloga teksta.
        if skaiciai and not KALBU_SAVYBES[self.language]["skaiciai"]:
            return
        self.number_mode = skaiciai
        self._perpiesk_mygtukus()
        self._zurnalas(f"Rezimas: {'123' if skaiciai else 'ABC'}")

    def _nustatyk_kalba(self, kodas):
        self.language = kodas
        vardas = KALBU_VARDAI[kodas]
        self.setWindowTitle(f"{LANGO_VARDAS} — {vardas} [{kodas}]")
        self._perpiesk_mygtukus()
        self._issaugok(kalba=kodas)
        self._zurnalas(f"Kalba: {vardas} [{kodas}]")

    # --- Dantratis ir klaustukas -------------------------------------------
    def _rodyk_nustatymus(self):
        meniu = QMenu(self)
        v_sk = QAction(t("Skyryba ir didžiosios"), self, checkable=True)
        v_sk.setChecked(self.skyryba_on)
        v_sk.triggered.connect(self._perjunk_skyryba)
        meniu.addAction(v_sk)

        v_vir = QAction(t("Visada viršuje"), self, checkable=True)
        v_vir.setChecked(bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        v_vir.triggered.connect(self._perjunk_virsuje)
        meniu.addAction(v_vir)

        meniu.addSeparator()
        # Zurnalas - DVI varneles, ne viena (2026-09-11). Pirmoji ijungia
        # technika, antroji prideda pati padiktuota teksta. Antroji pilka, kol
        # pirmoji isjungta: be zurnalo teksto vis tiek nebutu kur deti.
        v_zur = QAction(t("Rašyti derinimo žurnalą"), self, checkable=True)
        v_zur.setChecked(bool(self.nust["zurnalas"]))
        v_zur.triggered.connect(self._perjunk_zurnala)
        meniu.addAction(v_zur)

        v_tek = QAction(t("Žurnale saugoti ir tekstą"), self, checkable=True)
        v_tek.setChecked(bool(self.nust["zurnale_tekstas"]))
        v_tek.setEnabled(bool(self.nust["zurnalas"]))
        v_tek.triggered.connect(self._perjunk_zurnalo_teksta)
        meniu.addAction(v_tek)

        # Spaudziama eilute (Roberto 09-08: "loga kazkur raso, tai ji galima
        # issikviesti butu") - tik kai yra ka rodyti.
        if self.nust["zurnalas"]:
            v_z = QAction(t("Žurnalas: {}…").format(os.path.basename(ZURNALO_FAILAS)), self)
            v_z.triggered.connect(self._rodyk_zurnala)
            meniu.addAction(v_z)

        meniu.addSeparator()
        # Sakinys tikslus, o ne grazus: nustatymai i diska RASOMI, tad zadeti
        # "nerasom nieko" butu melas. Bet garsas ir tekstas is kompiuterio
        # neiseina niekada - o tai ir yra tai, del ko zmogus nerimauja.
        apacia = [t("Garsas ir tekstas lieka šiame kompiuteryje")]
        if not self.nust["zurnalas"]:
            apacia.append(t("Žurnalas nerašomas"))
        # Sakom TIESA apie tai, kas kalba klauso. Jei Paprikos nera, zmogus turi
        # tai matyti - kitaip jis manytu, kad girdi geriausia, ka turim.
        if self.model_lt is not None or PAPRIKA_PATH is not None:
            apacia.append(t("Ausys: Paprika — Kristijonas Jakubsonas"))
        else:
            apacia.append(t("Ausys: bendrasis modelis (Paprika neįdiegta)"))
        for tekstas in apacia:
            v = QAction(tekstas, self)
            v.setEnabled(False)
            meniu.addAction(v)

        meniu.exec(self.b_nust.mapToGlobal(self.b_nust.rect().bottomLeft()))

    def _rodyk_zurnala(self):
        """Paskutines zurnalo eilutes pacios programos lange, naujausios
        apacioje. "Rodyti faila" - Explorer su pazymetu failu, jei reikes siusti."""
        try:
            with open(ZURNALO_FAILAS, encoding="utf-8", errors="replace") as f:
                eilutes = f.readlines()[-300:]
        except OSError:
            eilutes = [t("(žurnalo dar nėra)") + "\n"]
        dlg = QDialog(self)
        dlg.setWindowTitle(t("Žurnalas — {}").format(os.path.basename(ZURNALO_FAILAS)))
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(14, 14, 14, 12)
        rodinys = QPlainTextEdit("".join(eilutes))
        rodinys.setReadOnly(True)
        rodinys.setFont(QFont("Consolas", 10))
        rodinys.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        lay.addWidget(rodinys)

        eilute = QHBoxLayout()
        b_rodyk = QPushButton(t("Rodyti failą"))
        b_rodyk.clicked.connect(
            lambda: os.startfile(os.path.dirname(ZURNALO_FAILAS)))
        eilute.addWidget(b_rodyk)
        eilute.addStretch(1)
        b_uzd = QPushButton(t("Uždaryti"))
        b_uzd.clicked.connect(dlg.reject)
        eilute.addWidget(b_uzd)
        lay.addLayout(eilute)

        dlg.resize(820, 520)
        # Naujausios eilutes apacioje - ten ir slenkam.
        rodinys.verticalScrollBar().setValue(rodinys.verticalScrollBar().maximum())
        dlg.exec()

    def _issaugok(self, **pakeitimai):
        """Viena vieta, kur nustatymai keiciami ir irasomi - kad neliktu vietos,
        kuri pakeicia atmintyje, bet pamirsta diske."""
        self.nust.update(pakeitimai)
        rasyk_nustatymus(self.nust)

    def _perjunk_skyryba(self, ijungta):
        self.skyryba_on = bool(ijungta)
        self._issaugok(skyryba=self.skyryba_on)
        self._zurnalas(f"Skyryba: {'ijungta' if ijungta else 'isjungta'}")

    def _perjunk_virsuje(self, ijungta):
        # setWindowFlag paslepia langa, todel po jo butinas show().
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(ijungta))
        self.show()
        self._issaugok(virsuje=bool(ijungta))

    def _perjunk_zurnala(self, ijungta):
        """Technikos zurnalas: irenginys, modeliu krovimo laikai, klaidos.
        Isjungiant kartu nukrenta ir teksto varnele - kitaip ji liktu pazymeta
        nieko nedaranti ir kita karta ijungus zurnala tekstas imtu byreti be
        zmogaus zinios."""
        ijungta = bool(ijungta)
        if ijungta:
            self._issaugok(zurnalas=True)
        else:
            self._issaugok(zurnalas=False, zurnale_tekstas=False)
        self._zurnalas(f"Zurnalas: {'ijungtas' if ijungta else 'isjungtas'}")

    def _perjunk_zurnalo_teksta(self, ijungta):
        """PLIUS pats padiktuotas tekstas. Ijungiant klausiama, nes zmogus turi
        zinoti, kad nuo dabar jo laiskai ir slaptazodziai guls i faila - tai ne
        nustatymas, o sprendimas."""
        if ijungta:
            if not self._klausk(
                    t("Žurnale saugoti ir tekstą"),
                    t("Nuo šiol į žurnalą bus įrašomas VISAS padiktuotas tekstas —\n"
                      "viskas, ką pasakysite: laiškai, sveikatos reikalai, balsu\n"
                      "ištartas slaptažodis.\n\n"
                      "Failas lieka jūsų kompiuteryje ir niekur nesiunčiamas, bet\n"
                      "prieš siųsdami jį kam nors pagalbos — perskaitykite, kas jame.\n\n"
                      "Įjungti?"),
                    numatytas_taip=False):
                return
        self._issaugok(zurnale_tekstas=bool(ijungta))

    # --- "?" meniu punktai (FOTO namu receptas, tamsiu stiliumi) ------------
    def _uzdarymo_mygtukas(self, dlg):
        eilute = QHBoxLayout()
        eilute.addStretch(1)
        b = QPushButton(t("Uždaryti"))
        b.clicked.connect(dlg.reject)
        eilute.addWidget(b)
        return eilute

    def _rodyk_apie(self):
        """Apie... - logo, pavadinimas, aprasas, versija, autoriai, nuoroda.
        Tinklas TIK paspaudus nuoroda."""
        dlg = QDialog(self)
        dlg.setWindowTitle(t("Apie programą"))
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(10)

        virsus = QHBoxLayout()
        virsus.setSpacing(14)
        logo = QLabel()
        if os.path.exists(IKONA):
            logo.setPixmap(QIcon(IKONA).pixmap(64, 64))
        virsus.addWidget(logo, alignment=Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(4)
        pavadinimas = QLabel("Diktuoklė")
        pavadinimas.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        info.addWidget(pavadinimas)
        info.addWidget(QLabel(t("Lietuviškas diktavimas be interneto —\n"
                                "garsas niekur nesiunčiamas, viskas lieka kompiuteryje.")))
        info.addWidget(QLabel(t("Versija {}").format(VERSIJA)))
        autoriai = QLabel("Robertas & Claude")
        autoriai.setStyleSheet("color: #8f8f8f;")
        info.addWidget(autoriai)
        # DI zymejimas VIRSUJE, ne aprase apacioje (ES DI akto 50 str.,
        # nuo 2026-08-02; sudi.lt/gidai/di-turinio-zymejimas). Kodas ir ikona
        # - DI; padiktuotas tekstas - vartotojo, todel tai pasakoma atskirai.
        di = QLabel(t("Sukurta naudojant DI: kodą rašė Claude, ikona — DI.\n"
                      "Padiktuotas tekstas yra jūsų — DI jį tik užrašo."))
        di.setStyleSheet("color: #E8B84B; font-size: 12px;")
        info.addWidget(di)
        virsus.addLayout(info)
        lay.addLayout(virsus)

        ausys = QLabel(t("Lietuviškos ausys — Paprika, Kristijonas Jakubsonas (CC BY 4.0)\n"
                         "Skyryba — punct_restore, Kristijonas Jakubsonas (Apache 2.0)\n"
                         "Variklis — faster-whisper (MIT)"))
        ausys.setStyleSheet("color: #9a9a9a; font-size: 12px;")
        lay.addWidget(ausys)

        nuoroda = QLabel(f'{t("Kūrėjo puslapis:")} <a href="{KUREJO_PUSLAPIS}" '
                         'style="color:#4f9cf7; font-weight:bold;">GitHub</a>')
        nuoroda.setOpenExternalLinks(True)
        lay.addWidget(nuoroda)
        lay.addLayout(self._uzdarymo_mygtukas(dlg))
        dlg.exec()

    def _rodyk_instrukcija(self):
        """Instrukcija: README rodomas pacios programos lange su slinktimi.
        Jokio Notepad, jokio tinklo."""
        try:
            with open(README, encoding="utf-8", errors="replace") as f:
                tekstas = f.read()
        except OSError as e:
            QMessageBox.warning(self, t("Pagalba"),
                                t("Nepavyko atidaryti README: {}").format(e))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t("Instrukcija"))
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(14, 14, 14, 12)
        rodinys = QPlainTextEdit(tekstas)
        rodinys.setReadOnly(True)
        rodinys.setFont(QFont("Consolas", 10))   # ASCII antrastes lygiuojasi
        lay.addWidget(rodinys)
        lay.addLayout(self._uzdarymo_mygtukas(dlg))
        dlg.resize(720, 540)
        dlg.exec()

    def _klausk_di(self):
        """Atidaro claude.ai su paruostu promptu. claude.ai/new?q= tik
        UZPILDO lauka - siuncia pats vartotojas. Tinklas TIK cia."""
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Neradote atsakymo? Klauskite DI")
        if os.path.exists(IKONA):
            dlg.setIconPixmap(QIcon(IKONA).pixmap(64, 64))
        dlg.setText(
            "Kas įvyks paspaudus OK:\n\n"
            "1. Atsidarys interneto naršyklė su DI padėjėjo claude.ai\n"
            "   puslapiu. Žinutės laukelyje jau bus įrašyta angliška\n"
            "   pradžia — prisistatymas, kas per programa.\n"
            "2. NEIŠSIGĄSKITE raudono pranešimo virš žinutės —\n"
            "   claude.ai jį rodo visada, kai tekstas ateina per nuorodą.\n"
            "3. Žinutės gale, po žodžių „My question:“, įrašykite SAVO\n"
            "   klausimą — galima lietuviškai! — ir spauskite siuntimą.\n"
            "4. Jei DI atsakys angliškai — paprašykite: „atsakyk\n"
            "   lietuviškai“.\n\n"
            "Pastaba: claude.ai gali paprašyti prisijungti (nemokama\n"
            "paskyra). Niekas neišsiunčiama be jūsų rankos.")
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok
                               | QMessageBox.StandardButton.Cancel)
        dlg.button(QMessageBox.StandardButton.Cancel).setText(t("Atšaukti"))
        if dlg.exec() != QMessageBox.StandardButton.Ok:
            return
        # Roberto testas 2026-09-11: paspaudes "?" jis pamate, kad nuoroda veda
        # i profili, o ne i programa - repo dar nebuvo. Dabar: asistentui pirma
        # duodamas BRIEF (ka gali teigti, ko ne, simptomu lentele), ir tik tada
        # klausimas - kaip Reginutes README daro zmogui.
        promptas = (
            f"Please read {BRIEF_URL} first - it is the author's briefing about"
            ' the app "Diktuoklė" (Lithuanian/Russian/English offline voice'
            " dictation for Windows; hold Right Ctrl to dictate; nothing leaves"
            f" the PC). Source and README: {KUREJO_PUSLAPIS}. Then answer my"
            " question in plain, human language, in the language I write in,"
            " no programmer jargon. My question: ")
        webbrowser.open("https://claude.ai/new?q=" + urllib.parse.quote(promptas))

    # --- Zurnalas ----------------------------------------------------------
    def _zurnalas(self, tekstas, tipas="info"):
        """Rasoma TIK jei zmogus pats ijunge (dovanoje isjungta).

        tipas="tekstas" zymi eilutes, kuriose guli pats padiktuotas turinys -
        joms maza to, kad zurnalas ijungtas: reikia ATSKIROS varneles. Taip
        zmogus, prasantis pagalbos, gali nusiusti technini zurnala nesiusdamas
        savo laisku ir ligos istoriju.

        Klaidos ("warn") busenos eiluteje rodomos VISADA, nepriklausomai nuo
        zurnalo - kitaip zmogus apie jas nesuzinotu is viso.
        """
        if tipas == "warn":
            self.busena_sig.emit(tekstas[:22], "#ff6a6a")
        if not self.nust["zurnalas"]:
            return
        if tipas == "tekstas" and not self.nust["zurnale_tekstas"]:
            return
        try:
            os.makedirs(os.path.dirname(ZURNALO_FAILAS), exist_ok=True)
            with open(ZURNALO_FAILAS, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{tipas}] {tekstas}\n")
        except Exception:
            pass

    # --- Klausimas su lietuviskais mygtukais --------------------------------
    def _klausk(self, antraste, tekstas, numatytas_taip=True):
        """QMessageBox.question() statinis - jo mygtukai VISADA "Yes/No", nes
        Qt standartiniai neiseina per musu t(). Roberto testas 2026-09-11:
        lietuviskas langas su angliskais mygtukais. Todel egzempliorius, o
        mygtuku tekstai - per zodyna. Grazina True, jei zmogus sutiko."""
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setWindowTitle(antraste)
        dlg.setText(tekstas)
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dlg.button(QMessageBox.StandardButton.Yes).setText(t("Taip"))
        dlg.button(QMessageBox.StandardButton.No).setText(t("Ne"))
        dlg.setDefaultButton(QMessageBox.StandardButton.Yes if numatytas_taip
                             else QMessageBox.StandardButton.No)
        return dlg.exec() == QMessageBox.StandardButton.Yes

    # --- Modeliu parsisiuntimas (pirmas paleidimas) -------------------------
    def _klausk_apie_modelius(self):
        """⚠️ TIK GUI GIJOJE. Qt langu is fono gijos kurti negalima (OKF
        pyqt6_threading_signals_guard), o cia yra dialogas - tad ši dalis
        vyksta PRIES paleidziant krovimo gija, o pats siuntimas - joje.

        Uzpildo self._siusti sarasa tuo, ka zmogus leido parsisiusti."""
        self._siusti = []
        try:
            from parsisiuntimas import ko_truksta
            truksta = ko_truksta(self.kalbos)
        except Exception as e:
            self._zurnalas(f"Modeliu patikra nepavyko: {e}", "warn")
            return
        if not truksta:
            return

        gb = sum(mb for _, _, mb in truksta) / 1000.0
        sutiko = self._klausk(
            t("Reikia parsisiųsti kalbos modelius"),
            t("Pasirinktoms kalboms trūksta modelių — reikės parsisiųsti\n"
              "apie {} GB.\n\n"
              "Tai vienkartinis veiksmas: po jo programa veiks be interneto,\n"
              "ir garsas niekur nebus siunčiamas.\n\n"
              "Parsisiųsti dabar?").format(f"{gb:.1f}"))
        if sutiko:
            self._siusti = truksta
        else:
            # Neatsisakom programos - tegu veikia su tuo, ka turi. Lietuviu
            # kalba tada suksis ant bendrojo modelio, ir dantratis tai pasakys.
            self._zurnalas("Zmogus atsisake parsisiusti modelius")

    def _klausk_apie_plokste(self):
        """⚠️ TIK GUI GIJOJE. Jei yra NVIDIA tvarkykle, o CUDA biblioteku dar
        nera - pasiulom parsisiusti VIENA karta. Roberto testas 2026-09-11: su
        gera plokste gavo procesoriaus greiti, nes pakete biblioteku nera."""
        self._siusti_cuda = False
        if CPU_REZIMAS:
            return                      # zmogus pats prase procesoriaus
        try:
            import cuda
            if not cuda.plokste_yra() or cuda.bibliotekos_yra():
                return
        except Exception as e:
            self._zurnalas(f"Plokstes patikra nepavyko: {e}")
            return
        self._siusti_cuda = self._klausk(
            t("Rasta NVIDIA vaizdo plokštė"),
            t("Kompiuteryje yra NVIDIA vaizdo plokštė. Su ja atpažinimas vyksta\n"
              "maždaug dvidešimt kartų greičiau — 0,2 s vietoj 3 s.\n\n"
              "Tam reikia vieną kartą parsisiųsti apie {} GB bibliotekų.\n"
              "Be jų programa veiks, tik ant procesoriaus.\n\n"
              "Parsisiųsti dabar?").format("1,7"))
        if not self._siusti_cuda:
            self._zurnalas("Zmogus atsisake CUDA biblioteku - liks procesorius")

    # --- Modeliai ----------------------------------------------------------
    def _krauk_modelius(self):
        # global - funkcijos PRADZIOJE (Python reikalauja pries pirma panaudojima).
        # Sie trys gali pasikeisti cia pat: krentant is CUDA i procesoriu ir
        # atsiradus ka tik parsisiustai Paprikai.
        global IRENGINYS, CT_LARGE, CT_PAPRIKA, PAPRIKA_PATH
        self.busena_sig.emit(t("Kraunu…"), "#ffaa00")
        # Siuntimas - fono gijoje, be jokiu langu (juos jau parode GUI gija).
        if getattr(self, "_siusti", None):
            from parsisiuntimas import parsisiusk
            for raktas, repo, _mb in self._siusti:
                self.busena_sig.emit(t("Siunčiu…"), "#ffaa00")
                try:
                    t0 = time.time()
                    parsisiusk(raktas, repo)
                    self._zurnalas(f"{raktas} parsisiustas per {time.time() - t0:.0f} s")
                except Exception as e:
                    # Nenutraukiam visko del vieno: gal kita kalba pavyks.
                    self._zurnalas(f"{raktas} PARSISIUSTI NEPAVYKO: {e}", "warn")
            self._siusti = []
            # Paprikos kelias galejo ka tik atsirasti - perklausiam is naujo.
            try:
                from modeliai import paprikos_kelias
                PAPRIKA_PATH = paprikos_kelias()
            except Exception:
                pass
        # CUDA bibliotekos: parsisiunciam, jei zmogus leido, ir ijungiam, jei yra.
        # PRIES kraunant modelius - ctranslate2 DLL ieskos tada, kai jam reikes.
        if not CPU_REZIMAS:
            try:
                import cuda
                if getattr(self, "_siusti_cuda", False):
                    self.busena_sig.emit(t("Siunčiu…"), "#ffaa00")
                    t0 = time.time()
                    cuda.parsisiusk(pranesk=lambda s: self._zurnalas(f"[cuda] {s}"))
                    self._zurnalas(f"CUDA bibliotekos parsisiustos per {time.time() - t0:.0f} s")
                    self._siusti_cuda = False
                if cuda.ijunk():
                    self._zurnalas("CUDA bibliotekos ijungtos: " + cuda.CUDA_KATALOGAS)
                else:
                    # Biblioteku nera - CUDA nepavyks; nebandom, is karto CPU.
                    # Sutaupom ~5 s (krovimas i plokste + patikra + perkrovimas).
                    IRENGINYS, CT_LARGE, CT_PAPRIKA = "cpu", "int8", "int8"
                    self._zurnalas("CUDA biblioteku nera - is karto procesorius")
            except Exception as e:
                self._zurnalas(f"CUDA paruosimas nepavyko: {e}", "warn")
                IRENGINYS, CT_LARGE, CT_PAPRIKA = "cpu", "int8", "int8"

        gijos = CPU_GIJOS if CPU_REZIMAS else 0
        self._zurnalas(f"irenginys: {IRENGINYS}" + (f", giju {CPU_GIJOS}" if CPU_REZIMAS else ""))
        try:
            t0 = time.time()
            self.model = WhisperModel(MODEL_SIZE, device=IRENGINYS, compute_type=CT_LARGE,
                                      cpu_threads=gijos)
            self._zurnalas(f"{MODEL_SIZE} uzkrautas per {time.time() - t0:.1f} s ({CT_LARGE})")
        except Exception as e:
            # ⚠️ Cia sprendziasi, ar programa eiliniam zmogui apskritai pakyla.
            # Pakete CUDA NERA (su ja butu +2 GB, o NVIDIA turi mazuma), tad
            # `device="cuda"` svetimoje masinoje mes klaida - ir be sio kritimo
            # zmogus gautu tik "MODELIS NEPAKILO". Krentam i procesoriu: leciau
            # (~3 s sakiniui pries 0,15 s), bet veikia. Tas pats kritimas gelbsti
            # ir tada, kai NVIDIA yra, bet tvarkykles per senos.
            self._zurnalas(f"{IRENGINYS} nepavyko ({e}); bandom procesoriu", "warn")
            try:
                t0 = time.time()
                IRENGINYS, CT_LARGE, CT_PAPRIKA = "cpu", "int8", "int8"
                gijos = os.cpu_count() or 4
                self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8",
                                          cpu_threads=gijos)
                self._zurnalas(f"{MODEL_SIZE} uzkrautas ant CPU per {time.time() - t0:.1f} s")
            except Exception as e2:
                self._zurnalas(f"MODELIS NEPAKILO: {e2}", "warn")
                return

        # Paprika gali buti nerasta (svetimas kompiuteris, kur jos niekas nepadejo).
        # Tada NEKRINTAM ir nedarom lietuviu kalbos neveikiancios: krentam i
        # large-v3. Jis lietuviskai silpnesnis (musu matavimu 25,95 % WER pries
        # Paprikos 7,63 %), bet blogiau yra geriau, nei niekaip - svarbu, kad
        # zmogus ZINOTU, ir tai pasakyta dantratyje.
        if PAPRIKA_PATH is None:
            self.model_lt = None
            from modeliai import kur_ieskota
            self._zurnalas("Paprika nerasta; lietuviu kalba suksis ant "
                           + MODEL_SIZE + ". Ieskota: " + " | ".join(kur_ieskota()))
        else:
            try:
                t0 = time.time()
                self.model_lt = WhisperModel(PAPRIKA_PATH, device=IRENGINYS,
                                             compute_type=CT_PAPRIKA, cpu_threads=gijos)
                self._zurnalas(f"Paprika uzkrauta per {time.time() - t0:.1f} s ({CT_PAPRIKA})")
            except Exception as e:
                self.model_lt = None
                self._zurnalas(f"PAPRIKA NEPAKILO: {e}", "warn")

        try:
            t0 = time.time()
            from punct_restore import Punctuator
            self.punct = Punctuator()
            self.punct.restore("apsilimas")
            self._zurnalas(f"Skyryba paruosta per {time.time() - t0:.1f} s")
        except Exception as e:
            self.punct = None
            self._zurnalas(f"SKYRYBA NEPAKILO: {e}", "warn")

        # ⚠️ CUDA PATIKRA ATPAZINIMU, ne krovimu (2026-09-11, Roberto testas).
        # ctranslate2 modeli i vaizdo plokste UZKRAUNA net tada, kai cuBLAS nera:
        # zurnale buvo "large-v3 uzkrautas 2.2 s (float16)", o klaida
        # "Library cublas64_12.dll is not found" atejo tik pirmo diktavimo metu.
        # Del to atsarginis kelias i procesoriu, sedejes krovimo dalyje, nesuveike
        # NIEKADA - zmogui atrode, kad programa "ilgai galvoja", o ji tiesiog
        # kaskart luzo. Todel cia paleidziam bandomaji atpazinima ant pusės
        # sekundes tylos: pigu (~0,2 s), bet pagauna VISAS vaizdo plokstes bedas
        # - trukstamas DLL, senas tvarkykles, per maza atminti - dar PRIES tai,
        # kai zmogus paspaudzia Ctrl.
        if IRENGINYS != "cpu" and not self._plokste_tikrai_veikia():
            self._perkrauk_i_cpu()

        self.busena_sig.emit(t("Pasiruošęs"), "#4ADE80")
        self._start_klausytoja()

    def _plokste_tikrai_veikia(self):
        """True, jei modelis sugeba ATPAZINTI, ne tik uzsikrauti."""
        try:
            tyla = np.zeros(SAMPLE_RATE // 2, dtype=np.float32)
            t0 = time.time()
            segmentai, _ = self.model.transcribe(audio=tyla, language="lt",
                                                 beam_size=1, vad_filter=False)
            list(segmentai)       # generatorius - be sito niekas neivyksta
            self._zurnalas(f"Plokstes patikra praejo per {time.time() - t0:.2f} s")
            return True
        except Exception as e:
            self._zurnalas(f"Vaizdo plokste neveikia ({e}); pereinam i procesoriu",
                           "warn")
            return False

    def _perkrauk_i_cpu(self):
        """Perkrauna tuos pacius modelius procesoriuje. Lietuviu kalbai svarbu
        NEPRARASTI Paprikos - be jos kokybe nukristu nuo 7,63 % iki 25,95 % WER."""
        global IRENGINYS, CT_LARGE, CT_PAPRIKA
        IRENGINYS, CT_LARGE, CT_PAPRIKA = "cpu", "int8", "int8"
        gijos = os.cpu_count() or 4
        try:
            t0 = time.time()
            self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8",
                                      cpu_threads=gijos)
            self._zurnalas(f"{MODEL_SIZE} perkrautas i CPU per {time.time() - t0:.1f} s")
        except Exception as e:
            self._zurnalas(f"CPU PERKROVIMAS NEPAVYKO: {e}", "warn")
            return
        if PAPRIKA_PATH:
            try:
                t0 = time.time()
                self.model_lt = WhisperModel(PAPRIKA_PATH, device="cpu",
                                             compute_type="int8", cpu_threads=gijos)
                self._zurnalas(f"Paprika perkrauta i CPU per {time.time() - t0:.1f} s")
            except Exception as e:
                self.model_lt = None
                self._zurnalas(f"Paprika i CPU nepakilo: {e}", "warn")

    # --- Klavisai ----------------------------------------------------------
    def _start_klausytoja(self):
        self.listener = keyboard.Listener(on_press=self._klavisas_zemyn,
                                          on_release=self._klavisas_aukstyn)
        self.listener.daemon = True
        self.listener.start()

    def _klavisas_zemyn(self, key):
        if key == TRIGGER_KEY:
            self._pradek_irasyma()
            return

        # Laikant R-Ctrl rodykles yra po pat pirstu: <- ABC/123, -> kalba.
        # Irasymas NENUTRAUKIAMAS - rezimas nuskaitomas irasa baigiant, tad
        # galioja visam tam gabalui.
        if self.recording and key in (keyboard.Key.left, keyboard.Key.right):
            self.komanda_sig.emit("abc123" if key == keyboard.Key.left else "kalba")
            try:
                self.listener.suppress_event()   # kad svetimame lange
            except Exception:                    # Ctrl+rodykle neperkeltu
                pass                             # zymeklio per zodi
            return

        if key == keyboard.Key.shift_r:
            dabar = time.time()
            if dabar - self._paskutinis_shift < 0.4:
                self._paskutinis_shift = 0.0
                self.komanda_sig.emit("abc123")
            else:
                self._paskutinis_shift = dabar

    def _klavisas_aukstyn(self, key):
        if key == TRIGGER_KEY and self.recording:
            threading.Thread(target=self._baik_ir_atpazink, daemon=True).start()

    # --- Irasymas ----------------------------------------------------------
    def _pradek_irasyma(self):
        if self.recording or self.model is None:
            return
        self.recording = True
        self.frames = []
        try:
            self.stream = self.audio.open(format=pyaudio.paInt16, channels=CHANNELS,
                                          rate=SAMPLE_RATE, input=True,
                                          frames_per_buffer=CHUNK)
            threading.Thread(target=self._irasymo_ciklas, daemon=True).start()
            self.busena_sig.emit(t("Klausau"), "#ff6a6a")
        except Exception as e:
            self.recording = False
            self._zurnalas(f"Mikrofonas: {e}", "warn")

    def _irasymo_ciklas(self):
        rms_eile = []
        while self.recording:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                imtis = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = float(np.sqrt(np.mean(imtis * imtis)))
                rms_eile.append(rms)
                self._pikas = max(rms, self._pikas * PIKO_KRITIMAS, PIKO_GRINDYS)
                lygis = rms / self._pikas
                # Tik duomenys - langa perpiesia QTimer GUI gijoje.
                self.banga.lygiai = self.banga.lygiai[1:] + [min(1.0, lygis)]
            except Exception:
                break
        self.banga.lygiai = [0.0] * STULPELIU
        self._pikas = PIKO_GRINDYS
        # Matavimas, ne spejimas: kad bangos jautruma derintume pagal tikrus
        # Roberto mikrofono skaicius.
        if rms_eile:
            self._zurnalas(f"[garsas] rms min {min(rms_eile):.0f}  vid "
                           f"{sum(rms_eile) / len(rms_eile):.0f}  max {max(rms_eile):.0f}")

    def _baik_ir_atpazink(self):
        if not self.recording:
            return
        self.recording = False
        skaiciai = self.number_mode
        # NE "kalba" - tas vardas siame faile jau priklauso sasajos moduliui
        # (import kalba), ir vietinis kintamasis ji uzdengtu.
        kodas = self.language
        time.sleep(0.05)
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if not self.frames:
            self.busena_sig.emit(t("Pasiruošęs"), "#4ADE80")
            return

        self.busena_sig.emit(t("Atpažįstu"), "#ffaa00")
        try:
            garsas = np.frombuffer(b"".join(self.frames), dtype=np.int16).astype(np.float32) / 32768.0
            # initial_prompt duoda modeliui toną - 09-08 nuspresta ju NEKEISTI
            # "tuo paciu", jie ten del priezasties (maziau rasybos klaidu).
            # Angliskas pridetas ta paciu principu: prasom taisyklingos kalbos
            # su skyryba, nes large-v3 anglu kalbai ja deda pats.
            uzuomina = {
                "lt": "Tai taisyklinga lietuvių kalba su skyryba.",
                "ru": "Это правильная русская речь.",
                "en": "This is correct English speech with punctuation.",
            }[kodas]
            # Lietuviu - Paprika (Kristijono fine-tune), rusu ir anglu - tas pats
            # large-v3: vienas failas, dvi kalbos.
            naudoti_paprika = KALBU_SAVYBES[kodas]["modelis"] == "paprika"
            modelis = self.model_lt if (naudoti_paprika and self.model_lt) else self.model
            t0 = time.time()
            segmentai, _ = modelis.transcribe(audio=garsas, language=kodas, beam_size=5,
                                              vad_filter=True, initial_prompt=uzuomina)
            tekstas = " ".join(s.text.strip() for s in segmentai).strip()
            kuris = "Paprika" if modelis is self.model_lt else MODEL_SIZE
            self._zurnalas(f"[{kuris}] {time.time() - t0:.2f} s")

            if tekstas:
                # Kas atejo is modelio PRIES bet koki tvarkyma - kad skaiciu
                # klaidas aiskintumes pagal priezasti, ne pasekme.
                self._zurnalas(f"[modelis] {tekstas}", "tekstas")
                if skaiciai:
                    tekstas = words_to_numbers(tekstas, kodas)
                else:
                    # Girdeti galima bet kaip, rasyti - pagal standarta.
                    tekstas = tarimas_i_rasyba(numbers_to_words(tekstas, kodas), kodas)
                if self.punct and KALBU_SAVYBES[kodas]["skyryba"] and self.skyryba_on:
                    try:
                        t1 = time.time()
                        atstatyta, st = self.punct.restore(tekstas)
                        atstatyta = tvarkyk_po_skyrybos(atstatyta)
                        if st["refused"]:
                            self._zurnalas(f"[skyryba] atmesta {st['refused']}")
                        self._zurnalas(f"[skyryba] {(time.time() - t1) * 1000:.0f} ms")
                        tekstas = atstatyta
                    except Exception as e:
                        self._zurnalas(f"[skyryba] nepavyko: {e}", "warn")

                self._zurnalas(f"[OK] {tekstas}", "tekstas")
                pyperclip.copy(tekstas)
                time.sleep(0.05)
                ctrl = keyboard.Controller()
                ctrl.press(keyboard.Key.ctrl_l)
                ctrl.tap("v")
                ctrl.release(keyboard.Key.ctrl_l)
                ctrl.release(keyboard.Key.ctrl_l)
            else:
                self._zurnalas("[!] Nieko neatpazinta")
        except Exception as e:
            self._zurnalas(f"Atpazinimo klaida: {e}", "warn")
        finally:
            self.busena_sig.emit(t("Pasiruošęs"), "#4ADE80")

    def closeEvent(self, event):
        # ⚠️ Roberto testas 2026-09-11: uzdare langa, o PROCESAS LIKO (987 MB,
        # vis dar klauso desinio Ctrl; instaliatorius sake "Diktuokle.exe
        # naudoja failus"). Priezastis: torch / onnxruntime / ctranslate2
        # giju baseinai NE daemon - Python prie iseities ju laukia amzinai.
        # Vaistas grubus, bet vienintelis patikimas GUI programai su tokiais
        # varikliais: susitvarkom, ka galim, ir iseinam per os._exit.
        # Prarasti nera ko - nustatymai i diska rasomi keiciant, ne uzdarant.
        self.recording = False
        try:
            if self.listener:
                self.listener.stop()
        except Exception:
            pass
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
        except Exception:
            pass
        try:
            self.audio.terminate()
        except Exception:
            pass
        self._zurnalas("Uzdaroma")
        event.accept()
        os._exit(0)


if __name__ == "__main__":
    # Windows taskbar rodo MUSU ikona, ne pythonw.exe: procesas prisistato savo
    # AppUserModelID PRIES QApplication (seimos receptas - FOTO namai main.py;
    # be sito ikona taskbare atsirastu tik exe builde). Roberto pastaba 09-08.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "ClaudeGifts.Diktuokle")
    except Exception:
        pass
    # Tik VIENAS egzempliorius (09-08, prie darbalaukio nuorodos): du langai
    # abu klausytu R-Ctrl ir tekstas isikilijuotu du kartus. Pavadintas mutex -
    # antras paleidimas ji randa uzimta (ERROR_ALREADY_EXISTS = 183), pasako ir
    # iseina. Rankena laikoma globaliai, kad gyventu visa procesa.
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\ClaudeGifts.Diktuokle")
    if ctypes.windll.kernel32.GetLastError() == 183:
        app = QApplication(sys.argv)
        # Sasajos kalba ir cia - antras paleidimas ivyksta pries langa, tad
        # nustatymus nuskaitom atskirai (pigu: vienas mazas JSON).
        kalba.nustatyk(skaityk_nustatymus()["sasajos_kalba"] or kalba.os_kalba())
        QMessageBox.information(None, "Diktuoklė",
                                t("Diktuoklė jau paleista — žiūrėk užduočių juostoje."))
        sys.exit(0)
    apkarpyk_zurnala()
    app = QApplication(sys.argv)
    langas = Diktuokle()
    langas.show()
    sys.exit(app.exec())
