# XML pretvornik za Visual Studio

Namizna Python aplikacija za Windows: REK-1b XML → REK-O XML.
Datoteke se obdelujejo lokalno. Izberi vhod, klikni **Pretvori**, nato **Shrani kot**.
Izvorna datoteka ostane ohranjena. Pretvorba poteka v ozadju.

## Visual Studio 2022

1. V Visual Studio Installer namesti **Python development** in Python 3.10 ali novejši s podporo za Tcl/Tk.
2. Odpri `XmlConverter.sln`.
3. V **Python Environments** izberi ali ustvari okolje Python.
4. V terminalu tega okolja, v mapi projekta, zaženi `python -m pip install -r requirements.txt`.
5. Zaženi projekt s **Ctrl+F5**. Začetna datoteka je `main.py`.

Tudi iz terminala: `python main.py`.
Če uporabljaš Visual Studio Code, odpri mapo, izberi Python interpreter, namesti odvisnosti in zaženi `main.py`.

## Pravila pretvorbe

Zneski se prenesejo neposredno iz REK-1b brez seštevanja in brez privzetih ničel:

- A081O/P do A086O/P → istoimenska polja v REK-O, samo če obstajajo v vhodu.
- A086O in A086P se nikoli ne izračunata na novo.
- A081SZ in A082SZ sta pavšala; nista vir za obračunane zneske ali zneske za plačilo.
- Zastavici SF določata način vnosa starega obrazca; ne pomenita oprostitve prispevka.
- Zbirna polja F401..F405 → F301..F305: R → R, O → O, Z (za plačilo) → P.
- Računi in sklici se prenesejo iz zbirnega dela; fiksnih računov ni več.
- Manjkajoča polja ostanejo izpuščena. O se ne kopira samodejno v P.
- Izvorni A...P je v stari shemi označen kot plačani znesek; prenese se nespremenjeno,
  vendar pretvorba ne določa nove obveznosti za plačilo v REK-O. Če ta ni enaka zgodovinsko
  plačanemu znesku, je pred oddajo potreben vsebinski pregled.

Primer: vhodni A081SZ=4.87, A082SZ=7.72, A082O=7.72 in A086O=7.72
ustvari samo A082O=7.72 in A086O=7.72. A081O/P, A082P in A086P se ne ustvarijo.

Preslikava osebnih podatkov in glave ostane kot prej: A003i → A003, A003p → A003a,
DocumentType O in F010 1096. Konverter je namenjen obstoječi pretvorbi REK-1b,
ne poljubnim vrstam starih REK obrazcev.

Referenčni shemi:
https://edavki.durs.si/Documents/Schemas/PODO-Common-1.xsd
https://edavki.durs.si/Documents/Schemas/REK_1b_2.xsd

Aplikacija ne preverja veljavnosti po uradni XSD shemi in ne oddaja dokumentov v eDavke.
Zavrne pokvarjen XML, DTD, neustrezno strukturo, manjkajoča obvezna osebna polja,
prazen seznam postavk in neveljavne prenesene zneske. Zunanji XML viri se ne nalagajo.

## Preverjanje

`python -m unittest discover -s tests -v`

## Samostojni EXE (na Windows)

V istem Python okolju:

```
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name XmlConverter main.py
```

Rezultat je `dist/XmlConverter.exe`. Gradnjo EXE izvedi na Windows.

## Windows CMD brez grafičnega vmesnika

V isto mapo shrani `konvi.py` in `converter.py`. Potrebuješ Python 3.10 ali novejši.
Odpri CMD v mapi projekta in enkrat namesti odvisnosti:

```bat
python -m pip install -r requirements.txt
```

Zagon (imena s presledki daj v narekovaje):

```bat
python konvi.py "reki (3).xml"
```

Rezultat: `reki (3)_REK_O.xml` v isti mapi kot vhodna datoteka.
Izhodno ime lahko določiš tudi sam:

```bat
python konvi.py "C:\Podatki\reki (3).xml" "C:\Podatki\pretvorjeno.xml"
```

Ukaz ne prepisuje obstoječih datotek. Če izhod že obstaja, izberi drugo ime.
Pomoč: `python konvi.py --help`. Vrnjena koda je 0 ob uspehu, 1 ob napaki
pretvorbe ali shranjevanja in 2 ob napačnih argumentih.
Uporablja isto pretvorbo kot namizna aplikacija; zneskov ne sešteva.
