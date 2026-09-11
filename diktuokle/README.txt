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
  Lietuviska sneka atpazista PAPRIKA - Kristijono Jakubsono modelis,
  mokytas is LIEPA-3 garsyno. Skyryba ir didziasias deda jo paties
  punct_restore. Abu jis paskelbe ATVIRAI - todel si programa ir yra.
  Mes sudejom aplink jo darba langa, klavisus ir diegima. Aciu.


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
  Skyryba ir didziosios dedamos automatiskai. Taska sakinio gale
  sakyk pats - "taskas" - arba tiesiog tesk kita sakini.


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
  Ant procesoriaus - apie 3 s kiekvienam sakiniui, trumpam ar ilgam
  (Whisper visada apdoroja 30 s langa). Su NVIDIA vaizdo plokste -
  apie 0,15 s. Programa plokste aptinka pati ir pasiulo parsisiusti
  bibliotekas (~1,7 GB, viena karta).


NUSTATYMAI (krumpliaratis)
--------------------------
  Skyryba ir didziosios    - ijungti / isjungti.
  Visada virsuje           - langas neuzsidengia kitais.
  Rasyti derinimo zurnala  - ISJUNGTA. Ijungus rasomi tik techniniai
                             dalykai: irenginys, laikai, klaidos.
  Zurnale saugoti ir teksta - ISJUNGTA. Ijungus i faila kris VISKAS,
                             ka padiktuosi. Programa paklaus dar karta.

  Nustatymai isimenami. Meniu apacioje parasyta, kas klauso.


JEI KAS NE TAIP
---------------
  Ijunk derinimo zurnala (krumpliaratis) ir pakartok. Zurnalas guli
  %LOCALAPPDATA%\Diktuokle\diktuokle.log - meniu ji atidaro.
  Eilute [Paprika] arba [large-v3] rodo, kiek uztruko; jei modelis
  nepakilo - bus parasyta, kodel.

  Neradai atsakymo? "?" -> "Klauskite DI" atidaro pokalbi su asistentu,
  kuris jau bus gaves autoriaus instruktaza apie sia programa.


KAS VIDUJE
----------
  Lietuviskos ausys: Paprika (Kristijonas Jakubsonas, CC BY 4.0)
  Rusu ir anglu:     Whisper large-v3 (OpenAI, MIT)
  Skyryba:           punct_restore (Kristijonas Jakubsonas, Apache 2.0)
  Variklis:          faster-whisper (SYSTRAN, MIT)

  Kodas: https://github.com/RobertasTa/diktuokle

  A gift from Claude & Robertas
