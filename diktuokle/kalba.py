# -*- coding: utf-8 -*-
"""kalba.py - sasajos kalbos sluoksnis (seimos sablonas is FOTO namu).

Lietuviskas tekstas = zodyno raktas; t() grazina vertima arba pati rakta.
Trukstamas vertimas NELUZTA - zmogus pamatys lietuviska eilute, ne klaida.

Skirtumas nuo FOTO namu: ten kalba gulejo atskirame `kalba.txt`, cia ji yra
`nustatymai.json` lauke `sasajos_kalba` kartu su visu kitu. Kad nebutu ciklinio
importo (kalba.py <- variklis <- faster_whisper), sis modulis nustatymu NESKAITO
pats - `diktuokle.py` po ju nuskaitymo kvieciam `kalba.nustatyk(...)`.

⚠️ KALBU VARDAI NEVERCIAMI. Mygtukuose stovi endonimai - "Lietuvių", "Русский",
"English" - t. y. kiekviena kalba vadinasi savo pacios kalba. Taip daro Windows
ir naršyklės, ir tai vienintelis budas, kuris veikia visose sasajose vienodai:
rusakalbis, netycia gaves lietuviska sasaja, vis tiek ras savo "Русский".
"""

KALBOS = ("lt", "ru", "en")

# Kalbu vardai mygtukuose - endonimai, tie patys visose sasajose (zr. auksciau).
KALBU_VARDAI = {"lt": "Lietuvių", "ru": "Русский", "en": "English"}

LANG = "lt"


def nustatyk(kodas):
    """Kvieciama VIENA karta, pries kuriant langa."""
    global LANG
    if kodas in KALBOS:
        LANG = kodas


def os_kalba():
    """Pirmam paleidimui, jei diegiant kalba nenurodyta: lietuviska Windows -> lt,
    rusiska -> ru, visos kitos -> en. LANGID & 0x3FF (FOTO namu receptas)."""
    try:
        import ctypes
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return {0x27: "lt", 0x19: "ru"}.get(langid & 0x3FF, "en")
    except Exception:
        pass
    try:
        import locale
        loc = (locale.getlocale()[0] or "").lower()
        for pre in ("lt", "ru"):
            if loc.startswith(pre):
                return pre
        return "en"
    except Exception:
        return "en"


