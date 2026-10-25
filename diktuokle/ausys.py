# -*- coding: utf-8 -*-
"""ausys.py - naujos ausys (0.2, 2026-10-25): LT_ausys lietuviu, GigaAM v3 rusu.

Kodel jos, o ne Whisper - pamatuota tame paciame kompiuteryje, tais paciais
garsais (`_darbal/lt_ausys_palyginimas/REZULTATAI.md`, `ru/REZULTATAI_RU.md`):

  LT  Roberto komandos   WER 17,9 %  (Paprika 23,2 %)
      FLEURS             WER  9,8 %  (Paprika  9,8 %)
      ilgas diktavimas   WER 10,2 %  (Paprika 31,8 % - numeta pabaigas)
      procesoriuje 0,05 s komandai - greiciau, nei Paprika vaizdo plokstėje;
      skyryba ir didziasias deda pati.
  RU  FLEURS             WER  4,6 %  (large-v3 3,9 %), bet procesoriuje
      0,11 s sakiniui pries 7,2 s; 227 MB vietoj 3,1 GB.

Abi ausys sukasi PROCESORIUJE - CUDA joms nereikia. Variklis - onnx-asr (MIT).

⚠️ ILGI IRASAI. Abi mokytos ant trumpu gabalu. GigaAM 130 s irase pameta puse
zodziu (WER 60 %), karpant pauzėse - 5,2 %; LT_ausys karpant 3-5 kartus
greitesne. Todel ilgesni nei MAX_S kerpami TYLOS VIDURYJE. Karpo Silero VAD,
kuris jau guli faster-whisper pakete - nieko papildomai nesiunciama.

VAD dar atsako, ar kalbos IS VISO buvo. Tyloje (500 klipu) LT_ausys prirase
6 310 simboliu siuksliu, su VAD - 101: zmogus, netycia spustelejes klavisa, ju
neberas savo laiske. Trumpas irasas, kuriame kalba YRA, atpazistamas VISAS -
krastu apkarpymas komandoms kainavo +0,65 % WER (dv 16,77 -> 17,42).
"""
import numpy as np

SR = 16000
MAX_S = 20                  # spike: gabalai 9-21 s, nei vieno nukirsto zodzio


def gabalai(garsas):
    """[] - kalbos nera; kitaip [(pradzia, pabaiga)] imtimis, kiekvienas <= ~MAX_S.

    Ilgas irasas kerpamas tarp kalbos gabalu, tylos viduryje, ir pradzia/galas
    lieka kaip buvo (0 ir len) - kad nieko nenukirptume."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    kalba = get_speech_timestamps(garsas, VadOptions(
        min_silence_duration_ms=300, speech_pad_ms=200, max_speech_duration_s=MAX_S))
    if not kalba:
        return []
    if len(garsas) <= MAX_S * SR:
        return [(0, len(garsas))]
    ribos, pr = [], 0
    for a, b in zip(kalba, kalba[1:]):
        if b["end"] - pr > MAX_S * SR:      # kitas gabalas nebetilptu - kerpam cia
            kirpti = (a["end"] + b["start"]) // 2
            ribos.append((pr, kirpti))
            pr = kirpti
    ribos.append((pr, len(garsas)))
    return ribos


class OnnxAusys:
    """Vienas onnx-asr modelis is katalogo (jokio tinklo - failus jau padejo
    `parsisiuntimas.py`)."""

    def __init__(self, tipas, katalogas, gijos=0):
        import onnx_asr
        import onnxruntime as rt
        so = rt.SessionOptions()
        if gijos:
            so.intra_op_num_threads = gijos      # 0 - onnxruntime pats (fiziniai branduoliai)
        self.modelis = onnx_asr.load_model(tipas, katalogas, quantization="int8", sess_options=so)
        # Pirmas atpazinimas visada letesnis - tegu jis ivyksta kraunant, ne zmogui diktuojant.
        self.modelis.recognize(np.zeros(SR, dtype=np.float32), sample_rate=SR)

    def atpazink(self, garsas):
        """float32, 16 kHz, mono -> tekstas ("" - kalbos nebuvo)."""
        tekstas = ""
        for a, b in gabalai(garsas):
            d = self.modelis.recognize(garsas[a:b], sample_rate=SR).strip()
            if not d:
                continue
            # Ausys kiekviena gabala pradeda didziaja - jos mano, kad tai sakinio
            # pradzia. Roberto pasaka 2026-10-25: "mociute var Virdavo",
            # "geriausia Vakarai" - kirpta per pauze sakinio viduryje. Jei
            # ankstesnis gabalas sakinio NEBAIGE, mazinam. Kaina: vardas, pataikes
            # i gabalo pradzia sakinio viduryje, gaus mazaja - tai rečiau.
            # Visas didziasias ("LDSP") paliekam.
            if tekstas and tekstas[-1] not in ".?!…" and d[:1].isupper() \
                    and not d.split()[0].isupper():
                d = d[0].lower() + d[1:]
            tekstas = f"{tekstas} {d}" if tekstas else d
        return tekstas
