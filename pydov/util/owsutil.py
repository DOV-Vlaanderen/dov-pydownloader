# -*- coding: utf-8 -*-
"""Module grouping utility functions for OWS services."""
from owslib.feature.schema import (
    _get_describefeaturetype_url,
    _get_elements,
    _construct_schema,
    XS_NAMESPACE,
)

try:
    # Python3
    from urllib.parse import urlparse
except ImportError:
    # Python2
    from urlparse import urlparse

from owslib.etree import etree
from owslib.iso import MD_Metadata
from owslib.namespaces import Namespaces
from owslib.util import (
    openURL,
    nspath_eval,
    findall,
)

from pydov.util.errors import (
    MetadataNotFoundError,
    FeatureCatalogueNotFoundError,
)


def __get_namespaces():
    """Get default namespaces from OWSLib, extended with the 'gfc' namespace
    to be able to parse feature catalogues."""
    n = Namespaces()
    ns = n.get_namespaces()
    ns[None] = n.get_namespace("gmd")
    ns['gfc'] = 'http://www.isotc211.org/2005/gfc'
    return ns


__namespaces = __get_namespaces()


def __get_remote_md(md_url):
    """Request the remote metadata by calling the `md_url` and
    returning the response.

    Parameters
    ----------
    md_url : str
        URL to the remote metadata.

    Returns
    -------
    bytes
        Response containing the remote metadata.

    """
    return openURL(md_url).read()


def __get_remote_fc(fc_url):
    """Request the remote featurecatalogue by calling the `fc_url` and
    returning the response.

    Parameters
    ----------
    fc_url : str
        URL to the remote feature catalogue.

    Returns
    -------
    bytes
        Response containing the remote feature catalogue.

    """
    return openURL(fc_url).read()


def __get_remote_describefeaturetype(describefeaturetype_url):
    """Request the remote DescribeFeatureType by calling the
    `describefeaturetype_url` and returning the response.

    Parameters
    ----------
    describefeaturetype_url : str
        URL to the DescribeFeatureType.

    Returns
    -------
    bytes
        Response containing the remote DescribeFeatureType.

    """
    return openURL(describefeaturetype_url).read()


def get_remote_metadata(contentmetadata):
    """Request and parse the remote metadata associated with the layer
    described in `contentmetadata`.

    Parameters
    ----------
    contentmetadata : owslib.feature.wfs110.ContentMetadata
        Content metadata associated with a WFS layer, containing the
        associated `metadataUrls`.

    Returns
    -------
    owslib.iso.MD_Metadata
        Parsed remote metadata describing the WFS layer in more detail,
        in the ISO 19115/19139 format.

    Raises
    ------
    pydov.util.errors.MetadataNotFoundError
        If the `contentmetadata` has no valid metadata URL associated with it.

    """
    md_url = None
    for md in contentmetadata.metadataUrls:
        if md.get('url', None) is not None \
                and 'getrecordbyid' in md.get('url', "").lower():
            md_url = md.get('url')

    if md_url is None:
        raise MetadataNotFoundError

    content = __get_remote_md(md_url)
    doc = etree.fromstring(content)
    return MD_Metadata(doc)


def get_csw_base_url(contentmetadata):
    """Get the CSW base url for the remote metadata associated with the
    layer described in `contentmetadata`.

    Parameters
    ----------
    contentmetadata : owslib.feature.wfs110.ContentMetadata
        Content metadata associated with a WFS layer.

    Returns
    -------
    url : str
        Base URL of the CSW service where the remote metadata and feature
        catalogue can be requested.

    Raises
    ------
    pydov.util.errors.MetadataNotFoundError
        If the `contentmetadata` has no valid metadata URL associated with it.
    """
    md_url = None
    for md in contentmetadata.metadataUrls:
        if md.get('url', None) is not None \
                and 'getrecordbyid' in md.get('url', "").lower():
            md_url = md.get('url')

    if md_url is None:
        raise MetadataNotFoundError

    parsed_url = urlparse(md_url)
    return parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path


def get_featurecatalogue_uuid(md_metadata):
    """Get the UUID of the feature catalogue associated with the metadata.

    Parameters
    ----------
    md_metadata : owslib.iso.MD_Metadata
        Metadata parsed according to the ISO 19115/19139 format.

    Returns
    -------
    uuid : str
        Universally unique identifier of the feature catalogue associated
        with the metadata.

    Raises
    ------
    pydov.util.errors.FeatureCatalogueNotFoundError
        If there is no Feature Catalogue associated with the metadata or its
        UUID could not be retrieved.

    """
    tree = etree.fromstring(md_metadata.xml)

    citation = tree.find(nspath_eval(
        'gmd:MD_Metadata/gmd:contentInfo/gmd:MD_FeatureCatalogueDescription/'
        'gmd:featureCatalogueCitation', __namespaces))

    if citation is None:
        raise FeatureCatalogueNotFoundError

    uuid = citation.attrib.get('uuidref', None)
    if uuid is None:
        raise FeatureCatalogueNotFoundError

    return uuid