_RU = {
    # --- Busenos eilute ---
    "Kraunu…": "Загрузка…",
    "Pasiruošęs": "Готово",
    "Klausau": "Слушаю",
    "Atpažįstu": "Распознаю",
    "Taip": "Да",
    "Ne": "Нет",
    # --- Dantratis ---
    # Roberto siulymas 2026-09-11 buvo "Разделение речи" - atmesta su priezastimi:
    # rusu gramatikoje "части речи" yra KALBOS DALYS (daiktavardis, veiksmazodis),
    # tad varnele skambetu apie gramatini skirstyma ar garso skaidyma, ne apie
    # kablelius. Bet jo nuojauta, kad "Пунктуация" per knygine, teisinga: Windows
    # rusiskoje versijoje ta pati funkcija vadinasi "автоматическая расстановка
    # знаков препинания" - imam ju zodi, kuri zmogus jau mate.
    "Skyryba ir didžiosios": "Знаки препинания и заглавные",
    "Visada viršuje": "Поверх других окон",
    "Rašyti derinimo žurnalą": "Вести журнал диагностики",
    "Žurnale saugoti ir tekstą": "Сохранять в журнале и текст",
    "Žurnalas: {}…": "Журнал: {}…",
    "Garsas ir tekstas lieka šiame kompiuteryje":
        "Звук и текст остаются на этом компьютере",
    "Žurnalas nerašomas": "Журнал не ведётся",
    # ⚠️ Pavarde palikta lotyniskai TYCIA: transliteruota "Кристийонас
    # Якубсонас" atrodo svetimai ir, svarbiau, su ja zmogus jo nerastu nei
    # GitHub'e, nei Hugging Face. Autoriu vardai neverciami.
    "Ausys: Paprika — Kristijonas Jakubsonas":
        "Распознавание: Paprika — Kristijonas Jakubsonas",
    "Ausys: bendrasis modelis (Paprika neįdiegta)":
        "Распознавание: общая модель (Paprika не установлена)",
    # --- Zurnalo teksto ijungimo klausimas ---
    "Nuo šiol į žurnalą bus įrašomas VISAS padiktuotas tekstas —\n"
    "viskas, ką pasakysite: laiškai, sveikatos reikalai, balsu\n"
    "ištartas slaptažodis.\n\n"
    "Failas lieka jūsų kompiuteryje ir niekur nesiunčiamas, bet\n"
    "prieš siųsdami jį kam nors pagalbos — perskaitykite, kas jame.\n\n"
    "Įjungti?":
        "Теперь в журнал будет записываться ВЕСЬ надиктованный текст —\n"
        "всё, что вы скажете: письма, вопросы здоровья, произнесённый\n"
        "вслух пароль.\n\n"
        "Файл остаётся на вашем компьютере и никуда не отправляется, но\n"
        "прежде чем послать его кому-то за помощью — прочитайте, что в нём.\n\n"
        "Включить?",
    # --- Modeliu parsisiuntimas (pirmas paleidimas) ---
    "Reikia parsisiųsti kalbos modelius": "Нужно загрузить языковые модели",
    "Siunčiu…": "Загружаю…",
    "Pasirinktoms kalboms trūksta modelių — reikės parsisiųsti\n"
    "apie {} GB.\n\n"
    "Tai vienkartinis veiksmas: po jo programa veiks be interneto,\n"
    "ir garsas niekur nebus siunčiamas.\n\n"
    "Parsisiųsti dabar?":
        "Для выбранных языков не хватает моделей — потребуется загрузить\n"
        "около {} ГБ.\n\n"
        "Это разовое действие: после него программа будет работать без\n"
        "интернета, и звук никуда не будет отправляться.\n\n"
        "Загрузить сейчас?",
    # --- CUDA (vaizdo ploksté) ---
    "Rasta NVIDIA vaizdo plokštė": "Найдена видеокарта NVIDIA",
    "Kompiuteryje yra NVIDIA vaizdo plokštė. Su ja atpažinimas vyksta\n"
    "maždaug dvidešimt kartų greičiau — 0,2 s vietoj 3 s.\n\n"
    "Tam reikia vieną kartą parsisiųsti apie {} GB bibliotekų.\n"
    "Be jų programa veiks, tik ant procesoriaus.\n\n"
    "Parsisiųsti dabar?":
        "В компьютере есть видеокарта NVIDIA. С ней распознавание идёт\n"
        "примерно в двадцать раз быстрее — 0,2 с вместо 3 с.\n\n"
        "Для этого нужно один раз загрузить около {} ГБ библиотек.\n"
        "Без них программа будет работать, но на процессоре.\n\n"
        "Загрузить сейчас?",
    # --- Zurnalo langas ---
    "Žurnalas — {}": "Журнал — {}",
    "(žurnalo dar nėra)": "(журнала пока нет)",
    "Rodyti failą": "Показать файл",
    "Uždaryti": "Закрыть",
    # --- "?" meniu ---
    "Pagalba": "Справка",
    "Apie...": "О программе...",
    "Instrukcija": "Инструкция",
    "Neradote atsakymo? Klauskite DI": "Не нашли ответа? Спросите ИИ",
    # --- Apie langas ---
    "Apie programą": "О программе",
    "Lietuviškas diktavimas be interneto —\n"
    "garsas niekur nesiunčiamas, viskas lieka kompiuteryje.":
        "Диктовка без интернета —\n"
        "звук никуда не отправляется, всё остаётся на компьютере.",
    "Versija {}": "Версия {}",
    "Sukurta naudojant DI: kodą rašė Claude, ikona — DI.\n"
    "Padiktuotas tekstas yra jūsų — DI jį tik užrašo.":
        "Создано с помощью ИИ: код писал Claude, иконка — ИИ.\n"
        "Надиктованный текст — ваш, ИИ его только записывает.",
    "Lietuviškos ausys — Paprika, Kristijonas Jakubsonas (CC BY 4.0)\n"
    "Skyryba — punct_restore, Kristijonas Jakubsonas (Apache 2.0)\n"
    "Variklis — faster-whisper (MIT)":
        "Литовское распознавание — Paprika, Kristijonas Jakubsonas (CC BY 4.0)\n"
        "Пунктуация — punct_restore, Kristijonas Jakubsonas (Apache 2.0)\n"
        "Движок — faster-whisper (MIT)",
    "Kūrėjo puslapis:": "Страница автора:",
    # --- Kiti pranesimai ---
    "Diktuoklė jau paleista — žiūrėk užduočių juostoje.":
        "Диктовалка уже запущена — смотрите на панели задач.",
    "Nepavyko atidaryti README: {}": "Не удалось открыть README: {}",
    "Atšaukti": "Отмена",
}

