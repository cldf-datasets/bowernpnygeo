
This dataset is derived from [Files for Australian Language Locations](https://doi.org/10.5281/zenodo.4898185).
Thus, all caveats mentioned in the description of this dataset apply here as well. Suitable use
cases are described as

> These maps should be considered as a way to relate linguistic groups to one another in space. It 
> should help to visualize the approximate distances between groups, abstracting away from 
> multilingualism, population density, and Indigenous settlement patterns.

This dataset is derived as follows:

- **Matching features to Glottolog languoids**: The features (aka polygons) in the source GeoJSON
  are matched to the "nearest" Glottolog languoid in terms of the Glottolog classification. Thus,
  if no identical match can be found, varieties are matched to their parent language in Glottolog,
  and languages which are not attested in Glottolog, but the genealogy of which is known are matched
  to the closest sub-group in Glottolog. The matching was done based on languoid name, genealogy and
  location and is recorded at [etc/languages.csv](etc/languages.csv).
- The main contribution of this dataset are two GeoJSON files:
  - [cldf/languages.geojson](cldf/languages.geojson): The polygons found in the source are
    aggregated on Glottolog language level. Thus, the features in this file represent speaker areas
    for the respective Glottolog language-level languoids.
  - [cldf/families.geojson](cldf/families.geojson): The polygons found in the source are
    aggregated on Glottolog top-level family level. Considering that the language families covered
    by this dataset are only represented in Australia and all Australian languges are supposed to
    be covered here, the features in this file represent speaker areas for the respective Glottolog
    family-level languoid.


### Usage

Since the GIS data is linked to the CLDF dataset via the [speakerArea](https://github.com/cldf/cldf/tree/master/components/languages#speaker-area)
property, you can access it programmatically, e.g. using `pycldf`:

```python
>>> from pycldf import Dataset
>>> ds = Dataset.from_metadata('cldf/Generic-metadata.json')
>>> pny = [l for l in ds.objects('LanguageTable') if l.cldf.glottocode == 'pama1250'][0]
>>> import shapely
>>> area = shapely.geometry.shape(pny.speaker_area_as_geojson_feature['geometry'])
>>> area.contains(shapely.Point(140, -20))
True
>>> import json
>>> geojson = json.dumps(pny.speaker_area_as_geojson_feature, indent=2)
>>> print(geojson)
```

E.g. to display the area of the Pama-Nyungan family:

```geojson
{}
```