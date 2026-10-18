# Westminster source data

For character skills, traits, ideology and DNA bindings, edit [`character_overrides.json`](character_overrides.json).
The [modding guide](../../docs/modding.md) has examples and regeneration commands. Do not edit snapshot outputs as inputs.

Downloaded data goes in `raw/` (not in git). Re-download with the commands below.

## Constituency boundaries (2024)

- **Dataset:** "Westminster Parliamentary Constituencies (July 2024) Boundaries UK BGC" (generalised to 20 m,
  clipped to the coastline), all 650 seats, in British National Grid metres.
- **Source:** ONS Open Geography Portal.
- **Licence:** Open Government Licence v3.0. Attribution: "Source: Office for National Statistics licensed under the
  Open Government Licence v.3.0. Contains OS data © Crown copyright and database right 2024."

```sh
U="https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Westminster_Parliamentary_Constituencies_July_2024_Boundaries_UK_BGC/FeatureServer/0/query"
for off in 0 200 400 600; do
  curl -s -o westminster/data/raw/pcon24_$off.geojson \
    "$U?where=1%3D1&outFields=PCON24CD,PCON24NM&outSR=27700&f=geojson&resultOffset=$off&resultRecordCount=200&orderByFields=PCON24CD"
done
```

The map is then built with `.venv/bin/python westminster/tools/map/build_map.py` (Python packages: the repo's
`requirements.txt`).

## ITL2 areas (the duchies)

"International Territorial Level 2 (January 2025) Boundaries UK BGC", ONS, Open Government Licence v3.0.

```sh
curl -s -o westminster/data/raw/itl2_2025.geojson "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/ITL2_JAN_2025_UK_BGC/FeatureServer/0/query?where=1%3D1&outFields=ITL225CD,ITL225NM&outSR=27700&f=geojson"
```

## Towns (the baronies)

GeoNames `cities1000` (places of 1,000+ people), CC BY 4.0, "GeoNames (geonames.org)". Unzipped into `raw/geonames/`.

```sh
curl -L -o westminster/data/raw/cities1000.zip https://download.geonames.org/export/dump/cities1000.zip
(cd westminster/data/raw && mkdir -p geonames && unzip -o -q cities1000.zip -d geonames)
```

## Neighbouring land (scenery)

Natural Earth 1:10m admin-0 countries, public domain.

```sh
curl -L -o westminster/data/raw/ne_10m_admin_0_countries.zip https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip
```

## Elevation

Copernicus DEM GLO-90 (90 m), from the AWS open data bucket. Licence: "© DLR e.V. 2010-2014 and © Airbus
Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
(free use with that attribution). The 1° tiles for latitudes 49-60 and longitudes 11°W-2°E go in `raw/dem/`;
sea-only tiles don't exist, so 104 of the 168 download.

```sh
cd westminster/data/raw && mkdir -p dem && cd dem
for lat in $(seq 49 60); do for lon in $(seq -11 2); do
  if [ $lon -lt 0 ]; then L=$(printf "W%03d" $((-lon))); else L=$(printf "E%03d" $lon); fi
  n="Copernicus_DSM_COG_30_N${lat}_00_${L}_00_DEM"
  curl -s -f -o $n.tif "https://copernicus-dem-90m.s3.amazonaws.com/$n/$n.tif" || true
done; done
```

