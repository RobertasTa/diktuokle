DIKTUOKLE - lietuviskas diktavimas balsu be interneto
=====================================================

  Rasyk teksta balsu lietuviskai bet kurioje Windows programoje: kalbos
  atpazinimas veikia tavo kompiuteryje, nemokamai, garsas niekur
  nesiunciamas.
  Lithuanian offline speech-to-text dictation for Windows.

  Sukurta naudojant DI: programos koda rase Claude (Anthropic) kartu su
  Robertu; ikona sukurta naudojant DI. Tekstas, kuri padiktuoji, yra
  TAVO - DI ji tik uzraso.

  Vardas: "diktuoti -> diktuokle", kaip "skaiciuoti -> skaiciuokle" -
  irankis, kuriuo diktuojama.

Kalbi - tekstas atsiranda ten, kur mirksi zymeklis. Bet kurioje programoje.


AUSYS - KRISTIJONO JAKUBSONO
----------------------------
  Lietuviska sneka atpazista LT_AUSYS - Kristijono Jakubsono modelis
  "kmynas" (mokytas is LIEPA-3 garsyno), musu paverstas ONNX formatu,
  kad suktusi procesoriuje. Skyryba ir didziasias jis deda pats.
  Kristijonas savo darba paskelbe ATVIRAI - todel si programa ir yra.
  Mes sudejom aplink ji langa, klavisus ir diegima. Aciu.

  Iki versijos 0.2 cia dirbo jo Paprika. LT_ausys klysta reciau (musu
  matavimu komandoms 17,9 % zodziu pries 23,2 %), ilgo diktavimo
  nebenukerpa ir procesoriuje veikia greiciau, nei Paprika veike su
  vaizdo plokste.

  Rusiska sneka atpazista GigaAM v3 (SberDevices) - irgi procesoriuje.


DIKTAVIMAS
----------
  Laikyk DESINI Ctrl ir kalbek. Paleidai - tekstas irasomas.
  Lange banga rodo, kad mikrofonas tikrai girdi.
  Kalbek ta kalba, kurios mygtukas melynas - kitaip gausi nesamone.


LAIKANT DESINI Ctrl
-------------------
  <-  (rodykle kairen)   ABC / 123  - zodziai arba skaitmenys
  ->  (rodykle desinen)  kita kalba (tarp idiegtu)

  Perjungus kalbeti galima toliau, pirsto nuo Ctrl nekeliant.
  Perjungimas galioja VISAM tam gabalui, kuri diktuoji laikydamas Ctrl.

  2x desinys Shift - taip pat ABC / 123.


REZIMAS ABC (zodziai)
---------------------
  Skaiciai rasomi zodziais, kaip pasakyti: "dvidesimt penki".
  Skyryba ir didziosios dedamos automatiskai. Tasko pacioje gale
  programa nededa - diktuojant dalimis jis atsidurtu vidury minties.
  Kelis sakinius is eiles skiria pati.


REZIMAS 123 (skaitmenys) - lietuviu ir rusu kalboms
---------------------------------------------------
  Skaiciai virsta skaitmenimis:
    "vienas nulis nulis nulis"       -> 1000   (po viena skaitmeni)
    "simtas dvidesimt penki"         -> 125    (sudetiniai)
    "du tukstanciai dvidesimt penki" -> 2025
    "penkiu lentu po astuoniolika milimetru" -> 5 lentu po 18 milimetru

  Galima sakyti ir zenklus:
    taskas   kablelis   bruksnys   pliusas   lygu   procentas

  Anglu kalbai mygtukas 123 neaktyvus - modelis angliskus skaicius
  ir taip raso skaitmenimis.


GREITIS
-------
  Lietuviu ir rusu kalbos - procesoriuje, vaizdo plokstes nereikia:
  komandai apie 0,1 s, minutei diktavimo - 1-3 s (pagal procesoriu).
  Ilgas irasas pats sukarpomas pauzese.

  Anglu kalba (Whisper large-v3) procesoriuje leta - apie 3-7 s
  sakiniui. Su NVIDIA vaizdo plokste - apie 0,15 s. Jei pasirinkta
  anglu kalba, programa plokste aptinka pati ir pasiulo parsisiusti
  bibliotekas (~1,7 GB, viena karta).


NUSTATYMAI (krumpliaratis)
--------------------------
  Skyryba ir didziosios    - ijungti / isjungti.
  Visada virsuje           - langas neuzsidengia kitais.
  Mikrofonas               - kuri klausyti. Numatytasis - Windows; jei
                             Windows ji pats perjungia (nauja USB kolonele,
                             ausines), pasirink savaji - programa jo laikysis.
  Rasyti derinimo zurnala  - ISJUNGTA. Ijungus rasomi tik techniniai
                             dalykai: irenginys, laikai, klaidos.
  Zurnale saugoti ir teksta - ISJUNGTA. Ijungus i faila kris VISKAS,
                             ka padiktuosi. Programa paklaus dar karta.

  Nustatymai isimenami. Meniu apacioje parasyta, kas klauso.


JEI KAS NE TAIP
---------------
  Ijunk derinimo zurnala (krumpliaratis) ir pakartok. Zurnalas guli
  %LOCALAPPDATA%\Diktuokle\diktuokle.log - meniu ji atidaro.
  Eilute [lt_ausys], [gigaam] arba [large-v3] rodo, kiek uztruko; jei
  modelis nepakilo - bus parasyta, kodel. Busenoje "Modelio nera" -
  tos kalbos modelis neparsisiuste: paleisk programa is naujo, ji
  pasiulys parsisiusti.

  Neradai atsakymo? "?" -> "Klauskite DI" atidaro pokalbi su asistentu,
  kuris jau bus gaves autoriaus instruktaza apie sia programa.


KAS VIDUJE
----------
  Lietuviskos ausys: LT_ausys - kmynas v4 (Kristijonas Jakubsonas,
                     CC BY 4.0), huggingface.co/RobertasTa/lt-ausys
  Rusu:              GigaAM v3 (SberDevices, MIT)
  Anglu:             Whisper large-v3 (OpenAI, MIT)
  Varikliai:         onnx-asr (MIT), faster-whisper (SYSTRAN, MIT)

  Kodas: https://github.com/RobertasTa/diktuokle

  A gift from Claude & Robertas
