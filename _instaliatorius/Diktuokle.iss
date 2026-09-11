; Diktuokle - Inno Setup instaliatorius su KALBU VARNELEMIS.
; Statyti:  ISCC.exe Diktuokle.iss   (leisti is sio katalogo)
;
; ROBERTO IDEJA (2026-09-11), del kurios sis skriptas apskritai toks:
;   "Kiekvienas zmogus yra individualus: vienam gali reiketi tik lietuviu,
;    kitam lietuviu ir anglu. Siulau instaliatoriu, kuriame issoka lentele ir
;    gali pasizymeti."
; Ka tai duoda, pamatuota: tik lietuviu - 1,9 GB, rusu+anglu - 3,1 GB (tas pats
; failas abiem!), visos trys - 5,0 GB. Be varneliu VISIEMS butu 5,0 GB.
;
; SPRENDIMAI:
;  - ONEDIR (seimos sprendimas 15). onefile kaskart isspakuotu 830 MB i temp.
;  - PrivilegesRequired=lowest -> i vartotojo profili, JOKIO UAC lango.
;  - MODELIU CIA NERA. Jie sveria gigabaitus ir parsisiunciami PIRMO PALEIDIMO
;    metu - programa pati paklausia ir parodo, kiek reikes. Inno Setup dideliems
;    parsisiuntimams netinka: nutrukus rysiui ties 700-uoju megabaitu zlugtu
;    visas diegimas. Varneles cia daro viena dalyka - irasо i nustatymai.json,
;    kuriu kalbu zmogus nori.
;  - AppId GUID FIKSUOTAS - NIEKADA nekeisti (kitaip senos versijos liks).

; ⚠️ DU VARDAI, ir tai TYCIA (2026-09-11, Roberto testas parode klaida):
;   AppName    - RODOMAS zmogui, todel su lietuviska raide: "Diktuoklė".
;   AppFailams - KATALOGU ir FAILU varduose, be diakritikos: "Diktuokle".
; Priezastis ta pati, del kurios zurnalo failas vadinasi be lietuvisku raidziu:
; FAT32 flesiukas, svetima koduote ar sena programa is tokio kelio gali
; nebeatrasti failu. Rodomas tekstas ir failo vardas yra du skirtingi dalykai.
#define AppName      "Diktuoklė"
#define AppFailams   "Diktuokle"
#define AppVersion   "0.1"
#define AppExeName   "Diktuokle.exe"
#define AppUrl       "https://github.com/RobertasTa/diktuokle"