def get_remote_featurecatalogue(csw_url, fc_uuid):
    """Request and parse the remote feature catalogue described by the CSW
    base url and feature catalogue UUID.

    Parameters
    ----------
    csw_url : str
        Base URL of the CSW service to query, should end with 'csw'.
    fc_uuid : str
        Universally unique identifier of the feature catalogue.

    Returns
    -------
    dict
        Dictionary with fields described in the feature catalogue, using the
        following schema:

        >>>   {'definition' : 'feature type definition',
        >>>    'attributes' : {'name':
        >>>      {'definition' : 'attribute definition',
        >>>       'values' : ['list of', 'values'],
        >>>       'multiplicity': (lower, upper)}
        >>>    }
        >>>   }

        Where the lower multiplicity is always and integer and the upper
        multiplicity is either an integer or the str 'Inf' indicating an
        infinate value.

    Raises
    ------
    pydov.util.errors.FeatureCatalogueNotFoundError
        If there is no feature catalogue with given UUID available in the
        given CSW service.

    """
    fc_url = csw_url + '?Service=CSW&Request=GetRecordById&Version=2.0.2' \
                       '&outputSchema=http://www.isotc211.org/2005/gmd' \
                       '&elementSetName=full&id=' + fc_uuid

    content = __get_remote_fc(fc_url)
    tree = etree.fromstring(content)

    fc = tree.find(nspath_eval('gfc:FC_FeatureCatalogue', __namespaces))
    if fc is None:
        raise FeatureCatalogueNotFoundError

    r = {}
    r['definition'] = fc.findtext(nspath_eval(
        'gfc:featureType/gfc:FC_FeatureType/gfc:definition/'
        'gco:CharacterString', __namespaces))

    attributes = {}
    for a in fc.findall(nspath_eval(
            'gfc:featureType/gfc:FC_FeatureType/gfc:carrierOfCharacteristics/'
            'gfc:FC_FeatureAttribute', __namespaces)):
        attr = {}
        name = a.findtext(
            nspath_eval('gfc:memberName/gco:LocalName', __namespaces))
        attr['definition'] = a.findtext(nspath_eval(
            'gfc:definition/gco:CharacterString', __namespaces))

        try:
            multiplicity_lower = int(a.findtext(nspath_eval(
                'gfc:cardinality/gco:Multiplicity/gco:range/gco'
                ':MultiplicityRange/gco:lower/gco:Integer', __namespaces)))
        except (TypeError, ValueError):
            multiplicity_lower = 0

        upper = a.find(nspath_eval(
            'gfc:cardinality/gco:Multiplicity/gco:range/gco'
            ':MultiplicityRange/gco:upper/gco:UnlimitedInteger',
            __namespaces))

        try:
            multiplicity_upper = int(upper.text)
        except (TypeError, ValueError):
            multiplicity_upper = None

        if upper.get('isInfinite', 'false').lower() == 'true':
            multiplicity_upper = 'Inf'

        values = []
        for lv in a.findall(nspath_eval('gfc:listedValue/gfc:FC_ListedValue',
                                        __namespaces)):
            value = lv.findtext(nspath_eval('gfc:label/gco:CharacterString',
                                            __namespaces))
            if value is not None:
                values.append(value)
        attr['values'] = values
        attr['multiplicity'] = (multiplicity_lower, multiplicity_upper)
        attributes[name] = attr

    r['attributes'] = attributes
    return r


def get_namespace(wfs, layer):
    """Request the namespace associated with a layer by performing a
    DescribeFeatureType request.

    Parameters
    ----------
    wfs : owslib.wfs.WebFeatureService
        WFS service to use, associated with the layer.
    layer : str
        Workspace-qualified name of the layer to get the namespace of (
        typename).

    Returns
    -------
    namespace : str
        URI of the namespace associated with the given layer.

    """
    from owslib.feature.schema import _get_describefeaturetype_url
    url = _get_describefeaturetype_url(url=wfs.url, version='1.1.0',
                                       typename=layer)
    schema = __get_remote_describefeaturetype(url)
    tree = etree.fromstring(schema)
    namespace = tree.attrib.get('targetNamespace', None)
    return namespace


def get_remote_schema(url, typename, version='1.0.0'):
    """Copy the owslib.feature.schema.get_schema method to be able to
    monkeypatch the openURL request in tests.

    Parameters
    ----------
    url : str
        Base URL of the WFS service.
    typename : str
        Typename of the feature type to get the schema of.
    version : str
        Version of WFS to use. Defaults to 1.0.0


    Returns
    -------
    dict
        Schema of the given WFS layer.

    """
    url = _get_describefeaturetype_url(url, version, typename)
    res = __get_remote_describefeaturetype(url)
    root = etree.fromstring(res)

    if ':' in typename:
        typename = typename.split(':')[1]
    type_element = findall(root, '{%s}element' % XS_NAMESPACE,
                           attribute_name='name', attribute_value=typename)[0]
    complex_type = type_element.attrib['type'].split(":")[1]
    elements = _get_elements(complex_type, root)
    nsmap = None
    if hasattr(root, 'nsmap'):
        nsmap = root.nsmap
    return _construct_schema(elements, nsmap)
