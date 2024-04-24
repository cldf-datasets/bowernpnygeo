import json
import types
import pathlib
import subprocess
import collections

from shapely import union_all
from shapely.geometry import shape
from pycldf import Sources
from cldfbench import Dataset as BaseDataset
from clldutils.color import qualitative_colors
from clldutils.jsonlib import dump
from clldutils.markup import add_markdown_text

BASE_URL = "https://zenodo.org/record/4898185/files/"
FILES = [
    'Chirila Language Codes.xlsx',
    'AustralianPolygons.kml',
    'AustralianCentroids.kml',
    'AustralianLanguageFamilies.kml',
]


def merged_geometry(features):
    # Note: We slightly increase each polygon using `buffer` to make sure they overlap a bit and
    # internal boundaries are thus removed.
    return union_all([shape(f['geometry']).buffer(0.001) for f in features])


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
        geojson = dict(type="FeatureCollection", features=self, properties=self.properties)
        dump(geojson, self.path, indent=2)

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

        glangs = {lg.id: lg for lg in args.glottolog.api.languoids()}
        lang2fam = {}
        lang = {gc for gc, glang in glangs.items() if glang.level.name == 'language'}

        polys_by_code = collections.defaultdict(list)
        coded_langs = {
            r['Name']: r for r in self.etc_dir.read_csv('languages.csv', dicts=True)
            if r.get('Glottocode')}

        # Assemble all Glottocodes related to any area.
        uncoded = []
        for i, f in enumerate(self.raw_dir.read_json('AustralianPolygons.geojson')['features']):
            props = types.SimpleNamespace(**f['properties'])
            args.writer.objects['ContributionTable'].append(dict(
                ID=props.fid,
                Name=props.name,
                Layer=props.layer,
                Pama_Nyungan=getattr(props, 'Family', '').lower() != 'nonpny',
                Dialect=getattr(props, 'Dialect', '') == 'y',
                Comment=getattr(props, 'description', None),
                Source=['bowern_2021']
            ))
            if props.name in coded_langs:
                glang = glangs[coded_langs[props.name]['Glottocode']]
                polys_by_code[glang.id].append((props.fid, f))
                lang2fam[glang.id] = glang.id if not glang.lineage else glang.lineage[0][1]
                if glang.lineage:
                    lang2fam[glang.id] = glang.lineage[0][1]
                    for _, fgc, _ in glang.lineage:
                        lang2fam[fgc] = glang.lineage[0][1]
                        polys_by_code[fgc].append((props.fid, f))
                else:
                    lang2fam[glang.id] = glang.id
            else:
                uncoded.append(f)
        dump(dict(type="FeatureCollection", features=uncoded),
             self.etc_dir / 'uncoded.geojson', indent=2)

        colors = dict(zip(
            [k for k, v in collections.Counter(lang2fam.values()).most_common()],
            qualitative_colors(len(lang2fam.values()))))

        with FeatureCollection(
            self.cldf_dir / 'languages.geojson',
            title='Speaker areas for languages',
            description='Speaker areas aggregated for Glottolog language-level languoids, '
                        'color-coded by family.',
        ) as geojson:
            for gc, polys in polys_by_code.items():
                glang = glangs[gc]
                if gc in lang:
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=gc,
                        Name=glang.name,
                        Glottocode=gc,
                        Latitude=glang.latitude,
                        Longitude=glang.longitude,
                        Source_Languoid_IDs=[p[0] for p in polys],
                        Speaker_Area=geojson.path.stem,
                        Glottolog_Languoid_Level='language',
                        Family=glangs[lang2fam[gc]].name if lang2fam[gc] != gc else None,
                    ))
                    geojson.append_feature(
                        merged_geometry([p[1] for p in polys]),
                        title=glang.name,
                        fill=colors[lang2fam[gc]],
                        family=glangs[lang2fam[gc]].name if lang2fam[gc] != gc else None,
                        **{'cldf:languageReference': gc, 'fill-opacity': 0.8})
        args.writer.objects['MediaTable'].append(geojson.as_row())

        with FeatureCollection(
            self.cldf_dir / 'families.geojson',
            title='Speaker areas for language families',
            description='Speaker areas aggregated for Glottolog top-level family languoids.',
        ) as geojson:
            for gc in sorted(set(lang2fam.values())):
                glang = glangs[gc]
                if gc not in lang:  # Don't append isolates twice!
                    args.writer.objects['LanguageTable'].append(dict(
                        ID=gc,
                        Name=glang.name,
                        Glottocode=gc,
                        Source_Languoid_IDs=[p[0] for p in polys_by_code[gc]],
                        Speaker_Area=geojson.path.stem,
                        Glottolog_Languoid_Level='family',
                    ))
                geojson.append_feature(
                    merged_geometry([p[1] for p in polys_by_code[gc]]),
                    title=glang.name,
                    fill=colors[gc],
                    **{'cldf:languageReference': gc, "fill-opacity": 0.8})
        args.writer.objects['MediaTable'].append(geojson.as_row())

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
                'name': 'Glottolog_Languoid_Level'},
            {
                'name': 'Family',
            },
            {
                'name': 'Source_Languoid_IDs',
                'separator': ' ',
                'dc:description': 'List of identifiers of shapes in the original shapefile that '
                                  'were aggregated to create the shape referenced by Speaker_Area.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference'
            },
        )
