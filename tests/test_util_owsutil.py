"""Module grouping tests for the pydov.util.owsutil module."""
import re
import sys

import pytest
from numpy.compat import unicode

import owslib
from owslib.etree import etree
from owslib.fes import (
    PropertyIsEqualTo,
    FilterRequest,
)
from owslib.iso import MD_Metadata
from owslib.util import nspath_eval
from owslib.wfs import WebFeatureService
from pydov.util import owsutil
from pydov.util.errors import (
    MetadataNotFoundError,
    FeatureCatalogueNotFoundError,
)


@pytest.fixture
def mp_wfs(monkeypatch):
    """Monkeypatch the call to the remote GetCapabilities request.

    Parameters
    ----------
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """
    def read(*args, **kwargs):
        with open('tests/data/util/owsutil/wfscapabilities.xml', 'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
            data = etree.fromstring(data)
        return data

    monkeypatch.setattr(
        owslib.feature.common.WFSCapabilitiesReader, 'read', read)


@pytest.fixture
def wfs(mp_wfs):
    """PyTest fixture providing an instance of a WebFeatureService based on
    a local copy of a GetCapabilities request.

    Parameters
    ----------
    mp_wfs : pytest.fixture
        Monkeypatch the call to the remote GetCapabilities request.

    Returns
    -------
    owslib.wfs.WebFeatureService
        WebFeatureService based on the local GetCapabilities.

    """
    return WebFeatureService(
        url="https://www.dov.vlaanderen.be/geoserver/wfs",
        version="1.1.0")


@pytest.fixture
def mp_remote_md(wfs, monkeypatch):
    """Monkeypatch the call to get the remote metadata of the
    dov-pub:Boringen layer.

    Parameters
    ----------
    wfs : pytest.fixture returning owslib.wfs.WebFeatureService
        WebFeatureService based on the local GetCapabilities.
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """
    def __get_remote_md(*args, **kwargs):
        with open('tests/data/util/owsutil/md_metadata.xml', 'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
        return data

    if sys.version_info[0] < 3:
        monkeypatch.setattr('pydov.util.owsutil.__get_remote_md.func_code',
                            __get_remote_md.func_code)
    else:
        monkeypatch.setattr('pydov.util.owsutil.__get_remote_md.__code__',
                            __get_remote_md.__code__)


@pytest.fixture
def md_metadata(wfs, mp_remote_md):
    """PyTest fixture providing a MD_Metadata instance of the
    dov-pub:Boringen layer.

    Parameters
    ----------
    wfs : pytest.fixture returning owslib.wfs.WebFeatureService
        WebFeatureService based on the local GetCapabilities.
    mp_remote_md : pytest.fixture
        Monkeypatch the call to get the remote metadata of the
        dov-pub:Boringen layer.

    Returns
    -------
    owslib.iso.MD_Metadata
        Parsed metadata describing the Boringen WFS layer in more detail,
        in the ISO 19115/19139 format.

    """
    contentmetadata = wfs.contents['dov-pub:Boringen']
    return owsutil.get_remote_metadata(contentmetadata)


@pytest.fixture
def mp_remote_fc(monkeypatch):
    """Monkeypatch the call to get the remote feature catalogue of the
    dov-pub:Boringen layer.

    Parameters
    ----------
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """
    def __get_remote_fc(*args, **kwargs):
        with open('tests/data/util/owsutil/fc_featurecatalogue.xml', 'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
        return data

    if sys.version_info[0] < 3:
        monkeypatch.setattr('pydov.util.owsutil.__get_remote_fc.func_code',
                            __get_remote_fc.func_code)
    else:
        monkeypatch.setattr('pydov.util.owsutil.__get_remote_fc.__code__',
                            __get_remote_fc.__code__)


@pytest.fixture
def mp_remote_fc_notfound(monkeypatch):
    """Monkeypatch the call to get an inexistent remote featurecatalogue.

    Parameters
    ----------
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """
    def __get_remote_fc(*args, **kwargs):
        with open('tests/data/util/owsutil/fc_featurecatalogue_notfound.xml',
                  'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
        return data

    if sys.version_info[0] < 3:
        monkeypatch.setattr('pydov.util.owsutil.__get_remote_fc.func_code',
                            __get_remote_fc.func_code)
    else:
        monkeypatch.setattr('pydov.util.owsutil.__get_remote_fc.__code__',
                            __get_remote_fc.__code__)


@pytest.fixture
def wfs_getfeature():
    """PyTest fixture providing a WFS GetFeature response for the
    dov-pub:Boringen layer.

    Returns
    -------
    str
        WFS response of a GetFeature call to the dov-pub:Boringen layer.

    """
    with open('tests/data/search/wfsgetfeature.xml', 'r') as f:
        data = f.read()
        return data


@pytest.fixture
def mp_remote_describefeaturetype(monkeypatch):
    """Monkeypatch the call to a remote DescribeFeatureType of the
    dov-pub:Boringen layer.

    Parameters
    ----------
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """
    def __get_remote_describefeaturetype(*args, **kwargs):
        with open('tests/data/util/owsutil/wfsdescribefeaturetype.xml',
                  'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
        return data

    if sys.version_info[0] < 3:
        monkeypatch.setattr(
            'pydov.util.owsutil.__get_remote_describefeaturetype.func_code',
            __get_remote_describefeaturetype.func_code)
    else:
        monkeypatch.setattr(
            'pydov.util.owsutil.__get_remote_describefeaturetype.__code__',
            __get_remote_describefeaturetype.__code__)


def clean_xml(xml):
    """Clean the given XML string of namespace definition, namespace
    prefixes and syntactical but otherwise meaningless differences.

    Parameters
    ----------
    xml : str
        String representation of XML document.

    Returns
    -------
    str
        String representation of cleaned XML document.

    """
    # remove xmlns namespace definitions
    r = re.sub(r'[ ]+xmlns:[^=]+="[^"]+"', '', xml)

    # remove namespace prefixes in tags
    r = re.sub(r'<(/?)[^:]+:([^ >]+)([ >])', r'<\1\2\3', r)

    # remove extra spaces in tags
    r = re.sub(r'[ ]+/>', '/>', r)

    # remove extra spaces between tags
    r = re.sub(r'>[ ]+<', '><', r)

    return r


class TestOwsutil(object):
    """Class grouping tests for the pydov.util.owsutil module."""

    def test_get_csw_base_url(self, wfs):
        """Test the owsutil.get_csw_base_url method.

        Test whether the CSW base URL of the dov-pub:Boringen layer is correct.

        Parameters
        ----------
        wfs : pytest.fixture returning owslib.wfs.WebFeatureService
            WebFeatureService based on the local GetCapabilities.

        """
        contentmetadata = wfs.contents['dov-pub:Boringen']
        assert owsutil.get_csw_base_url(contentmetadata) == \
               'https://www.dov.vlaanderen.be/geonetwork/srv/nl/csw'

    def test_get_csw_base_url_nometadataurls(self, wfs):
        """Test the owsutil.get_csw_base_url method for a layer without
        metdata urls.

        Test whether a MetadataNotFoundError is raised.

        Parameters
        ----------
        wfs : pytest.fixture returning owslib.wfs.WebFeatureService
            WebFeatureService based on the local GetCapabilities.

        """
        contentmetadata = wfs.contents['dov-pub:Boringen']
        contentmetadata.metadataUrls = []
        with pytest.raises(MetadataNotFoundError):
            owsutil.get_csw_base_url(contentmetadata)

    def test_get_featurecatalogue_uuid(self, md_metadata):
        """Test the owsutil.get_featurecatalogue_uuid method.

        Test whether the featurecatalogue uuid of the dov-pub:Boringen layer
        is correct.

        Parameters
        ----------
        md_metadata : pytest.fixture providing owslib.iso.MD_Metadata
            Parsed metadata describing the Boringen WFS layer in more detail,
            in the ISO 19115/19139 format.

        """
        assert owsutil.get_featurecatalogue_uuid(md_metadata) == \
               'c0cbd397-520f-4ee1-aca7-d70e271eeed6'

    def test_get_featurecatalogue_uuid_nocontentinfo(self, md_metadata):
        """Test the owsutil.get_featurecatalogue_uuid method when the
        metadata is missing the gmd:contentInfo element.

        Test whether a FeatureCatalogueNotFoundError is raised.

        Parameters
        ----------
        md_metadata : pytest.fixture providing owslib.iso.MD_Metadata
            Parsed metadata describing the Boringen WFS layer in more detail,
            in the ISO 19115/19139 format.

        """
        tree = etree.fromstring(md_metadata.xml)
        root = tree.find('{http://www.isotc211.org/2005/gmd}MD_Metadata')
        for ci in tree.findall(
                './/{http://www.isotc211.org/2005/gmd}contentInfo'):
            root.remove(ci)
        md_metadata.xml = etree.tostring(tree)

        with pytest.raises(FeatureCatalogueNotFoundError):
            owsutil.get_featurecatalogue_uuid(md_metadata)

    def test_get_featurecatalogue_uuid_nouuidref(self, md_metadata):
        """Test the owsutil.get_featurecatalogue_uuid method when the
        gmd:contentInfo element is missing a 'uuidref' attribute.

        Test whether a FeatureCatalogueNotFoundError is raised.

        Parameters
        ----------
        md_metadata : pytest.fixture providing owslib.iso.MD_Metadata
            Parsed metadata describing the Boringen WFS layer in more detail,
            in the ISO 19115/19139 format.

        """
        tree = etree.fromstring(md_metadata.xml)
        for ci in tree.findall(nspath_eval(
            'gmd:MD_Metadata/gmd:contentInfo/'
            'gmd:MD_FeatureCatalogueDescription/'
            'gmd:featureCatalogueCitation',
            {'gmd': 'http://www.isotc211.org/2005/gmd'})):
            ci.attrib.pop('uuidref')
        md_metadata.xml = etree.tostring(tree)

        with pytest.raises(FeatureCatalogueNotFoundError):
            owsutil.get_featurecatalogue_uuid(md_metadata)

    def test_get_namespace(self, wfs, mp_remote_describefeaturetype):
        """Test the owsutil.get_namespace method.

        Test whether the namespace of the dov-pub:Boringen layer is correct.

        Parameters
        ----------
        wfs : pytest.fixture returning owslib.wfs.WebFeatureService
            WebFeatureService based on the local GetCapabilities.
        mp_remote_describefeaturetype : pytest.fixture
            Monkeypatch the call to a remote DescribeFeatureType of the
            dov-pub:Boringen layer.

        """
        assert owsutil.get_namespace(wfs, 'dov-pub:Boringen') == \
               'http://dov.vlaanderen.be/ocdov/dov-pub'

    def test_get_remote_featurecatalogue(self, mp_remote_fc):
        """Test the owsutil.get_remote_featurecatalogue method.

        Test whether the feature catalogue of the dov-pub:Boringen layer
        matches the format described in the docs.

        Parameters
        ----------
        mp_remote_fc : pytest.fixture
            Monkeypatch the call to get the remote feature catalogue of the
            dov-pub:Boringen layer.

        """
        fc = owsutil.get_remote_featurecatalogue(
            'https://www.dov.vlaanderen.be/geonetwork/srv/nl/csw',
            'c0cbd397-520f-4ee1-aca7-d70e271eeed6')

        assert type(fc) is dict

        assert 'definition' in fc
        assert type(fc['definition']) in (str, unicode)

        assert 'attributes' in fc
        assert type(fc['attributes']) is dict

        attrs = fc['attributes']
        if len(attrs) > 0:
            for attr in attrs.values():
                assert type(attr) is dict

                assert 'definition' in attr
                assert type(attr['definition']) in (str, unicode)

                assert 'values' in attr
                assert type(attr['values']) is list
                if len(attr['values']) > 0:
                    for v in attr['values']:
                        assert type(v) in (str, unicode)
                    assert len(attr['values']) == len(set(attr['values']))

                assert 'multiplicity' in attr
                mp = attr['multiplicity']
                assert type(mp) is tuple
                assert len(mp) == 2
                assert mp[0] in (0, 1)
                assert (type(mp[1]) is int and mp[1] > 0) or mp[1] == 'Inf'

    def test_get_remote_featurecataloge_baduuid(self, mp_remote_fc_notfound):
        """Test the owsutil.get_remote_featurecatalogue method with an
        inexistent feature catalogue uuid.

        Test whether a FeatureCatalogueNotFoundError is raised.

        Parameters
        ----------
        mp_remote_fc_notfound : pytest.fixture
            Monkeypatch the call to get an inexistent remote featurecatalogue.

        """
        with pytest.raises(FeatureCatalogueNotFoundError):
            owsutil.get_remote_featurecatalogue(
                'https://www.dov.vlaanderen.be/geonetwork/srv/nl/csw',
                'badfc000-0000-0000-0000-badfc00badfc')

    def test_get_remote_metadata(self, md_metadata):
        """Test the owsutil.get_remote_metadata method.

        Test whether the resulting MD_Metadata is correct.

        Parameters
        ----------
        md_metadata : pytest.fixture returning owslib.iso.MD_Metadata
            Parsed metadata describing the Boringen WFS layer in more detail,
            in the ISO 19115/19139 format.

        """
        assert type(md_metadata) is MD_Metadata

    def test_get_remote_metadata_nometadataurls(self, wfs):
        """Test the owsutil.get_remote_metadata method when the WFS layer
        missed metadata URLs.

        Test whether a MetadataNotFoundError is raised.

        Parameters
        ----------
        wfs : pytest.fixture returning owslib.wfs.WebFeatureService
            WebFeatureService based on the local GetCapabilities.

        """
        contentmetadata = wfs.contents['dov-pub:Boringen']
        contentmetadata.metadataUrls = []
        with pytest.raises(MetadataNotFoundError):
            owsutil.get_remote_metadata(contentmetadata)

    def test_wfs_build_getfeature_request_onlytypename(self):
        """Test the owsutil.wfs_build_getfeature_request method with only a
        typename specified.

        Test whether the XML of the WFS GetFeature call is generated correctly.

        """
        xml = owsutil.wfs_build_getfeature_request('dov-pub:Boringen')
        assert clean_xml(etree.tostring(xml).decode('utf8')) == clean_xml(
            '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'service="WFS" version="1.1.0" '
            'xsi:schemaLocation="http://www.opengis.net/wfs '
            'http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"><wfs:Query '
            'typeName="dov-pub:Boringen"><ogc:Filter '
            'xmlns:ogc="http://www.opengis.net/ogc"/></wfs:Query></wfs'
            ':GetFeature>')

    def test_wfs_build_getfeature_request_bbox_nogeometrycolumn(self):
        """Test the owsutil.wfs_build_getfeature_request method with a bbox
        argument but without the geometry_column argument.

        Test whether an AttributeError is raised.

        """
        with pytest.raises(AttributeError):
            xml = owsutil.wfs_build_getfeature_request(
                'dov-pub:Boringen', bbox=(151650, 214675, 151750, 214775))

    def test_wfs_build_getfeature_request_bbox(self):
        """Test the owsutil.wfs_build_getfeature_request method with a
        typename, bbox and geometry_column.

        Test whether the XML of the WFS GetFeature call is generated correctly.

        """
        xml = owsutil.wfs_build_getfeature_request(
            'dov-pub:Boringen', bbox=(151650, 214675, 151750, 214775),
            geometry_column='geom')
        assert clean_xml(etree.tostring(xml).decode('utf8')) == clean_xml(
            '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'service="WFS" version="1.1.0" '
            'xsi:schemaLocation="http://www.opengis.net/wfs '
            'http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"><wfs:Query '
            'typeName="dov-pub:Boringen"><ogc:Filter '
            'xmlns:ogc="http://www.opengis.net/ogc"><ogc:Within> '
            '<ogc:PropertyName>geom</ogc:PropertyName><gml:Envelope '
            'xmlns:gml="http://www.opengis.net/gml" srsDimension="2" '
            'srsName="http://www.opengis.net/gml/srs/epsg.xml#31370"><gml'
            ':lowerCorner>151650.000 '
            '214675.000</gml:lowerCorner><gml:upperCorner>151750.000 '
            '214775.000</gml:upperCorner></gml:Envelope></ogc:Within></ogc'
            ':Filter></wfs:Query></wfs:GetFeature>')

    def test_wfs_build_getfeature_request_propertyname(self):
        """Test the owsutil.wfs_build_getfeature_request method with a list
        of propertynames.

        Test whether the XML of the WFS GetFeature call is generated correctly.

        """
        xml = owsutil.wfs_build_getfeature_request(
            'dov-pub:Boringen', propertyname=['fiche', 'diepte_tot_m'])
        assert clean_xml(etree.tostring(xml).decode('utf8')) == clean_xml(
            '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'service="WFS" version="1.1.0" '
            'xsi:schemaLocation="http://www.opengis.net/wfs '
            'http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"> <wfs:Query '
            'typeName="dov-pub:Boringen"> '
            '<wfs:PropertyName>fiche</wfs:PropertyName> '
            '<wfs:PropertyName>diepte_tot_m</wfs:PropertyName> <ogc:Filter/> '
            '</wfs:Query> </wfs:GetFeature>')

    def test_wfs_build_getfeature_request_filter(self):
        """Test the owsutil.wfs_build_getfeature_request method with an
        attribute filter.

        Test whether the XML of the WFS GetFeature call is generated correctly.

        """
        query = PropertyIsEqualTo(propertyname='gemeente',
                                  literal='Herstappe')
        filter_request = FilterRequest()
        filter_request = filter_request.setConstraint(query)
        try:
            filter_request = etree.tostring(filter_request,
                                            encoding='unicode')
        except LookupError:
            # Python2.7 without lxml uses 'utf-8' instead.
            filter_request = etree.tostring(filter_request,
                                            encoding='utf-8')

        xml = owsutil.wfs_build_getfeature_request(
            'dov-pub:Boringen', filter=filter_request)
        assert clean_xml(etree.tostring(xml).decode('utf8')) == clean_xml(
            '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'service="WFS" version="1.1.0" '
            'xsi:schemaLocation="http://www.opengis.net/wfs '
            'http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"> <wfs:Query '
            'typeName="dov-pub:Boringen"> <ogc:Filter> '
            '<ogc:PropertyIsEqualTo> '
            '<ogc:PropertyName>gemeente</ogc:PropertyName> '
            '<ogc:Literal>Herstappe</ogc:Literal> </ogc:PropertyIsEqualTo> '
            '</ogc:Filter> </wfs:Query> </wfs:GetFeature>')

    def test_wfs_build_getfeature_request_bbox_filter(self):
        """Test the owsutil.wfs_build_getfeature_request method with an
        attribute filter, a bbox and a geometry_column.

        Test whether the XML of the WFS GetFeature call is generated correctly.

        """
        query = PropertyIsEqualTo(propertyname='gemeente',
                                  literal='Herstappe')
        filter_request = FilterRequest()
        filter_request = filter_request.setConstraint(query)
        try:
            filter_request = etree.tostring(filter_request,
                                            encoding='unicode')
        except LookupError:
            # Python2.7 without lxml uses 'utf-8' instead.
            filter_request = etree.tostring(filter_request,
                                            encoding='utf-8')

        xml = owsutil.wfs_build_getfeature_request(
            'dov-pub:Boringen', filter=filter_request,
            bbox=(151650, 214675, 151750, 214775),
            geometry_column='geom')
        assert clean_xml(etree.tostring(xml).decode('utf8')) == clean_xml(
            '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'service="WFS" version="1.1.0" '
            'xsi:schemaLocation="http://www.opengis.net/wfs '
            'http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"> <wfs:Query '
            'typeName="dov-pub:Boringen"> <ogc:Filter> <ogc:And> '
            '<ogc:PropertyIsEqualTo> '
            '<ogc:PropertyName>gemeente</ogc:PropertyName> '
            '<ogc:Literal>Herstappe</ogc:Literal> </ogc:PropertyIsEqualTo> '
            '<ogc:Within> <ogc:PropertyName>geom</ogc:PropertyName> '
            '<gml:Envelope xmlns:gml="http://www.opengis.net/gml" '
            'srsDimension="2" '
            'srsName="http://www.opengis.net/gml/srs/epsg.xml#31370"> '
            '<gml:lowerCorner>151650.000 214675.000</gml:lowerCorner> '
            '<gml:upperCorner>151750.000 214775.000</gml:upperCorner> '
            '</gml:Envelope> </ogc:Within> </ogc:And> </ogc:Filter> '
            '</wfs:Query> </wfs:GetFeature>')

    def test_wfs_build_getfeature_request_bbox_filter_propertyname(self):
        """Test the owsutil.wfs_build_getfeature_request method with an
        attribute filter, a bbox, a geometry_column and a list of
        propertynames.

        Test whether the XML of the WFS GetFeature call is generated correctly.

        """
        query = PropertyIsEqualTo(propertyname='gemeente',
                                  literal='Herstappe')
        filter_request = FilterRequest()
        filter_request = filter_request.setConstraint(query)
        try:
            filter_request = etree.tostring(filter_request,
                                            encoding='unicode')
        except LookupError:
            # Python2.7 without lxml uses 'utf-8' instead.
            filter_request = etree.tostring(filter_request,
                                            encoding='utf-8')

        xml = owsutil.wfs_build_getfeature_request(
            'dov-pub:Boringen', filter=filter_request,
            bbox=(151650, 214675, 151750, 214775),
            geometry_column='geom', propertyname=['fiche', 'diepte_tot_m'])
        assert clean_xml(etree.tostring(xml).decode('utf8')) == clean_xml(
            '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'service="WFS" version="1.1.0" '
            'xsi:schemaLocation="http://www.opengis.net/wfs '
            'http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"> <wfs:Query '
            'typeName="dov-pub:Boringen"> '
            '<wfs:PropertyName>fiche</wfs:PropertyName> '
            '<wfs:PropertyName>diepte_tot_m</wfs:PropertyName> <ogc:Filter> '
            '<ogc:And> <ogc:PropertyIsEqualTo> '
            '<ogc:PropertyName>gemeente</ogc:PropertyName> '
            '<ogc:Literal>Herstappe</ogc:Literal> </ogc:PropertyIsEqualTo> '
            '<ogc:Within> <ogc:PropertyName>geom</ogc:PropertyName> '
            '<gml:Envelope xmlns:gml="http://www.opengis.net/gml" '
            'srsDimension="2" '
            'srsName="http://www.opengis.net/gml/srs/epsg.xml#31370"> '
            '<gml:lowerCorner>151650.000 214675.000</gml:lowerCorner> '
            '<gml:upperCorner>151750.000 214775.000</gml:upperCorner> '
            '</gml:Envelope> </ogc:Within> </ogc:And> </ogc:Filter> '
            '</wfs:Query> </wfs:GetFeature>')
