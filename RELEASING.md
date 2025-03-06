# Releasing

```shell
cldfbench makecldf cldfbench_bowernpnygeo.py --glottolog-version v5.1
pytest
```

```shell
cldfbench zenodo cldfbench_bowernpnygeo.py
```

```shell
cldfbench cldfreadme cldfbench_bowernpnygeo.py 
```

```shell
cldfbench readme cldfbench_bowernpnygeo.py 
```

```shell
pytest
```


```shell
cldfbench geojson.validate cldf
```

```shell
cldfbench geojson.multipolygon_spread cldf --format tsv | csvcut -t -c ID | cldfbench geojson.geojson cldf - > mpspread.geojson
```

```shell
cldfbench geojson.glottolog_distance cldf --format tsv | csvgrep -t -c Distance -r"(1|2|3|4|5|6|7|8|9)\." | csvcut -c ID | cldfbench geojson.geojson cldf - > gldist.geojson
```