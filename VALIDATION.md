# Validation

## Speaker area geometries

```shell
cldfbench geojson.validate cldf
```


## Glottolog distance

```shell
cldfbench geojson.glottolog_distance cldf --format tsv | csvgrep -t -c Distance -r"(1|2|3|4|5|6|7|8|9)\."
```
reports the following language-level speaker areas with a distance to the corresponding Glottolog
location greater than 1deg (~100km):

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

```shell
cldfbench geojson.multipolygon_spread cldf --format pipe
```

| ID | Spread | NPolys |
|:---------|---------:|---------:|
| kala1379 | 3.33 | 2 |

The two somewhat distant polygons mapped to dialects of [Kalarko-Mirniny](https://glottolog.org/resource/languoid/id/kala1379)
fit the - also spread-out - point coordinates Glottolog gives for these varieties.
