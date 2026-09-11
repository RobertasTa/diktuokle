# -*- coding: utf-8 -*-
"""modeliai.py - kur gyvena modeliai svetimame kompiuteryje.

Problema, kuria sis modulis sprendzia: kode keliai buvo IRASYTI KIETAI
(`D:\\_Balsas Lietuviksas\\_darbal\\paprika-ct2-int8`), nes programa gime ant
Roberto stalo. Bet kuriame kitame kompiuteryje tokio katalogo nera, ir lietuviu
kalba tiesiog nepakiltu - be jokios suprantamos klaidos.

Kuris modelis is kur ateina (patikrinta 2026-09-11 per HF API, ne prisiminta):

  large-v3 (rusu IR anglu) - `Systran/faster-whisper-large-v3`, MIT, JAU CT2
      formatu. faster-whisper parsisiuncia ji PATS, uztenka paduoti "large-v3".
  skyryba - `1-800-BAD-CODE/xlm-roberta_punctuation_fullstop_truecase`,
      Apache-2.0, ONNX. `punctuators` biblioteka parsisiuncia PATI.
  Paprika (lietuviu) - `kristijonas/paprika-whisper-lt-v3`, CC-BY-4.0, bet
      paskelbta TIK `safetensors` (transformers) formatu. faster-whisper tokio
      nevalgo. ⇒ VIENINTELIS modelis, kuriam reikia musu veiksmo.

Paprikos paieskos eile (pirmas rastas laimi):
  1. `DIKTUOKLE_PAPRIKA` aplinkos kintamasis - testams ir derinimui, be jokio
     failu kilnojimo;
  2. `modeliai\\paprika-ct2-int8` SALIA programos - taip pades instaliatorius
     (ir taip veikia flesiuko rezimas);
  3. `%LOCALAPPDATA%\\Diktuokle\\modeliai\\paprika-ct2-int8` - kai i Program
     Files rasyti negalima;
  4. HF repo vardas, jei toks paskelbtas (zr. PAPRIKA_HF) - faster-whisper
     parsisiunčia pats, kaip large-v3;
  5. Roberto darbinis kelias - TIK jo masinoje, kad jam nereiktu dubliuoti
     814 MB. Svetimam kompiuteriui sios eilutes tiesiog nera.

Jei nerandama nieko, `paprikos_kelias()` grazina None, o programa turi tai
pasakyti zmogui suprantamai, ne nukristi.
"""
import os

# Kai (jei) musu CT2 konversija bus paskelbta HF, cia irasomas jos vardas ir
# viskas suveikia savaime - faster-whisper parsisiuncia ji taip pat, kaip
# large-v3. Kol tuscia, sis kelias praleidziamas.
PAPRIKA_HF = "RobertasTa/paprika-whisper-lt-v3-ct2-int8"   # viesas nuo 2026-09-11

# Roberto masinos kelias. Cia jis TYCIA paskutinis: jei svetimame kompiuteryje
# atsirastu toks katalogas, tai butu atsitiktinumas, o ne musu numatytas kelias.
PAPRIKA_ROBERTO = r"D:\_Balsas Lietuviksas\_darbal\paprika-ct2-int8"

CIA = os.path.dirname(os.path.abspath(__file__))


def _duomenu_katalogas():
    """Ta pati seimos konvencija kaip zurnalui (SDF / FOTO namai saugykla.py)."""
    if os.path.exists(os.path.join(CIA, "Diktuokle_portable.txt")):
        return os.path.join(CIA, "Diktuokle_data")
    base = os.environ.get("LOCALAPPDATA")
    return os.path.join(base, "Diktuokle") if base else os.path.join(CIA, "Diktuokle_data")


def _yra_ct2(kelias):
    """CT2 katalogas atpazistamas is `model.bin`. Tikrinam TURINI, ne varda:
    tuscias ar pusiau parsisiustas katalogas neturi atrodyti kaip modelis."""
    return bool(kelias) and os.path.isfile(os.path.join(kelias, "model.bin"))


def paprikos_kelias():
    """Grazina katalogo kelia arba HF varda, arba None, jei nerasta niekur."""
    aplinka = os.environ.get("DIKTUOKLE_PAPRIKA")
    if _yra_ct2(aplinka):
        return aplinka

    for k in (os.path.join(CIA, "modeliai", "paprika-ct2-int8"),
              os.path.join(_duomenu_katalogas(), "modeliai", "paprika-ct2-int8")):
        if _yra_ct2(k):
            return k

    if PAPRIKA_HF:
        return PAPRIKA_HF        # faster-whisper parsisius pats

    if _yra_ct2(PAPRIKA_ROBERTO):
        return PAPRIKA_ROBERTO
    return None


def kur_ieskota():
    """Sarasas zmogui ir zurnalui, kai Paprika nerasta - kad butu aisku, KUR
    dėti, o ne tik kad 'nepavyko'."""
    return [os.environ.get("DIKTUOKLE_PAPRIKA") or "(DIKTUOKLE_PAPRIKA nenustatytas)",
            os.path.join(CIA, "modeliai", "paprika-ct2-int8"),
            os.path.join(_duomenu_katalogas(), "modeliai", "paprika-ct2-int8"),
            PAPRIKA_HF or "(HF vardas neįrašytas)",
            PAPRIKA_ROBERTO]
