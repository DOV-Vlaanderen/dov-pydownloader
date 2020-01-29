# -*- coding: utf-8 -*-
"""Module grouping utility functions for OWS services."""
import warnings

import pydov

from owslib.feature.schema import (
    _get_describefeaturetype_url,
    _get_elements,
    XS_NAMESPACE,
    GML_NAMESPACES
)
from owslib.fes import (
    UnaryLogicOpType,
    BinaryLogicOpType,
)

from urllib.parse import urlparse

from owslib.etree import etree
from owslib.iso import MD_Metadata
from owslib.namespaces import Namespaces
from owslib.util import (
    nspath_eval,
    findall,
)

from .errors import (
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
    return get_url(md_url)


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
    return get_url(fc_url)


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
    return get_url(describefeaturetype_url)


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

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
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
                       '&outputSchema=http://www.isotc211.org/2005/gfc' \
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

        values = {}
        for lv in a.findall(nspath_eval('gfc:listedValue/gfc:FC_ListedValue',
                                        __namespaces)):
            label = lv.findtext(nspath_eval('gfc:label/gco:CharacterString',
                                            __namespaces))
            definition = lv.findtext(nspath_eval(
                'gfc:definition/gco:CharacterString', __namespaces))

            if label is not None:
                label = label.strip()
                if label != '':
                    if definition is not None:
                        values[label] = definition.strip() if \
                            definition.strip() != '' else None
                    else:
                        values[label] = None

        attr['values'] = values if len(values) > 0 else None

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
    url = _get_describefeaturetype_url(url=wfs.url, version='2.0.0',
                                       typename=layer)
    schema = __get_remote_describefeaturetype(url)
    tree = etree.fromstring(schema)
    namespace = tree.attrib.get('targetNamespace', None)
    return namespace


def _construct_schema(elements, nsmap):
    """Copy the owslib.feature.schema.get_schema method to be able to get
    the geometry column name.

    Parameters
    ----------
    elements : list<Element>
        List of elements
    nsmap : dict
        Namespace map

    Returns
    -------
    dict
        Schema

    """
    schema = {
        'properties': {},
        'geometry': None
    }

    schema_key = None
    gml_key = None

    # if nsmap is defined, use it
    if nsmap:
        for key in nsmap:
            if nsmap[key] == XS_NAMESPACE:
                schema_key = key
            if nsmap[key] in GML_NAMESPACES:
                gml_key = key
    # if no nsmap is defined, we have to guess
    else:
        gml_key = 'gml'
        schema_key = 'xsd'

    mappings = {
        'PointPropertyType': 'Point',
        'PolygonPropertyType': 'Polygon',
        'LineStringPropertyType': 'LineString',
        'MultiPointPropertyType': 'MultiPoint',
        'MultiLineStringPropertyType': 'MultiLineString',
        'MultiPolygonPropertyType': 'MultiPolygon',
        'MultiGeometryPropertyType': 'MultiGeometry',
        'GeometryPropertyType': 'GeometryCollection',
        'SurfacePropertyType': '3D Polygon',
        'MultiSurfacePropertyType': '3D MultiPolygon'
    }

    for element in elements:
        data_type = element.attrib['type'].replace(gml_key + ':', '')
        name = element.attrib['name']

        if data_type in mappings:
            schema['geometry'] = mappings[data_type]
            schema['geometry_column'] = name
        else:
            schema['properties'][name] = data_type.replace(schema_key+':', '')

    if schema['properties'] or schema['geometry']:
        return schema
    else:
        return None


def get_remote_schema(url, typename, version='1.0.0'):
    """Copy the owslib.feature.schema.get_schema method to be able to
    monkeypatch the request in tests.

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
    type_element = findall(root, '{{{}}}element'.format(XS_NAMESPACE),
                           attribute_name='name', attribute_value=typename)[0]
    complex_type = type_element.attrib['type'].split(":")[1]
    elements = _get_elements(complex_type, root)
    nsmap = None
    if hasattr(root, 'nsmap'):
        nsmap = root.nsmap
    return _construct_schema(elements, nsmap)


def set_geometry_column(location, geometry_column):
    """Set the geometry column of the location query recursively.

    Parameters
    ----------
    location : pydov.util.location.AbstractLocationFilter or \
                owslib.fes.BinaryLogicOpType<AbstractLocationFilter> or \
                owslib.fes.UnaryLogicOpType<AbstractLocationFilter>
        Location filter limiting the features to retrieve. Can either be a
        single instance of a subclass of AbstractLocationFilter, or a
        combination using And, Or, Not of AbstractLocationFilters.
    geometry_column : str
        The name of the geometry column to query.

    Returns
    -------
    etree.Element
        XML element of this location filter.

    """
    if isinstance(location, UnaryLogicOpType) or \
            isinstance(location, BinaryLogicOpType):
        for i in location.operations:
            set_geometry_column(i, geometry_column)
    else:
        location.set_geometry_column(geometry_column)

    return location.toXML()


def wfs_build_getfeature_request(typename, geometry_column=None, location=None,
                                 filter=None, sort_by=None, propertyname=None,
                                 max_features=None, version='2.0.0'):
    """Build a WFS GetFeature request in XML to be used as payload in a WFS
    GetFeature request using POST.

    Parameters
    ----------
    typename : str
        Typename to query.
    geometry_column : str, optional
        Name of the geometry column to use in the spatial filter.
        Required if the ``location`` parameter is supplied.
    location : pydov.util.location.AbstractLocationFilter
        Location filter limiting the features to retrieve.
        Requires ``geometry_column`` to be supplied as well.
    filter : str of owslib.fes.FilterRequest, optional
        Filter request to search on attribute values.
    sort_by : str of owslib.fes.SortBy, optional
        List of properties to sort by.
    propertyname : list<str>, optional
        List of properties to return. Defaults to all properties.
    max_features : int
        Limit the maximum number of features to request.
    version : str, optional
        WFS version to use. Defaults to 1.1.0

    Raises
    ------
    AttributeError
        If ``bbox`` is given without ``geometry_column``.

    Returns
    -------
    element : etree.Element
        XML element representing the WFS GetFeature request.

    """
    if location is not None and geometry_column is None:
        raise AttributeError('location requires geometry_column and it is '
                             'None')

    xml = etree.Element('{http://www.opengis.net/wfs/2.0}GetFeature')
    xml.set('service', 'WFS')
    xml.set('version', version)

    if max_features is not None:
        if (not isinstance(max_features, int)) or (max_features <= 0):
            raise AttributeError('max_features should be a positive integer')
        xml.set('count', str(max_features))

    xml.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
            'http://www.opengis.net/wfs/2.0 '
            'http://schemas.opengis.net/wfs/{}/wfs.xsd'.format(version))

    query = etree.Element('{http://www.opengis.net/wfs/2.0}Query')
    query.set('typeNames', typename)

    if propertyname and len(propertyname) > 0:
        for property in propertyname:
            propertyname_xml = etree.Element(
                '{http://www.opengis.net/wfs/2.0}PropertyName')
            propertyname_xml.text = property
            query.append(propertyname_xml)

    filter_xml = etree.Element('{http://www.opengis.net/fes/2.0}Filter')
    filter_parent = filter_xml

    if filter is not None and location is not None:
        # if both filter and location are specified, we wrap them inside an
        # ogc:And
        and_xml = etree.Element('{http://www.opengis.net/fes/2.0}And')
        filter_xml.append(and_xml)
        filter_parent = and_xml

    if filter is not None:
        filterrequest = etree.fromstring(filter)
        filter_parent.append(filterrequest[0])

    if location is not None:
        location = set_geometry_column(location, geometry_column)
        filter_parent.append(location)

    query.append(filter_xml)

    if sort_by is not None:
        query.append(etree.fromstring(sort_by))

    xml.append(query)
    return xml


def wfs_get_feature(baseurl, get_feature_request):
    """Perform a WFS request using POST.

    Parameters
    ----------
    baseurl : str
        Base URL of the WFS service.
    get_feature_request : etree.Element
        XML element representing the WFS GetFeature request.

    Returns
    -------
    bytes
        Response of the WFS service.

    """
    data = etree.tostring(get_feature_request)

    request = pydov.session.post(baseurl, data, timeout=pydov.request_timeout)
    request.encoding = 'utf-8'
    return request.text.encode('utf8')


def get_url(url):
    """Perform a GET request to an OWS service an return the result.

    Parameters
    ----------
    url : str
        URL to request.

    Returns
    -------
    bytes
        Response containing the result of the GET request.

    """

    request = pydov.session.get(url, timeout=pydov.request_timeout)
    request.encoding = 'utf-8'
    return request.text.encode('utf8')
