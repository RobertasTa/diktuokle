# Diktuoklė 0.1 → 0.2: kaip matuota, kodėl pakeistos ausys

*Matuota 2026-10-25 viename kompiuteryje (Ryzen 9 9950X, RTX PRO 4500), tais pačiais garsais visiems modeliams.
Senoji pusė paleista **lygiai taip, kaip ją kviečia Diktuoklė 0.1** (beam 5, VAD, ta pati `initial_prompt`), naujoji — kaip 0.2
(onnx-asr 0.12, int8). „Procesorius" — 4 gijos, kad būtų arčiau eilinio kompiuterio. Įrašų čia nėra: autoriaus balso komandos
lieka jo kompiuteryje, skelbiami tik suvestiniai skaičiai.*

WER — žodžių klaidos, CER — raidžių. Prieš skaičiuojant etalonas ir atpažintas tekstas suvienodinami: mažosios, be skyrybos,
skaičiai žodžiais (kad „20" ir „dvidešimt" nebūtų klaida).

## Lietuvių: LT_ausys prieš Paprika

| Rinkinys | LT_ausys · CPU | Paprika · CPU | Paprika · GPU (kaip 0.1) |
|---|---|---|---|
| autoriaus komandos per mikrofoną, 127 | **17,85 %** · 0,05 s | 22,80 % · 3,01 s | 23,23 % · 0,11 s |
| FLEURS lt skaitymas, 300 | **9,38 %** · 0,15 s | 9,49 % · 4,68 s | 9,51 % · 0,22 s |
| ilgi gabalai (4 FLEURS sakiniai iš eilės, ~45 s), 40 | **10,20 %** · 1,04 s | 32,37 % · 15,31 s | 31,81 % · 1,46 s |

Laikas — vidurkis vienam įrašui. Ilguose gabaluose Paprika 3 iš 40 kartų (procesoriuje — 2) atpažino mažiau nei 80 % žodžių —
numetė pabaigą; LT_ausys — 0 iš 40. Visas FLEURS lt (986 sakiniai, be Paprikos CPU): LT_ausys 9,75 %, Paprika GPU 9,81 %.

**Skyryba.** 0.1 lietuviškai turėjo atskirą skyrybos modelį (`punct_restore` + xlm-roberta, 1,1 GB), nes Paprika rašo be
ženklų. LT_ausys ženklus deda pati. Tikrinta FLEURS lt su originalia skyryba (986 sakiniai; lyginami tik sutapę žodžiai):

| Variantas | kablelis P | R | F1 | sakinio galas F1 |
|---|---|---|---|---|
| LT_ausys pati | 79,3 % | 93,0 % | **85,6 %** | 93,1 % |
| LT_ausys + skyrybos modelis | 81,5 % | 91,6 % | 86,3 % | — * |
| Paprika + skyrybos modelis (0.1) | 80,9 % | 91,1 % | 85,7 % | — * |

\* 0.1 taško gale tyčia nededa (autoriaus taisyklė — diktuojant dalimis jis atsidurtų vidury minties); 0.2 tą taisyklę palieka.
Skyrybos modelis LT_ausys pridėtų 0,7 punkto — ne verta 1,1 GB parsisiuntimo ir 0,5 GB torch pakete.

## Rusų: GigaAM v3 prieš Whisper large-v3

FLEURS ru test, 775 įrašai. Skaičiai prieš lyginant verčiami žodžiais (num2words, vardininkas abiem pusėm), ё → е.

| | WER | CER | sekundės / įrašą |
|---|---|---|---|
| GigaAM v3 e2e int8 · CPU | 4,56 % | 1,51 % | **0,15** |
| large-v3 · GPU (kaip 0.1) | **3,92 %** | 1,29 % | 0,56 |
| be skaitmenų (610 įrašų): GigaAM / large-v3 | 3,26 % / **2,97 %** | | |
| pirmi 40, procesoriuje: GigaAM / large-v3 | **1,97 %** / 2,95 % | | **0,11** / 7,23 |

large-v3 rusiškai truputį tikslesnis. Bet be vaizdo plokštės jis sakiniui galvoja ~7 s, o GigaAM — dešimtąją sekundės dalį;
parsisiųsti 0,23 GB vietoj 3,1 GB. Dauguma kompiuterių NVIDIA neturi, todėl 0.2 rusų kalbai ima GigaAM.

## Ilgi įrašai ir tyla — du bandymai, kurie galėjo ir nepavykti

**Karpymas pauzėse** (gabalai ≤ 20 s, kerpama tylos viduryje, Silero VAD):

| Įrašas | be karpymo | su karpymu |
|---|---|---|
| GigaAM, 134 s (FLEURS ru sakiniai iš eilės) | WER 60,0 %, atpažinta 102 iš 209 žodžių | **WER 5,2 %**, 207 iš 209 |
| LT_ausys, 115 s | WER 12,7 %, 7,2 s | **WER 10,7 %, 2,2 s** |
| LT_ausys, 278 s | WER 16,7 %, 24,5 s | **WER 16,3 %, 4,5 s** |

**Tyla.** 500 tylos / triukšmo klipų: be VAD LT_ausys prirašė 6 310 simbolių, su VAD — 101 (485 klipai liko tušti).
Bet apkarpyti kalbos kraštus trumpiems įrašams buvo blogiau (komandų WER 16,77 → 17,42 %), todėl 0.2 VAD naudoja tik
dviem dalykams: ar kalbos išvis buvo, ir kur kirpti ilgesnius nei 20 s įrašus. Trumpas įrašas su kalba atpažįstamas visas.

*Šie du bandymai paleisti Diktuoklės surinkimo aplinkoje (onnxruntime 1.24.4, kaip pakete). Int8 skaičiavimai joje truputį
kitokie nei 1.31, kuria matuota pirmoji lentelė, todėl komandų WER čia 16,77 %, o ne 17,85 %.*

## Ko tai neįrodo

- Tai ne „geriausias lietuvių modelis" — lyginta tik su tuo, ką naudojo 0.1. Komercinių atpažintuvų nelyginom.
- Autoriaus komandos — vieno žmogaus balsas, vienas mikrofonas, namų komandos. Kitam balsui skaičiai bus kiti; kryptis — greičiausiai ta pati.
- FLEURS yra skaitymas, ne diktavimas. Jis geras palyginti modelius tarpusavyje, ne pažadėti tikslumą.
