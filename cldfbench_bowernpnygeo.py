import pathlib
import subprocess
import collections

from shapely.geometry import shape, Point
from cldfbench import Dataset as BaseDataset
from cldfbench.datadir import DataDir

LCOLS = {
    'glottolog@id': 'Glottocode',
    'ISO639': 'ISO639P3code',
    'StandardLanguageName': 'Name',
    'Family': 'Family',
    'Langs_Subgroups::SubgroupName': 'SubGroup',
    'EtymologyofName': 'EtymologyOfName',
    'Latitude': 'Latitude',
    'Longitude': 'Longitude',
    'AIATSIS_Code': 'AIATSIScode',
}
BASE_URL = "https://zenodo.org/record/4898185/files/"
FILES = [
    'Chirila Language Codes.xlsx',
    'AustralianPolygons.kml',
    'AustralianCentroids.kml',
    'AustralianLanguageFamilies.kml',
]
# Matches by looking up point coordinates in polygons:
KML_NAME_TO_STANDARD_NAME = {
    "Karlaaku": "Galaagu",
    "Ngajumaya": "Ngatjumaya",
    "Wanamara": "Wunumara",
    #"Kuuku Yani": "Umpithamu",
    #"Kugu Nganhcara": "Kugu-Uwanh",
    "Yirandhali": "Yirandali",
    #"Minang": "Bibbulman",
    #"Nyunga": "Wudjari",
    "Mbeiwum": "Mbiywom",
    #"Ndra'ngith": "Anguthimri",
    #"Amangu": "Nganakarti",
    "Mpalityan": "Mpalitjanh",
    #"WakaWaka": "Gureng Gureng",
    "Gubbi Gubbi": "Gabi-Gabi",
    "Guyani": "Kuyani",
    "Nunukal": "Nukunul",
    #"Uw-Olgol": "Koko-Bera",
    "Kuuk-Narr": "Kok-Nar",
    #"Koko Bera": "Kuuku-Ya'u",
    "Yir Yoront": "Yir-Yoront",
    "Kuku Yalanji": "Kuku-Yalanji",
    "YortaYorta": "Yorta Yorta",
    "Gandangara": "Gundungurra",
    "Nimanburu": "Nimanburru",
    #"Kwini": "Gunin",
    "Djadjawurung": "Djadjawurrung",
    "MathiMathi": "Mathi-Mathi",
    "Wemba Wemba": "Yabula-Yabula",
    "Ngaliwuru": "Ngaliwurru",
    "Magati Ke": "Mati Ke",
    #"Marri Ammu": "Marrithiyel",
    "Ladji Ladji": "Ladji-Ladji",
    #"Yiman": "Waka-Waka",
    #"Yangga": "Biri",
    "Kokatha": "Kukatha",
    #"Daungwurrung": "Wemba-Wemba",
    "Djirbal": "Dyirbal",
    #"Wirri": "Barada",
    #"Wadjigu": "Gayiri",
    "Anmatyerr": "Anmatyerre",
    "Lower Aranda": "Lower Southern Aranda",
    "Western Arrarnta": "Western Arrarnte",
    "Eastern Arrernte": "Eastern and Central Arrernte",
    #"Bigambal": "Githabul",
    #"Wangkangurru": "Karangura",
    "Darrkinyung": "Darkinyung",
    "Thanggatti": "Thanggati",
    "Eora": "Iyora",
    "Gija": "Kija",
    "Gajirrebeng": "Kajirrabeng",
    #"Mengerrdji": "Erre",
    "Urningangk": "Urningangga",
    "Yaygirr": "Yaygir",
    "Bininj Kunwok": "Bininj Gun-wok",
    "Gudanji": "Gurdanji",
    #"Tharrgari": "Thiin",
    "Dungaloo": "Dhungaloo",
    #"Yiningayi": "Wadjabangayi",
    "Larrakia": "Larrakiya",
    #"Ngarkat": "Ngayawang",
    #"Ngaiawang": "Keramin",
    "Raminyeri": "Ramindjeri",
    #"Tharrayi": "Yingkarta",
    "Nhanda": "Nhanta",
    "Hunter River Lake Macquarie": "Hunter River and Lake Macquarie",
    "Kungkarri": "Kungkari",
    "Gaagudju": "Gagudju",
    #"Gugu Badhun": "Gudjal",
    #"Jiwarliny": "Yulparija",
    #"Garandi": "Kuthant",
    #"Southern Anaiwan": "Nganyaywana",
    #"Ribh": "Kurtjar",
    #"Gugu Djangun": "Mbabaram",
    #"Wik-Alkan": "Wik-Ngatharr",
    #"Wik-Alkan": "Wik-Me?nh",
    #"Wik-Paacha": "Wik-Ngathan",
    #"Kuuk Yak": "Kuuk Thaayorre",
    "Takalak": "Tagalaka",
    #"Athima": "Walangama",
    #"Ogunyjan": "Olkola",
    #"Menthe": "Emmi",
    #"Yunggurr": "Matngele",
    #"Tyerraty": "Kungarakany",
    #"Marri Tjevin": "Marringarr",
    "Nyaanyatjarra": "Ngaanyatjarra",
    #"Omeo language": "Bidhawal",
    #"Condamine- Upper-Clarence": "Bandjalang",
    #"Lower Richmond": "Minjungbal",
    "Guyambal": "Yugambal",
    #"Awu Alaya": "Gugu-Rarmul",
    #"Ogh-Alungul": "Gugu-Warra",
    #"Ogh-Alungul": "Aghu-Tharnggala",
    #"Ogh Awarrangg": "Kunjen",
    #"Agu Aloja": "Kuuk-Yak",
    "Southern Kaantju": "Kaanju",
}

class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "bowernpnygeo"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return super().cldf_specs()

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
        langs = {r['StandardLanguageName']: r
                 for r in self.raw_dir.read_csv('Chirila_Language_Codes.Sheet1.csv', dicts=True)}
        print(len(langs))
        mlayer, mcat = collections.Counter(), collections.Counter()
        missing = {}
        for i, f in enumerate(self.raw_dir.read_json('AustralianPolygons.geojson')['features']):
            props = f['properties']
            props['name'] = KML_NAME_TO_STANDARD_NAME.get(props['name'], props['name'])
            if props['name'] not in langs:
                mlayer.update([props.get('layer')])
                mcat.update([props.get('Dialect')])
                missing[props['name']] = shape(f['geometry'])
            else:
                del langs[f['properties']['name']]
        print(mlayer)
        print(mcat)
        print('{} unmatched Languages in Language_Codes sheet'.format(len(langs)))
        for l in sorted(langs):
            print(l)

        print('{} unmatched Languages in AustralianPolygons'.format(len(missing)))
        for name in sorted(missing):
            print(name)
        #    for lname, l in langs.items():
        #        if l['RoundedLong'] and l['RoundedLat']:
        #            p = Point(float(l['RoundedLong']), float(l['RoundedLat']))
        #            if p.within(area):
        #                print('    "{}": "{}",'.format(name, lname))
