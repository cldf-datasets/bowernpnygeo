# Validation

## Speaker area geometries

The validity of all speaker area geometries in this dataset has been checked running the `geojson.validate`
command from the [`cldfgeojson`](https://pypi.org/project/cldfgeojson/) package:
```shell
cldfbench geojson.validate cldf
```


## Glottolog distance

To confirm agreement with other sources of geo-information for languages, we computed distances between
the speaker areas and the point-coordinates in [Glottolog](https://glottolog.org), via the `geojson.glottolog_distance`
command.
```shell
cldfbench geojson.glottolog_distance cldf --format tsv | csvgrep -t -c Distance -r"(1|2|3|4|5|6|7|8|9)\."
```

The following language-level speaker areas with a distance to the corresponding Glottolog
location greater than 1deg (~100km) were reported:

ID|Distance|Contained| NPolys | Comment
---|---|---|-------:|---
baya1257 | 1.2506413936976037 | False | 1 | https://github.com/glottolog/glottolog/issues/1143
bula1255 | 1.0516860750131474 | False | 1 | Not much seems to be known about the location of this extinct language.
kala1379 | 1.1264186776933531 | False | 2 | The varieties of the Glottoog language are also spread-out over big distances.
kung1258 | 4.0798361751535275 | False | 1 | The location of the Glottolog language is a bit of an outlier of the Southern Maric group this language belongs to.
lowe1403 | 2.2067966759172313 | False | 1 | Matches the distance of varieties of the corresponding Glottolog language https://glottolog.org/resource/languoid/id/lowe1403
mbab1239 | 2.9570642756570833 | False | 1 | https://github.com/glottolog/glottolog/issues/1142
pint1250 | 1.3224097988308894 | False | 1 | The distance of about 150km between polygon and Glottolog location seems acceptable for Central Australia.
yuga1244 | 1.4598896588088563 | False | 2 | https://github.com/glottolog/glottolog/issues/1144



## Multi-Polygon spread

Finally, we computed the spread of polygons in Multi-Polygon geometries assigned to the same language
via `geojson.multipolygon_spread`,
```shell
cldfbench geojson.multipolygon_spread cldf --format pipe
```

which reported one case with unusual spread:

| ID | Spread | NPolys |
|:---------|---------:|---------:|
| kala1379 | 3.33 | 2 |

This case does agree with the geographic information from Glottolog, though, as the two somewhat 
distant polygons mapped to dialects of [Kalarko-Mirniny](https://glottolog.org/resource/languoid/id/kala1379) fit the - also spread-out - point-coordinates 
Glottolog gives for these varieties.