Python packages for the map build: numpy, pillow, shapely, pyproj, scipy, pyshp, tifffile, imagecodecs (all in the
repo's `requirements.txt`).

## The 2024 Parliament (the 2024 bookmark)

`tools/data/build_2024.py` downloads these into `raw/` once (`--refresh` downloads again) and generates the
bookmark's characters, dynasties, title history, party titles, bookmark and localization (the outputs are listed in
the script's docstring). It takes well under a second once the downloads are cached.

```sh
.venv/bin/python westminster/tools/data/build_2024.py
```

| File in `raw/` | What | Source | Licence |
|---|---|---|---|
| `ge2024_candidacies.csv` | Every candidacy at the 4 July 2024 general election: constituency and ONS code (PCON24CD), candidate, MNIS member id, party, votes, share, majority, result position | UK Parliament election results, <https://electionresults.parliament.uk/general-elections/6/candidacies.csv> (House of Commons Library) | Open Parliament Licence v3.0 |
| `pcon24_names.json` | PCON24CD to PCON24NM, the names the map's `c_` titles were made from | ONS Open Geography Portal (the boundary service above, `returnGeometry=false`) | Open Government Licence v3.0 |
| `members_api_2024.json` | Each winner's Members API record (gender, display name) | UK Parliament Members API, `https://members-api.parliament.uk/api/Members/{id}` | Open Parliament Licence v3.0 |
| `wikidata_mps_2024.json` | Date of birth (P569, with its precision) and sex (P21), looked up by parliament.uk member id (P10428) | Wikidata SPARQL, <https://query.wikidata.org/> | CC0 |

Attribution for UK Parliament data: "Contains Parliamentary information licensed under the Open Parliament Licence
v3.0." The dates of birth of the four bookmark characters who aren't MPs (Mary Lou McDonald, John Swinney, Michelle
O'Neill, Vaughan Gething) are written into the script, also from Wikidata.

How the data is used:

- Seats are matched by ONS code: PCON24CD gives the ONS name, and `key(name)` (as in `tools/map/geo.py`) gives the
  county title. All 650 match.
- Birth dates: to the day where Wikidata has it; Wikidata's month or year where that's all it has (the missing day or
  month comes from a stable hash of the seat); about 50 years old on polling day where Wikidata has no date (85 MPs).
- Gender comes from the Members API.
- `data/ge2024_results.csv` (in git, derived from the candidacies under the Open Parliament Licence) has each seat's
  ONS code, title, electorate, turnout, winner, majority and vote shares (Lab, Con, LD, RUK, Green, SNP, PC, SF,
  DUP, SDLP, APNI, UUP, TUV, independents, the Speaker, others). `tools/data/build_seat_leans.py` turns it into the
  election and poll script (each seat's lean, national shares).

### MPs' spouses (fictional) and likenesses

`tools/data/build_spouses.py` (called by `build_2024.py`) invents spouses; these two files only keep it from giving
an MP their real spouse's name, or an opposite-sex spouse to an openly LGBT+ MP:

| File in `raw/` | What | Source | Licence |
|---|---|---|---|
| `wikidata_mps_2024_family.json` | Spouse (P26) name and sex, sexual orientation (P91), by parliament.uk member id | Wikidata SPARQL | CC0 |
| `wikipedia_lgbtq_uk_politicians.json` | Wikitext of "List of LGBTQ politicians in the United Kingdom" (names only are used) | Wikipedia API | CC BY-SA 4.0 |

`tools/data/build_likenesses.py` (fixed portraits) uses no downloaded data: appearances are described by hand in it.

### MPs' ideologies (caucus lists)

`build_2024.py` gives an MP their own ideology only where it is obvious from public record: membership of a
self-declared caucus, read from the member lists of these Wikipedia articles (MediaWiki API, `action=parse`, cached
once; `--refresh` downloads again). Only the first link of each list item or table row is read (the member), and
each linked page is matched to an MP through its Wikidata item (MediaWiki API `prop=pageprops`), which
`wikidata_mps_2024.json` ties to the parliament.uk member id. An MP on two lists with different ideologies, or on a
list outside their party's range, falls back to their party. Everyone else takes their party's mainstream ideology,
with a little seeded variation for Labour, Conservative and Lib Dem backbenchers. The reason for each MP is a
comment in `history/characters/wm_2024_mps.txt` and a line in `tools/test_out/ideology_2024.txt`.

| File in `raw/` | Article (section read) | Ideology |
|---|---|---|
| `wikipedia_caucus_socialist_campaign_group.json` | Socialist Campaign Group ("Current members"; "Expelled" and "Defected" entries dated 2024 or later) | Socialist |
| `wikipedia_caucus_one_nation_conservatives_caucus.json` | One Nation Conservatives (caucus) ("Membership") | One Nation |
| `wikipedia_caucus_european_research_group.json` | European Research Group ("Structure": chairs and subscribers, not past subscribers) | National Conservative |
| `wikipedia_caucus_common_sense_group.json` | Common Sense Group ("Conservative MPs") | National Conservative |
| `wikipedia_caucus_new_conservatives_uk.json` | New Conservatives (UK) ("Membership") | National Conservative |
| `wikipedia_caucus_free_market_forum.json` | Free Market Forum (parliamentary supporters) | Free-market |
| `wikipedia_caucus_qids.json` | Wikidata item of each linked page | |

Licence: Wikipedia text is CC BY-SA 4.0 (<https://en.wikipedia.org/>, the articles' authors); the mod uses only the
plain fact of membership, not the text. Reform UK MPs are Populist Right by party. No reliable member list was found
for Labour's centrist groups (Labour to Win, Labour Together, Progress) or the Conservative Growth Group, so Labour
Centrists and most Free-marketeers come from the seeded fallback. Two people who aren't 2024 MPs are set by hand from
their Wikipedia articles: Liz Truss (Free-market: the Conservative Growth Group backs her) and Tony Blair (Centrist:
New Labour, Progress). Independents take the mainstream ideology of the party they came from where Wikipedia records
one (Alex Easton: DUP; Ayoub Khan: Liberal Democrat councillor), otherwise Centrist; Jeremy Corbyn is on the
Socialist Campaign Group's list.

<!-- flags:begin (generated by tools/ui/build_flags.py) -->
## Flags (title coats of arms)

`tools/ui/build_flags.py` downloads these SVGs from Wikimedia Commons into `raw/flags/` once (with `raw/flags/meta.json`; `--refresh` downloads again), renders them with resvg and stretches them to 3:2. The textures made from CC BY-SA files are under the same licence, with the attribution below. Every other title's flag is derived (generated) and needs no attribution.

| Flag | Title | Commons file | Author | Licence |
|---|---|---|---|---|
| Union Flag | `e_united_kingdom` | [Flag of the United Kingdom (3-5).svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_United_Kingdom_(3-5).svg) | Original: Acts of Union 1800 Vector: Yaddah | Public domain |
| St George's Cross | `k_england` | [Flag of England.svg](https://commons.wikimedia.org/wiki/File:Flag_of_England.svg) | Original: traditional Vector: Nicholas Shanks | Public domain |
| Saltire | `k_scotland` | [Flag of Scotland.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Scotland.svg) | none known | Public domain |
| Y Ddraig Goch | `k_wales` | [Flag of Wales.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Wales.svg) | Unknown Vector graphics by Tobias Jakobs | Public domain |
| St Patrick's Saltire (Northern Ireland has no official flag of its own) | `k_northern_ireland` | [Saint Patrick's Saltire.svg](https://commons.wikimedia.org/wiki/File:Saint_Patrick%27s_Saltire.svg) | Hoshie and others | Public domain |
| Royal Standard | `k_wm_crown` | [Royal standard of the United Kingdom.svg](https://commons.wikimedia.org/wiki/File:Royal_standard_of_the_United_Kingdom.svg) | Own work | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Northumbria | `d_northumberland_durham_and_tyne_and_wear` | [Flag of Northumbria.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Northumbria.svg) | Oren neu dag (talk) | Public domain |
| Cumbria | `d_cumbria` | [Community flag of Cumbria.svg](https://commons.wikimedia.org/wiki/File:Community_flag_of_Cumbria.svg) | Ben Walker | CC0 (http://creativecommons.org/publicdomain/zero/1.0/deed.en) |
| Lancashire | `d_lancashire` | [Flag of Lancashire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Lancashire.svg) | Wereon | CC BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/) |
| Cheshire | `d_cheshire` | [Flag of Cheshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Cheshire.svg) | Vexilo | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Merseyside | `d_merseyside` | [County Flag of Merseyside.svg](https://commons.wikimedia.org/wiki/File:County_Flag_of_Merseyside.svg) | Orionist | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| East Riding of Yorkshire | `d_east_yorkshire_and_northern_lincolnshire` | [Flag of the East Riding of Yorkshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_East_Riding_of_Yorkshire.svg) | Vexilo | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| North Riding of Yorkshire | `d_north_yorkshire` | [Flag of North Riding of Yorkshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_North_Riding_of_Yorkshire.svg) | Inops, original version by Vexilo | Public domain |
| West Riding of Yorkshire | `d_west_yorkshire` | [Flag of the West Riding of Yorkshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_West_Riding_of_Yorkshire.svg) | File:FlagOfYorkshire.svg The Yorkshire Ridings Society and The Flag Institute derivative work: Hogweard | Public domain |
| Lincolnshire | `d_lincolnshire` | [Flag of Lincolnshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Lincolnshire.svg) | unknown | Public domain |
| West Midlands | `d_west_midlands` | [Flag of the West Midlands County.svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_West_Midlands_County.svg) | Jpb1301 | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Essex | `d_essex` | [Flag of Essex.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Essex.svg) | Greentubing | Public domain |
| Cambridgeshire | `d_cambridgeshire_and_peterborough` | [Cambridgeshire Flag.svg](https://commons.wikimedia.org/wiki/File:Cambridgeshire_Flag.svg) | Hogweard | Public domain |
| Norfolk | `d_norfolk` | [Flag of Norfolk.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Norfolk.svg) | Hogweard | Public domain |
| Suffolk | `d_suffolk` | [County Flag of Suffolk.svg](https://commons.wikimedia.org/wiki/File:County_Flag_of_Suffolk.svg) | Vexilo | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Kent | `d_kent` | [Flag of Kent.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Kent.svg) | Richard Thompson | CC BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/) |
| Cornwall (St Piran's Flag) | `d_cornwall_and_isles_of_scilly` | [Flag of Cornwall.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Cornwall.svg) | Jon Harald Søby | Public domain |
| Devon (St Petroc's Flag) | `d_devon` | [Flag of Devon.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Devon.svg) | Greentubing | Public domain |
| Middlesex | `d_outer_london_west_and_north_west` | [Flag of Middlesex.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Middlesex.svg) | The College of Arms | Public domain |
| Hampshire | `d_hampshire_and_isle_of_wight` | [Flag of Hampshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Hampshire.svg) | Greentubing | CC BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/) |
| Bedfordshire | `c_bedford` | [Bedfordshire County Flag.svg](https://commons.wikimedia.org/wiki/File:Bedfordshire_County_Flag.svg) | Hogweard | Public domain |
| Berkshire | `c_reading_central` | [Flag of Berkshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Berkshire.svg) | The Flag Institute Vexilo Hogweard | Public domain |
| Buckinghamshire | `c_aylesbury` | [Flag of Buckinghamshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Buckinghamshire.svg) | The Flag Institute | Attribution |
| Hertfordshire | `c_hertford_and_stortford` | [County Flag of Hertfordshire.svg](https://commons.wikimedia.org/wiki/File:County_Flag_of_Hertfordshire.svg) | FlagOfHertfordshire.PNG: The College of Arms derivative work: Malyszkz (talk) | Public domain |
| Herefordshire | `c_hereford_and_south_herefordshire` | [County Flag Of Herefordshire.svg](https://commons.wikimedia.org/wiki/File:County_Flag_Of_Herefordshire.svg) | Vexilo | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Worcestershire | `c_worcester` | [Flag of Worcestershire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Worcestershire.svg) | User:Hogweard and The Flag Institute | Public domain |
| Warwickshire | `c_warwick_and_leamington` | [Flag of Warwickshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Warwickshire.svg) | Vexilo Hogweard | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Shropshire | `c_shrewsbury` | [Flag of Shropshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Shropshire.svg) | Hogweard | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Staffordshire | `c_stafford` | [Staffordshire Flag.svg](https://commons.wikimedia.org/wiki/File:Staffordshire_Flag.svg) | User:Hogweard | Public domain |
| Derbyshire | `c_derbyshire_dales` | [Derbyshire flag.svg](https://commons.wikimedia.org/wiki/File:Derbyshire_flag.svg) | Dyfsunctional at English Wikipedia | Public domain |
| Nottinghamshire | `c_rushcliffe` | [County Flag of Nottinghamshire.svg](https://commons.wikimedia.org/wiki/File:County_Flag_of_Nottinghamshire.svg) | The Flag Institute | Public domain |
| Leicestershire | `c_mid_leicestershire` | [Flag of Leicestershire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Leicestershire.svg) | Hogweard | Public domain |
| Rutland | `c_rutland_and_stamford` | [Rutland County Flag.svg](https://commons.wikimedia.org/wiki/File:Rutland_County_Flag.svg) | Hogweard | Public domain |
| Northamptonshire | `c_northampton_south` | [Flag of Northamptonshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Northamptonshire.svg) | Brady Ells &amp; Ian Chadwick and The Flag Institute | Public domain |
| Oxfordshire | `c_oxford_east` | [Flag of Oxfordshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Oxfordshire.svg) | Vexilo | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Surrey | `c_guildford` | [Flag of Surrey.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Surrey.svg) | Hogweard | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Sussex | `c_lewes` | [Flag of Sussex.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Sussex.svg) | Unknown authorUnknown author | Public domain |
| Isle of Wight | `c_isle_of_wight_west` | [Flag of the Isle of Wight.svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_Isle_of_Wight.svg) | John Graney and The Flag Institute | Public domain |
| Somerset | `c_taunton_and_wellington` | [Flag of Somerset.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Somerset.svg) | Leonardo Piccioni de Almeida | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Dorset | `c_west_dorset` | [Flag of Dorset.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Dorset.svg) | Stephen Coombs &amp; Dave White | Public domain |
| Wiltshire | `c_south_west_wiltshire` | [County Flag of Wiltshire.svg](https://commons.wikimedia.org/wiki/File:County_Flag_of_Wiltshire.svg) | Wiltshire_flag.svg: Tango22 derivative work: NikNaks talk - gallery - wikipedia | Public domain |
| County Durham | `c_city_of_durham` | [Flag of County Durham.svg](https://commons.wikimedia.org/wiki/File:Flag_of_County_Durham.svg) | Martin23230 | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Northumberland | `c_north_northumberland` | [Flag of Northumberland.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Northumberland.svg) | Greentubing | Public domain |
| Tyne and Wear | `c_newcastle_upon_tyne_central_and_west` | [Flag of Tyne and Wear.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Tyne_and_Wear.svg) | Pete Loeser, vectorisation by RAPTOR7762Whats up? 16:29, 18 February 2026 (UTC) | Public domain |
| Cumberland | `c_carlisle` | [Flag of Cumberland.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Cumberland.svg) | JimmyGuano | CC0 (http://creativecommons.org/publicdomain/zero/1.0/deed.en) |
| Westmorland | `c_westmorland_and_lonsdale` | [Flag of Westmorland.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Westmorland.svg) | User:Hogweard | Public domain |
| Huntingdonshire | `c_huntingdon` | [Flag of Huntingdonshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Huntingdonshire.svg) | Hogweard | Public domain |
| Yorkshire | `c_york_outer` | [Flag of Yorkshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Yorkshire.svg) | The Yorkshire Ridings Society and The Flag Institute | Public domain |
| Aberdeenshire | `c_west_aberdeenshire_and_kincardine` | [Flag of Aberdeenshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Aberdeenshire.svg) | Hogweard | Public domain |
| Banffshire | `c_aberdeenshire_north_and_moray_east` | [Flag of Banffshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Banffshire.svg) | Hogweard | Public domain |
| Angus | `c_angus_and_perthshire_glens` | [Flag of Angus.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Angus.svg) | Swiãtopôłk | CC0 (http://creativecommons.org/publicdomain/zero/1.0/deed.en) |
| East Lothian | `c_lothian_east` | [Flag of East Lothian.svg](https://commons.wikimedia.org/wiki/File:Flag_of_East_Lothian.svg) | Hogweard | Public domain |
| Berwickshire | `c_berwickshire_roxburgh_and_selkirk` | [Flag of Berwickshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Berwickshire.svg) | Hogweard | Public domain |
| Kirkcudbrightshire | `c_dumfries_and_galloway` | [Flag of Kirkcudbrightshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Kirkcudbrightshire.svg) | Hogweard | Public domain |
| Caithness | `c_caithness_sutherland_and_easter_ross` | [Flag of Caithness.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Caithness.svg) | Hogweard | Public domain |
| Orkney | `c_orkney_and_shetland` | [2007 Flag of Orkney.svg](https://commons.wikimedia.org/wiki/File:2007_Flag_of_Orkney.svg) | Rab Knight from en.wikipedia | Public domain |
| Shetland (to Lerwick, as Orkney's flag has the seat) | `b_lerwick` | [Flag of Shetland.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Shetland.svg) | unknown | Public domain |
| Anglesey | `c_ynys_mon` | [Flag of Anglesey.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Anglesey.svg) | The Flag Institute | Public domain |
| Caernarfonshire | `c_bangor_aberconwy` | [Flag of Caernarfonshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Caernarfonshire.svg) | Hogweard | Public domain |
| Merionethshire | `c_dwyfor_meirionnydd` | [Flag of Merionethshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Merionethshire.svg) | The Flag Institute | Public domain |
| Flintshire | `c_alyn_and_deeside` | [Flag of Flintshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Flintshire.svg) | Hogweard | Public domain |
| Brecknockshire | `c_brecon_radnor_and_cwm_tawe` | [Flag of Brecknockshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Brecknockshire.svg) | Hogweard | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Pembrokeshire | `c_mid_and_south_pembrokeshire` | [Flag of Pembrokeshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Pembrokeshire.svg) | Peter Stock. Vectorized by Magasjukur2 | CC0 (http://creativecommons.org/publicdomain/zero/1.0/deed.en) |
| Glamorgan | `c_vale_of_glamorgan` | [Glamorgan Flag.svg](https://commons.wikimedia.org/wiki/File:Glamorgan_Flag.svg) | User:Hogweard | Public domain |
| Monmouthshire | `c_monmouthshire` | [Flag of Monmouthshire.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Monmouthshire.svg) | NikNaks | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| City of York | `c_york_central` | [Flag of York.svg](https://commons.wikimedia.org/wiki/File:Flag_of_York.svg) | Ec.Domnowall | CC BY 3.0 (https://creativecommons.org/licenses/by/3.0) |
| City of London | `c_cities_of_london_and_westminster` | [Flag of the City of London.svg](https://commons.wikimedia.org/wiki/File:Flag_of_the_City_of_London.svg) | Greentubing | Public domain |
| Birmingham | `c_birmingham_ladywood` | [Banner of arms of the City of Birmingham (1976–).svg](https://commons.wikimedia.org/wiki/File:Banner_of_arms_of_the_City_of_Birmingham_(1976%E2%80%93).svg) | JimmyGuano | CC0 (http://creativecommons.org/publicdomain/zero/1.0/deed.en) |
| Norwich | `c_norwich_south` | [Flag of Norwich.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Norwich.svg) | LegerityFortis | Public domain |
| Plymouth | `c_plymouth_sutton_and_devonport` | [Flag of Plymouth.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Plymouth.svg) | IncoherentP | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Glasgow | `c_glasgow_north` | [Flag of Glasgow.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Glasgow.svg) | TilmannR | CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0) |
| Edinburgh | `c_edinburgh_east_and_musselburgh` | [Flag of Edinburgh.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Edinburgh.svg) | NikNaks talk - gallery - wikipedia | CC BY-SA 3.0 (http://creativecommons.org/licenses/by-sa/3.0/) |
| Aberdeen | `c_aberdeen_north` | [Flag of Aberdeen.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Aberdeen.svg) | Oren neu dag (talk) | CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0) |
| Cardiff | `c_cardiff_south_and_penarth` | [Flag of Cardiff.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Cardiff.svg) | City_of_Cardiff_flag.png: The College of Arms / The Flag Institute derivative work: NikNaks talk - gallery - wikipedia | Public domain |
| Belfast | `c_belfast_south_and_mid_down` | [Flag of Belfast.svg](https://commons.wikimedia.org/wiki/File:Flag_of_Belfast.svg) | CityOfBelfastFlag.PNG: The College of Arms / The Flag Institute derivative work: NikNaks talk - gallery - wikipedia | Public domain |
<!-- flags:end -->


### Additional historical eras (development build)

`tools/data/build_eras.py` reads dated Commons memberships from the cached mySociety ParlParse people export,
filtering posts by `organization_id = house-of-commons` so devolved memberships cannot enter the Commons. Sources:
<https://github.com/mysociety/parlparse> and <https://members-api.parliament.uk/>. The raw membership export is already
used by the 1979 builder. Snapshots in `data/snapshots/{1945,1997,2010,2016}.json` record every mapping, notional seat
and unlanded historical MP. Numerical national baselines are rounded election shares, not reconstructed local results.

The older membership export lacks party labels. `members_1945_affiliations.json` records the factual 640-member
1945 table from [List of MPs elected in the 1945 United Kingdom general election](https://en.wikipedia.org/wiki/List_of_MPs_elected_in_the_1945_United_Kingdom_general_election),
retrieved 18 October 2026; Wikipedia contributors, CC BY-SA 4.0. Source URL and retrieval date are retained in the
file. Labour Co-operative members join the Labour group; National Liberals and Scottish Unionists join the
Conservative group. Minor parties without a represented party group are currently independent. This is a gameplay
grouping, not a claim that their original party identities were identical.

The Commons Library's [election dataset](https://commonslibrary.parliament.uk/research-briefings/cbp-8647/)
explains historical boundaries and multi-member/university seats. Historical geography is approximated on the fixed
650-seat modern map; local vote baselines are notional winner-based leans, not historical constituency vote shares.

`female_mps.json` caches the factual names from Wikipedia contributors' [list of female Commons members](https://en.wikipedia.org/wiki/List_of_female_members_of_the_House_of_Commons_of_the_United_Kingdom), retrieved 18 October 2026, CC BY-SA 4.0. The historical builder also uses cached Parliament API gender records and explicit documented name aliases; it does not infer gender from first names.