[Setup]
AppId={{7B3C1D90-5E2A-4F18-9C64-2D8A1F0B7E35}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Robertas & Claude (AI)
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
DefaultDirName={autopf}\{#AppFailams}
DefaultGroupName={#AppFailams}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename={#AppFailams}-{#AppVersion}-setup
SetupIconFile=..\diktuokle\Diktuokle.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
; ⚠️ SEIMOS PAMOKA (FOTO namai, 2026-08-30 Roberto gyvas testas): instaliatoriaus
; kalbos turi ATITIKTI programos kalbas. Tada buvau idejes rusu kalba programai,
; kuri rusiskai nemokejo - rusas butu pasirinkes rusiska diegima ir gaves
; nesuprantama programa. Diktuokle moka LT/RU/EN, tad cia visos trys.
;
; ⭐ LIETUVIU KALBOS INNO SETUP NETURI - nei pagrindiniame rinkinyje, nei
; neoficialiame (38 kalbos; patikrinta 2026-09-11 per jrsoftware/issrc API).
; Roberto klausimas "kur lietuviu kalba?" (2026-09-11), sustabdes pirmaji
; diegima, buvo teisingas: lietuviska dovana, kurios diegimas nekalba
; lietuviskai, yra puse dovanos. Todel `Lithuanian.isl` PARASYTAS MUSU - visi
; 296 pranesimai, salia sio failo. LIETUVIU PIRMA, nes tai lietuviska dovana.
Name: "lt"; MessagesFile: "Lithuanian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
lt.KalbuPuslapis=Diktavimo kalbos
lt.KalbuAprasas=Kokiomis kalbomis norite diktuoti?
lt.KalbuPaaiskinimas=Pažymėkite tik tai, ko jums reikia. Kiekvienai kalbai reikia savo modelio; jis parsisiunčiamas vieną kartą, pirmą kartą paleidus programą:%n%n    Lietuvių ~1,9 GB    Rusų arba anglų ~3,1 GB%n%nRusų ir anglų kalbos naudoja tą patį modelį, tad pasirinkus abi nieko papildomai nesiunčiama. Galima pasirinkti daugiausia dvi kalbas. Pirmoji pažymėta nustato ir pačios programos kalbą.
lt.KalbaLT=Lietuvių (Paprika – lietuvių kalbai pritaikytas modelis)
lt.KalbaRU=Rusų
lt.KalbaEN=Anglų
lt.NieckoNepazymeta=Pažymėkite bent vieną kalbą.
lt.PerDaugKalbu=Galima pasirinkti daugiausia dvi kalbas. Nuimkite vieną varnelę.
en.KalbuPuslapis=Dictation languages
en.KalbuAprasas=Which languages do you want to dictate in?
en.KalbuPaaiskinimas=Pick only what you need. Each language needs its own model, downloaded once on first run:%n%n    Lithuanian ~1.9 GB    Russian or English ~3.1 GB%n%nRussian and English share the same model, so picking both costs nothing extra. You can pick at most two. The first language you tick also sets the program's own language.
en.KalbaLT=Lithuanian (Paprika - a model fine-tuned for Lithuanian)
en.KalbaRU=Russian
en.KalbaEN=English
en.NieckoNepazymeta=Please tick at least one language.
en.PerDaugKalbu=You can pick at most two languages. Please untick one.
ru.KalbuPuslapis=Языки диктовки
ru.KalbuAprasas=На каких языках вы хотите диктовать?
ru.KalbuPaaiskinimas=Отметьте только то, что нужно. Для каждого языка нужна своя модель, она загружается один раз при первом запуске:%n%n    Литовский ~1,9 ГБ    Русский или английский ~3,1 ГБ%n%nРусский и английский используют одну модель, поэтому выбрать оба ничего не стоит дополнительно. Можно выбрать не более двух языков. Первый отмеченный задаёт и язык самой программы.
ru.KalbaLT=Литовский (Paprika - модель, дообученная для литовского)
ru.KalbaRU=Русский
ru.KalbaEN=Английский
ru.NieckoNepazymeta=Отметьте хотя бы один язык.
ru.PerDaugKalbu=Можно выбрать не более двух языков. Снимите одну галочку.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Diktuokle\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  KalbuPuslapis: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  // Atskiras puslapis, ne [Components]: komponentai Inno Setup'e susieti su
  // FAILAIS, o mums kalbos nieko nekeicia pakete - jos keicia tik nustatymus.
  KalbuPuslapis := CreateInputOptionPage(wpSelectTasks,
    ExpandConstant('{cm:KalbuPuslapis}'),
    ExpandConstant('{cm:KalbuAprasas}'),
    ExpandConstant('{cm:KalbuPaaiskinimas}'),
    False, False);   // varneles (ne radijo mygtukai), be "pazymeti viska"
  KalbuPuslapis.Add(ExpandConstant('{cm:KalbaLT}'));
  KalbuPuslapis.Add(ExpandConstant('{cm:KalbaRU}'));
  KalbuPuslapis.Add(ExpandConstant('{cm:KalbaEN}'));

  // Numatytoji varnele pagal DIEGIMO kalba: kas diegia rusiskai, greiciausiai
  // nori diktuoti rusiskai; kas angliskai - angliskai. Lietuviu - numatytoji
  // visais kitais atvejais, nes tai lietuviska dovana.
  if ActiveLanguage = 'ru' then
    KalbuPuslapis.Values[1] := True
  else if ActiveLanguage = 'en' then
    KalbuPuslapis.Values[2] := True
  else
    KalbuPuslapis.Values[0] := True;
end;

function KiekPazymeta: Integer;
var
  i: Integer;
begin
  Result := 0;
  for i := 0 to 2 do
    if KalbuPuslapis.Values[i] then
      Result := Result + 1;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = KalbuPuslapis.ID then
  begin
    // Be nė vienos kalbos programa neturetu nė vieno mygtuko - neleidziam eiti
    // toliau, o ne taisom tyliai uz zmogaus nugaros.
    if KiekPazymeta = 0 then
    begin
      MsgBox(ExpandConstant('{cm:NieckoNepazymeta}'), mbError, MB_OK);
      Result := False;
    end
    // ⛔ DAUGIAUSIA DVI (Roberto sprendimas 2026-09-11: "nededam galimybes
    // tureti GUI 3 ju kalbu, tik dvi arba viena, jokios trecios"). Technine
    // galimybe yra - trecia kalba nekainuoja nė megabaito, nes rusu ir anglu
    // dalijasi tuo paciu modeliu, o langas paplatetu nuo 454 iki 581 px. Bet
    // sprendimas del lango yra jo, ne mano: dovana turi atrodyti taip, kaip
    // autorius nori, o ne taip, kaip leidzia technika.
    else if KiekPazymeta > 2 then
    begin
      MsgBox(ExpandConstant('{cm:PerDaugKalbu}'), mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure RasykNustatymus;
var
  Katalogas, Failas, Kalbos, Pirma: String;
begin
  // Rasom TA PATI nustatymai.json, kuri skaito programa. Tvarka fiksuota
  // LT -> RU -> EN; PIRMA pazymeta kalba duoda ir sasajos kalba (Roberto
  // taisykle 2026-09-11).
  Kalbos := '';
  Pirma := '';
  if KalbuPuslapis.Values[0] then begin Kalbos := '"lt"'; Pirma := 'lt'; end;
  if KalbuPuslapis.Values[1] then
  begin
    if Kalbos <> '' then Kalbos := Kalbos + ', ';
    Kalbos := Kalbos + '"ru"';
    if Pirma = '' then Pirma := 'ru';
  end;
  if KalbuPuslapis.Values[2] then
  begin
    if Kalbos <> '' then Kalbos := Kalbos + ', ';
    Kalbos := Kalbos + '"en"';
    if Pirma = '' then Pirma := 'en';
  end;

  Katalogas := ExpandConstant('{localappdata}\Diktuokle');
  if not DirExists(Katalogas) then
    ForceDirectories(Katalogas);
  Failas := Katalogas + '\nustatymai.json';

  // KALBOS - VISADA i atskira faila, kuri programa paleidziant isiurbia ir
  // istrina. Roberto testas 2026-09-11: perdieges su VIENA kalba gavo DVI, nes
  // nustatymai.json jau buvo, o as jo "neliečiau". Dabar kalbu pasirinkimas
  // is diegimo laimi visada, o kiti laukai (skyryba, virsuje, zurnalas) lieka.
  SaveStringToFile(Katalogas + '\diegimo_kalbos.json',
    '{"kalbos": [' + Kalbos + '], "sasajos_kalba": "' + Pirma + '"}' + #13#10,
    False);

  // Pilnas nustatymu failas - tik jei jo dar nera (pirmas diegimas).
  if not FileExists(Failas) then
    SaveStringToFile(Failas,
      '{' + #13#10 +
      '  "kalbos": [' + Kalbos + '],' + #13#10 +
      '  "kalba": "' + Pirma + '",' + #13#10 +
      '  "sasajos_kalba": "' + Pirma + '",' + #13#10 +
      '  "skyryba": true,' + #13#10 +
      '  "virsuje": true,' + #13#10 +
      '  "zurnalas": false,' + #13#10 +
      '  "zurnale_tekstas": false' + #13#10 +
      '}' + #13#10, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    RasykNustatymus;
end;

// PASTABA salinant programa: %LOCALAPPDATA%\Diktuokle NETRINAMAS. Ten guli
// nustatymai ir - jei zmogus pats isijunge - zurnalas, o svarbiausia, kelis
// gigabaitus sverianti modeliu kopija. Istrynus ja, perdiegus tektu siustis
// is naujo. ([Code] sekcijoje komentaras yra "//", ne ";" - Pascal, ne Inno.)
