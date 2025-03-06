import json
import types
import pathlib
import subprocess

from pycldf import Sources
from cldfbench import Dataset as BaseDataset
from clldutils.jsonlib import dump
from clldutils.markup import add_markdown_text
from cldfgeojson.create import feature_collection, aggregate, shapely_fixed_geometry
from cldfgeojson.geojson import MEDIA_TYPE

BASE_URL = "https://zenodo.org/record/4898185/files/"
FILES = [
    'Chirila Language Codes.xlsx',
    'AustralianPolygons.kml',
    'AustralianCentroids.kml',
    'AustralianLanguageFamilies.kml',
]


class FeatureCollection(list):
    def __init__(self, path, **properties):
        self.path = path
        self.properties = properties
        list.__init__(self)

    def __enter__(self):
        return self

    def append_feature(self, shape, **properties):
        self.append(dict(type="Feature", properties=properties, geometry=shape.__geo_interface__))

    def __exit__(self, exc_type, exc_val, exc_tb):
        dump(feature_collection(self, **self.properties), self.path, indent=2)

    def as_row(self, **kw):
        res = dict(
            ID=self.path.stem,
            Name=self.properties['title'],
            Description=self.properties['description'],
            Media_Type='application/geo+json',
            Download_URL=self.path.name,
        )
        res.update(kw)
        return res


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "bowernpnygeo"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

    def cmd_readme(self, args) -> str:
        ds = self.cldf_reader()
        pny = [l for l in ds.objects('LanguageTable') if l.cldf.glottocode == 'pama1250'][0]
        geojson = json.dumps(pny.speaker_area_as_geojson_feature)
        return add_markdown_text(
            BaseDataset.cmd_readme(self, args),
            self.dir.joinpath('NOTES.md').read_text(encoding='utf8').format(geojson),
            'Description')

    def cmd_download(self, args):
        for f in FILES:
            with self.raw_dir.temp_download(BASE_URL + f + '?download=1', f.replace(' ', '_')) as p:
                if p.suffix == '.kml':
                    subprocess.check_call(['k2g', str(p), str(self.raw_dir)])
                elif p.suffix == '.xlsx':
                    self.raw_dir.xlsx2csv(p.name)
                else:
                    raise ValueError(p)

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf)
        args.writer.cldf.add_sources(*Sources.from_file(self.etc_dir / 'sources.bib'))
        coded_langs = {
            r['Name']: r for r in self.etc_dir.read_csv('languages.csv', dicts=True)
            if r.get('Glottocode')}

        uncoded, polys = [], []
        for i, f in enumerate(self.raw_dir.read_json('AustralianPolygons.geojson')['features']):
            props = types.SimpleNamespace(**f['properties'])
            args.writer.objects['ContributionTable'].append(dict(
                ID=props.fid,
                Name=props.name,
                Layer=props.layer,
                Pama_Nyungan=getattr(props, 'Family', '').lower() != 'nonpny',
                Dialect=getattr(props, 'Dialect', '') == 'y',
                Comment=getattr(props, 'description', None),
                Glottocode=coded_langs.get(props.name, {}).get('Glottocode'),
                Source=['bowern_2021'],
                Media_ID='features',
            ))
            if props.name in coded_langs:
                polys.append((props.fid, f, coded_langs[props.name]['Glottocode']))
            else:
                uncoded.append(f)

        args.writer.objects['MediaTable'].append(dict(
                ID='features',
                Name='Areas depicted in the source',
                Description='Language polygons as represented in Bowern 2021, in the file '
                            'AustralianPolygons.kml. These polygons form the atomic units from '
                            'which the aggregated speaker areas for Glottolog languages and '
                            'famiies in this dataset are aggregated.',
                Media_Type=MEDIA_TYPE,
                Download_URL='features.geojson',
            ))
        dump(feature_collection([f for _, f, _ in polys] + uncoded, title="", description=""),
             self.cldf_dir / 'features.geojson',
             indent=2)

        lids = None
        for ptype in ['language', 'family']:
            label = 'languages' if ptype == 'language' else 'families'
            p = self.cldf_dir / '{}.geojson'.format(label)
            features, languages = aggregate(polys, args.glottolog.api, level=ptype, buffer=0.005)
            dump(feature_collection(
                [shapely_fixed_geometry(f) for f in features],
                title='Speaker areas for {}'.format(label),
                description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype)),
                p,
                indent=2)
            for glang, pids, family in languages:
                if lids is None or (glang.id not in lids):  # Don't append isolates twice!
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=glang.id,
                        Name=glang.name,
                        Glottocode=glang.id,
                        Latitude=glang.latitude,
                        Longitude=glang.longitude,
                        Feature_IDs=pids,
                        Speaker_Area=p.stem,
                        Glottolog_Languoid_Level=ptype,
                        Family=family,
                    ))
            args.writer.objects['MediaTable'].append(dict(
                ID=p.stem,
                Name='Speaker areas for {}'.format(label),
                Description='Speaker areas aggregated for Glottolog {}-level languoids, '
                            'color-coded by family.'.format(ptype),
                Media_Type=MEDIA_TYPE,
                Download_URL=p.name,
            ))
            lids = {gl.id for gl, _, _ in languages}

    def schema(self, cldf):
        t = cldf.add_component(
            'ContributionTable',
            "Layer",
            {
                "name": "Pama_Nyungan",
                "dc:description":
                    "Flag signaling whether the variety is member of the Pama-Nyungan family.",
                "datatype": {"base": "boolean", "format": "yes|no"},
            },
            {
                "name": "Dialect",
                "dc:description":
                    "Flag signaling whether the variety is considered a dialect.",
                "datatype": {"base": "boolean", "format": "yes|no"},
            },
            {
                'name':'Comment',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#comment'
            },
            {
                "datatype": {
                    "base": "string",
                    "format": "[a-z0-9]{4}[1-9][0-9]{3}"
                },
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#glottocode",
                "valueUrl": "http://glottolog.org/resource/languoid/id/{Glottocode}",
                "name": "Glottocode",
                'dc:description':
                    'References a Glottolog languoid most closely matching the linguistic entity '
                    'described by the feature.',
            },
            {
                'name': 'Media_ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
                'dc:description': 'Features are linked to GeoJSON files that store the geo data.'
            },

            {
                'name': 'Source',
                'separator': ';',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'
            },
        )
        t.common_props['dc:description'] = \
            ('We list the individual shapes from the source dataset as contributions in order to '
             'preserve the original metadata.')
        cldf['ContributionTable', 'id'].common_props['dc:description'] = \
            ('We use the 1-based index of the first shape with corresponding '
             'LANGUAGE property in the original shapefile as identifier.')
        cldf.add_component('MediaTable')
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Speaker_Area',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#speakerArea'
            },
            {
                'name': 'Feature_IDs',
                'separator': ' ',
                'dc:description':
                    'List of identifiers of features that were aggregated '
                    'to create the feature referenced by Speaker_Area.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'
            },
            {
                "dc:description": "https://glottolog.org/meta/glossary#Languoid",
                "datatype": {
                    "base": "string",
                    "format": "dialect|language|family"
                },
                "name": "Glottolog_Languoid_Level"
            },
            {
                "name": "Family",
                "dc:description":
                    "Name of the top-level family for the languoid in the Glottolog classification."
                    " A null value in this column marks 1) top-level families in case "
                    "Glottolog_Languoid_Level is 'family' and 2) isolates in case "
                    "Glottolog_Languoid_Level is 'language'.",
            }
        )
