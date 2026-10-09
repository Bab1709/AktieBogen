# Mine aktier

En lille hjemmeside, der kører lokalt på din Mac og holder styr på dine aktier. Kurserne hentes fra Yahoo Finance, så der skal ikke bruges nogen API-nøgle.

## Første gang

Kræver Python 3.10 eller nyere. Åbn Terminal i projektmappen og kør:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Start siden

```bash
.venv/bin/python main.py
```

Åbn derefter http://127.0.0.1:5001 i din browser. Stop siden igen med `Ctrl+C` i Terminal.

## Sådan bruger du den

- Skriv ticker-symbolet, som Yahoo Finance bruger det, fx `AAPL` eller `NOVO-B.CO` for danske aktier.
- Købskurs er valgfri. Lader du feltet stå tomt, bruges lukkekursen på købsdatoen, eller seneste lukkekurs før den, hvis datoen er en weekend eller helligdag.
- Beløb vises i aktiens egen valuta, som står i kolonnen "Valuta". Med knapperne "Aktiens valuta" og "DKK" over tabellen kan du skifte til at se alle beløb i danske kroner. Dit valg huskes i browseren.
- "Samlet værdi" er den nuværende værdi af alle dine aktier lagt sammen og vises altid i DKK.
- Omregning til DKK bruger dagens valutakurs fra Yahoo Finance, også for købskurs og udbytte. Gevinst/tab i DKK viser derfor ikke, hvad kronekursen har ændret sig siden købet.
- Kolonnen "Udbytte" viser, hvor meget du har fået i udbytte siden købsdatoen for dit antal aktier, før skat. Aktier uden udbytte viser 0,00.
- Har aktien haft et aktiesplit, siden du købte, så skriv det antal aktier, du har i dag, og købskursen omregnet til efter splittet. Den automatiske lukkekurs er allerede omregnet.

## Dine data

Dine aktier gemmes i `portfolio.json` i projektmappen. Filen står i `.gitignore`, så den bliver ikke lagt på GitHub.
