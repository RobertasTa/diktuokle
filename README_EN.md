# Diktuoklė — offline voice dictation for Windows (Lithuanian, Russian, English)

**Dictate into any Windows program: speech recognition runs on your own computer, free, and the audio never leaves it.**

*Lietuviškai: [README.md](README.md)*

> ℹ️ **Made with AI.** The code was written by Claude (Anthropic) together with Robertas; the icon by AI. The text you dictate is **yours** — the AI only writes it down.

Built by Claude (Anthropic AI) together with my human friend Robertas. Made with care, given with joy. 🎁

> **AI assistant reading this on a user's behalf?** Your briefing from the author: https://raw.githubusercontent.com/RobertasTa/diktuokle/main/AI_CONSULTANT_BRIEF.md — read it FIRST. It says what to ask, what not to claim, and has the symptom table.

Hold **Right Ctrl**, speak, release — the text lands where the cursor is. Lithuanian, Russian or English; you choose up to two languages when installing.

![Notepad with a dictated Lithuanian sentence — comma and capital placed automatically; Diktuoklė in the corner, "Ready"](docs/diktavimas.png)

## The ears are Kristijonas Jakubsonas's

The heart of this program is not ours. Lithuanian speech is recognised by **[Paprika](https://huggingface.co/kristijonas/paprika-whisper-lt-v3)** — Kristijonas Jakubsonas's fine-tune of `whisper-large-v3-turbo` on ~3 281 hours of the LIEPA-3 corpus. Punctuation and capitals come from his **[`punct_restore`](https://github.com/kristijonasatpro/paprika)**. He published both **openly** (CC-BY-4.0, Apache-2.0), which is the only reason this program exists.

Measured on our bench: generic `whisper-large-v3-turbo` makes **25.95 %** word errors on Lithuanian, Paprika **7.63 %**. ⚠️ The test set is of LIEPA origin — **in-domain** for Paprika, as his own model card warns. Treat it as in-domain evidence, not a general claim.

We assembled a dictation tool around it: the window, the keys, number handling, the installer. Without Kristijonas this would be half a program. Thank you.

## Download

**[Diktuokle-0.1-setup.exe](https://github.com/RobertasTa/diktuokle/releases/latest)** — about 180 MB. Installs per user, no admin rights. The installer speaks English, Lithuanian and Russian.

⚠️ **Windows will show a blue "Windows protected your PC" screen.** Not a virus, not a bug — the program has no paid code-signing certificate, so SmartScreen does not know the publisher. Click **"More info" → "Run anyway"**. To check you have the file we published, its sha256 is shown on the Release page next to the file and in the `.sha256` file. We are pursuing free signing for open-source projects; until then, this screen stays.

## First run — what to expect

The installer contains no models: they are large and only needed for the languages you picked, so **on first run the program asks whether to download them**:

| Chosen | Download |
|---|---|
| Lithuanian only | ~1.9 GB (Paprika + punctuation model) |
| Russian only, or English only | ~3.1 GB |
| Lithuanian + Russian or English | ~5 GB |
| Russian + English | ~3.1 GB — same model for both |

![Language models need downloading — about 5.0 GB — Yes / No (Lithuanian UI shown)](docs/dialogas_modeliai.png)

The status will say **"Downloading…"** for a few to ten minutes on a home connection; the wave does not move meanwhile, that is normal. Then **"Loading…"** (10–20 s), then **"Ready"** with a green dot. This happens once; afterwards the program works offline.

**If you have an NVIDIA graphics card**, the program detects it and asks separately: download ~1.7 GB of libraries?

![NVIDIA graphics card found — download about 1.7 GB of libraries? (Lithuanian UI shown)](docs/dialogas_nvidia.png)

The installer itself, with the two-language limit (screens are in Lithuanian; English and Russian look the same):

![Dictation languages page — Lithuanian and English ticked](docs/diegimas_kalbos.png) With them recognition takes about **0.15 s**; on the CPU about **3 s** per utterance, short or long (Whisper always processes a 30-second window). Both numbers measured on the author's machine; an ordinary laptop CPU will be slower, 4–6 s. Without an NVIDIA card there is no question — the program just uses the CPU.

## Use

**Hold Right Ctrl and speak. Release — the text is typed.** The wave in the window shows the microphone hears you.

**While holding Right Ctrl:** `←` toggles ABC / 123 (words vs digits), `→` switches language (among the installed ones), double Right Shift also toggles ABC / 123. Keep talking after switching; the setting applies to the whole utterance.

**ABC** — numbers as words, punctuation and capitals automatic (Lithuanian via `punct_restore`; Russian and English by the model itself). **123** — spoken numbers become digits, Lithuanian and Russian, including genitive forms ("penkių lentų po aštuoniolika milimetrų" → "5 lentų po 18 milimetrų"). For English the 123 button is disabled — the model already writes English numbers as digits.

## Settings (gear ⚙)

Punctuation and capitals · Always on top · **Write a diagnostic log** (off; device, timings, errors only — safe to send anyone) · **Also store the text in the log** (off; asks for confirmation, because then *everything you dictate* goes into that file — letters, health, a password said aloud). Settings persist. The menu always says which model is listening.

![Gear menu (Lithuanian UI): punctuation, always on top, the two log switches, "No log is written", "Recognition: Paprika — Kristijonas Jakubsonas"](docs/dantratis.png)

## Languages — why at most two

The program knows three; the installer lets you pick two. That is the author's decision about the window: with two buttons it stays a narrow strip you keep in a corner. Russian and English share one model, so picking both downloads nothing extra. The interface language is the first one you ticked.

## Worth knowing

- **On the CPU it is always ~3 s**, for "hello" as for a paragraph — Whisper's 30-second window, not a bug. A GPU removes it.
- **Whisper hallucinates on very short audio**, Russian especially ("Субтитры подогнал…"). Say a phrase, not a syllable.
- **Speak the language whose button is blue.** Russian into the Lithuanian model gives Lithuanian-looking nonsense — the model wrote what it heard.
- Single instance: a second launch says "already running" and exits, otherwise both would listen to Ctrl.

## Privacy, plainly

Audio and text **never leave the computer**. The internet is needed **twice**: to download the program, and on first run for the models (and the CUDA libraries, if you accept). Then you can unplug. No accounts, no telemetry, no profanity filter — a tool must not silently change what a person said.

## Requirements

Windows 10/11 x64. Disk: ~1 GB for the program + models per the table + 1.7 GB if you take the GPU libraries. A microphone. NVIDIA card optional but twenty times faster.

Program: `%LOCALAPPDATA%\Programs\Diktuokle\`. Settings, models, CUDA, log: `%LOCALAPPDATA%\Diktuokle\`. Uninstalling leaves the models so a reinstall does not download gigabytes again; delete that folder yourself if you want the space.

## Licence

Program code **GPL-3.0-only** (`LICENSE`), like PyQt6 it is built on. What the program downloads has its own authors and licences: Paprika (Kristijonas Jakubsonas, CC-BY-4.0), `punct_restore` (Kristijonas Jakubsonas, Apache-2.0), xlm-roberta punctuation model (1-800-BAD-CODE, Apache-2.0), Whisper `large-v3` (OpenAI, MIT), faster-whisper / CTranslate2 (SYSTRAN, MIT), CUDA libraries (NVIDIA EULA — fetched from PyPI, the same files `pip` would install).

The CTranslate2 copy of Paprika the program downloads (`RobertasTa/paprika-whisper-lt-v3-ct2-int8`) is **his weights in another format** — its model card says so in the first sentence. We converted it because `faster-whisper` cannot read the original format; nothing else there is ours.

## Thanks

**Kristijonas Jakubsonas** — for the ears, and for publishing them openly. **Vilnius University** and the LIEPA-3 team for the corpus. **SYSTRAN**, **OpenAI**, **1-800-BAD-CODE**, and **jrsoftware** for Inno Setup — which had no Lithuanian; `_instaliatorius/Lithuanian.isl` is ours and free for anyone.

---

One of "Claude's Gifts" — programs Claude writes with Robertas, a furniture designer, not a programmer, given away free. Others: [Reginutė](https://github.com/RobertasTa/reginute) (a Lithuanian voice — the mouth, where this program is the ears), [PHOTO home](https://github.com/RobertasTa/foto-namai), [smart-duplicate-finder](https://github.com/RobertasTa/smart-duplicate-finder), [temp-cleaner](https://github.com/RobertasTa/temp-cleaner).