_EN = {
    # --- Busenos eilute ---
    "Kraunu…": "Loading…",
    "Pasiruošęs": "Ready",
    "Klausau": "Listening",
    "Atpažįstu": "Transcribing",
    "Taip": "Yes",
    "Ne": "No",
    # --- Dantratis ---
    "Skyryba ir didžiosios": "Punctuation and capitals",
    "Visada viršuje": "Always on top",
    "Rašyti derinimo žurnalą": "Write a diagnostic log",
    "Žurnale saugoti ir tekstą": "Also store the text in the log",
    "Žurnalas: {}…": "Log: {}…",
    "Garsas ir tekstas lieka šiame kompiuteryje":
        "Audio and text stay on this computer",
    "Žurnalas nerašomas": "No log is written",
    "Ausys: Paprika — Kristijonas Jakubsonas":
        "Recognition: Paprika — Kristijonas Jakubsonas",
    "Ausys: bendrasis modelis (Paprika neįdiegta)":
        "Recognition: general model (Paprika not installed)",
    # --- Zurnalo teksto ijungimo klausimas ---
    "Nuo šiol į žurnalą bus įrašomas VISAS padiktuotas tekstas —\n"
    "viskas, ką pasakysite: laiškai, sveikatos reikalai, balsu\n"
    "ištartas slaptažodis.\n\n"
    "Failas lieka jūsų kompiuteryje ir niekur nesiunčiamas, bet\n"
    "prieš siųsdami jį kam nors pagalbos — perskaitykite, kas jame.\n\n"
    "Įjungti?":
        "From now on the log will record ALL dictated text — everything\n"
        "you say: letters, health matters, a password spoken aloud.\n\n"
        "The file stays on your computer and is never sent anywhere, but\n"
        "before you send it to anyone for help — read what is in it.\n\n"
        "Turn on?",
    # --- Modeliu parsisiuntimas (pirmas paleidimas) ---
    "Reikia parsisiųsti kalbos modelius": "Language models need downloading",
    "Siunčiu…": "Downloading…",
    "Pasirinktoms kalboms trūksta modelių — reikės parsisiųsti\n"
    "apie {} GB.\n\n"
    "Tai vienkartinis veiksmas: po jo programa veiks be interneto,\n"
    "ir garsas niekur nebus siunčiamas.\n\n"
    "Parsisiųsti dabar?":
        "The selected languages are missing their models — about {} GB\n"
        "needs to be downloaded.\n\n"
        "This happens once: afterwards the program works without internet,\n"
        "and audio is never sent anywhere.\n\n"
        "Download now?",
    # --- CUDA (vaizdo ploksté) ---
    "Rasta NVIDIA vaizdo plokštė": "NVIDIA graphics card found",
    "Kompiuteryje yra NVIDIA vaizdo plokštė. Su ja atpažinimas vyksta\n"
    "maždaug dvidešimt kartų greičiau — 0,2 s vietoj 3 s.\n\n"
    "Tam reikia vieną kartą parsisiųsti apie {} GB bibliotekų.\n"
    "Be jų programa veiks, tik ant procesoriaus.\n\n"
    "Parsisiųsti dabar?":
        "This computer has an NVIDIA graphics card. With it, recognition runs\n"
        "about twenty times faster — 0.2 s instead of 3 s.\n\n"
        "That needs a one-time download of about {} GB of libraries.\n"
        "Without them the program still works, just on the CPU.\n\n"
        "Download now?",
    # --- Zurnalo langas ---
    "Žurnalas — {}": "Log — {}",
    "(žurnalo dar nėra)": "(no log yet)",
    "Rodyti failą": "Show file",
    "Uždaryti": "Close",
    # --- "?" meniu ---
    "Pagalba": "Help",
    "Apie...": "About...",
    "Instrukcija": "Instructions",
    "Neradote atsakymo? Klauskite DI": "No answer here? Ask an AI",
    # --- Apie langas ---
    "Apie programą": "About",
    "Lietuviškas diktavimas be interneto —\n"
    "garsas niekur nesiunčiamas, viskas lieka kompiuteryje.":
        "Offline voice dictation —\n"
        "audio is never sent anywhere, everything stays on your computer.",
    "Versija {}": "Version {}",
    "Sukurta naudojant DI: kodą rašė Claude, ikona — DI.\n"
    "Padiktuotas tekstas yra jūsų — DI jį tik užrašo.":
        "Made with AI: the code was written by Claude, the icon by AI.\n"
        "The dictated text is yours — the AI only writes it down.",
    "Lietuviškos ausys — Paprika, Kristijonas Jakubsonas (CC BY 4.0)\n"
    "Skyryba — punct_restore, Kristijonas Jakubsonas (Apache 2.0)\n"
    "Variklis — faster-whisper (MIT)":
        "Lithuanian recognition — Paprika, Kristijonas Jakubsonas (CC BY 4.0)\n"
        "Punctuation — punct_restore, Kristijonas Jakubsonas (Apache 2.0)\n"
        "Engine — faster-whisper (MIT)",
    "Kūrėjo puslapis:": "Author's page:",
    # --- Kiti pranesimai ---
    "Diktuoklė jau paleista — žiūrėk užduočių juostoje.":
        "Diktuoklė is already running — look in the taskbar.",
    "Nepavyko atidaryti README: {}": "Could not open README: {}",
    "Atšaukti": "Cancel",
}

_ZODYNAI = {"ru": _RU, "en": _EN}


def t(raktas):
    """LT rezime grazina rakta, kitur - vertima (arba rakta, jei vertimo nera)."""
    zod = _ZODYNAI.get(LANG)
    if zod is None:
        return raktas
    return zod.get(raktas, raktas)
