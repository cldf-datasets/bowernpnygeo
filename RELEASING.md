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

Now run the technical validation procedures described in `VALIDATION.md`.
