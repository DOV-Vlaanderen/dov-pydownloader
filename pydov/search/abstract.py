# -*- coding: utf-8 -*-
"""Module containing the abstract search classes to retrieve DOV data."""
import datetime
from distutils.util import strtobool

import owslib
import pydov
from owslib.etree import etree
from owslib.fes import (
    FilterRequest,
)
from owslib.wfs import WebFeatureService
from pydov.util import owsutil
from pydov.util.dovutil import (
    get_xsd_schema,
    build_dov_url,
)
from pydov.util.errors import (
    LayerNotFoundError,
    InvalidSearchParameterError,
    FeatureOverflowError,
    InvalidFieldError,
    WfsGetFeatureError,
)
from ..util.owsutil import get_remote_schema


class AbstractCommon(object):
    """Class grouping methods common to AbstractSearch and
    AbstractTypeCommon."""

    @classmethod
    def _typeconvert(cls, text, returntype):
        """Parse the text to the given returntype.

        Parameters
        ----------
        text : str
           Text to convert
        returntype : str
            Parse the text to this output datatype. One of
            `string`, `float`, `integer`, `date`, `datetime`, `boolean`.

        Returns
        -------
        str or float or int or bool or datetime.date or datetime.datetime
            Returns the parsed text converted to the type described by
            `returntype`.

        """
        if returntype == 'string':
            def typeconvert(x):
                return u'' + (x.strip())
        elif returntype == 'integer':
            def typeconvert(x):
                return int(x)
        elif returntype == 'float':
            def typeconvert(x):
                return float(x)
        elif returntype == 'date':
            def typeconvert(x):
                # Patch for Zulu-time issue of geoserver for WFS 1.1.0
                if x.endswith('Z'):
                    return datetime.datetime.strptime(x, '%Y-%m-%dZ').date() \
                           + datetime.timedelta(days=1)
                else:
                    return datetime.datetime.strptime(x, '%Y-%m-%d').date()
        elif returntype == 'datetime':
            def typeconvert(x):
                if x.endswith('Z'):
                    return datetime.datetime.strptime(
                            x, '%Y-%m-%dT%H:%M:%SZ').date() \
                           + datetime.timedelta(days=1)
                else:
                    return datetime.datetime.strptime(
                        x.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        elif returntype == 'boolean':
            def typeconvert(x):
                return strtobool(x) == 1
        else:
            def typeconvert(x):
                return x

        return typeconvert(text)


class AbstractSearch(AbstractCommon):
    """Abstract search class grouping methods common to all DOV search
    classes. Not to be instantiated or used directly."""

    __wfs = None

    def __init__(self, layer, objecttype):
        """Initialisation.

        Parameters
        ----------
        layer : str
            WFS layer to use for searching and retrieving records.
        objecttype : pydov.types.AbstractDovType
            Subclass of AbstractDovType indicating the associated DOV datatype.

        """
        self._layer = layer
        self._type = objecttype

        self._fields = None
        self._wfs_fields = None
        self._geometry_column = None

        self._map_wfs_source_df = {}
        self._map_df_wfs_source = {}

    def _init_wfs(self):
        """Initialise the WFS service. If the WFS service is not
        instanciated yet, do so and save it in a static variable available
        to all subclasses and instances.
        """
        if AbstractSearch.__wfs is None:
            AbstractSearch.__wfs = WebFeatureService(
                url=build_dov_url('geoserver/wfs'), version="2.0.0")

    def _init_namespace(self):
        """Initialise the WFS namespace associated with the layer.

        Raises
        ------
        NotImplementedError
            This is an abstract method that should be implemented in a
            subclass.

        """
        raise NotImplementedError('This should be implemented in a subclass.')

    def _init_fields(self):
        """Initialise the fields and their metadata available in this search
        class.

        Raises
        ------
        NotImplementedError
            This is an abstract method that should be implemented in a
            subclass.

        """
        raise NotImplementedError('This should be implemented in a subclass.')

    def _get_layer(self):
        """Get the WFS metadata for the layer.

        Returns
        -------
        owslib.feature.wfs110.ContentMetadata
            Content metadata describing the layer.

        Raises
        ------
        pydov.util.errors.LayerNotFoundError
            When the layer of this search class could not be found in the
            associated WFS service.

        """
        self._init_wfs()

        if self._layer not in self.__wfs.contents:
            raise LayerNotFoundError(
                'Layer {} could not be found'.format(self._layer))
        else:
            return self.__wfs.contents[self._layer]

    def _get_schema(self):
        """Get the WFS schema (i.e. the output of the DescribeFeatureType
        request) of the layer.

        Returns
        -------
        schema : dict
            Schema associated with the layer.

        """
        self._init_wfs()
        layername = self._layer.split(':')[1] if ':' in self._layer else \
            self._layer
        return get_remote_schema(
            build_dov_url('geoserver/wfs'), layername, '2.0.0')

    def _get_namespace(self):
        """Get the WFS namespace of the layer.

        Returns
        -------
        namespace : str
            The namespace associated with the WFS layer. This is the
            namespace of the fields of this layer, needed to parse the
            output of a GetFeature request.

        """
        self._init_wfs()
        return owsutil.get_namespace(self.__wfs, self._layer)

    def _get_remote_metadata(self):
        """Request and parse the remote metadata associated with the layer.

        Returns
        -------
        owslib.iso.MD_Metadata
            Parsed remote metadata describing the WFS layer in more detail,
            in the ISO 19115/19139 format.

        """
        wfs_layer = self._get_layer()
        return owsutil.get_remote_metadata(wfs_layer)

    def _get_remote_xsd_schemas(self):
        """Request and parse the remote XSD schemas associated with this type.

        Returns
        -------
        list of etree.ElementTree
            List of parsed XSD schemas associated with this type.

        """
        return [etree.fromstring(get_xsd_schema(i)) for i in
                self._type.get_xsd_schemas()]

    def _get_csw_base_url(self):
        """Get the CSW base url for the remote metadata associated with the
        layer.

        Returns
        -------
        url : str
            Base URL of the CSW service where the remote metadata and feature
            catalogue can be requested.

        """
        wfs_layer = self._get_layer()
        return owsutil.get_csw_base_url(wfs_layer)

    @classmethod
    def _get_xsd_enum_values(cls, xsd_schemas, xml_field):
        """Get the distinct enum values from XSD schemas for a given XML field.

        Depending of the 'xsd_type' of the XML field, retrieve the distinct
        enum values and definitions from the XSD schemas.

        Parameters
        ----------
        xsd_schemas : list of etree.ElementTree
            List of parsed XSD schemas.
        xml_field : dict
            Dictionary describing the XML field, including a 'xsd_type' key
            linking the type to the enum type in (one of) the XSD schemas.

        Returns
        -------
        values : dict
            Dictionary containing the enum values as keys (in the datatype
            of the XML field) and the definitions as values.

        """
        values = None
        if xml_field.get('xsd_type', None):
            values = {}
            for schema in xsd_schemas:
                tree_values = schema.findall(
                    './/{{http://www.w3.org/2001/XMLSchema}}simpleType['
                    '@name="{}"]/'
                    '{{http://www.w3.org/2001/XMLSchema}}restriction/'
                    '{{http://www.w3.org/2001/XMLSchema}}enumeration'.format(
                        xml_field.get('xsd_type')))
                for e in tree_values:
                    value = cls._typeconvert(
                        e.get('value'), xml_field.get('type'))
                    values[value] = e.findtext(
                        './{http://www.w3.org/2001/XMLSchema}annotation/{'
                        'http://www.w3.org/2001/XMLSchema}documentation')
        return values

    def _build_fields(self, wfs_schema, feature_catalogue, xsd_schemas):
        """Build the dictionary containing the metadata about the available
        fields.

        Parameters
        ----------
        wfs_schema : dict
            The schema associated with the WFS layer.
        feature_catalogue : dict
            Dictionary with fields described in the feature catalogue,
            as returned by pydov.util.owsutil.get_remote_featurecatalogue.

        Returns
        -------
        fields : dict<str,dict>
            Dictionary containing the metadata of the available fields,
            where the metadata dictionary includes:

            name (str)
                The name of the field.

            definition (str)
                The definition of the field.

            type (str)
                The datatype of the field.

            notnull (boolean)
                Whether the field is mandatory (True) or can be null (False).

            cost (integer)
                The cost associated with the request of this field in the
                output dataframe.

        Raises
        ------
        RuntimeError
            When the defined fields of this type are invalid.

        """
        fields = {}
        self._wfs_fields = []
        self._geometry_column = wfs_schema.get('geometry_column', None)

        for f in self._type.get_fields(include_subtypes=False).values():
            if not isinstance(f, pydov.types.fields.AbstractField):
                raise RuntimeError(
                    "Type '{}' fields should be instances of "
                    "pydov.types.fields.AbstractField, found {}.".format(
                        self._type.__name__, str(type(f))))

        for f in self._type.get_fields(include_subtypes=True).values():
            if not isinstance(f, pydov.types.fields.AbstractField):
                raise RuntimeError(
                    "Fields of subtype of '{}' should be instances of "
                    "pydov.types.fields.AbstractField, found {}.".format(
                        self._type.__name__, str(type(f))))

        _map_wfs_datatypes = {
            'int': 'integer',
            'decimal': 'float',
            'double': 'float',
            'dateTime': 'datetime'
        }

        df_wfs_fields = self._type.get_fields(source=('wfs',)).values()
        for f in df_wfs_fields:
            self._map_wfs_source_df[f['sourcefield']] = f['name']
            self._map_df_wfs_source[f['name']] = f['sourcefield']

        for wfs_field in wfs_schema['properties'].keys():
            if wfs_field in feature_catalogue['attributes']:
                fc_field = feature_catalogue['attributes'][wfs_field]
                self._wfs_fields.append(wfs_field)

                name = self._map_wfs_source_df.get(wfs_field, wfs_field)

                field = {
                    'name': name,
                    'definition': fc_field['definition'],
                    'type': _map_wfs_datatypes.get(
                        wfs_schema['properties'][wfs_field],
                        wfs_schema['properties'][wfs_field]),
                    'notnull': fc_field['multiplicity'][0] > 0,
                    'query': True,
                    'cost': 1
                }

                if fc_field['values'] is not None:
                    field['values'] = fc_field['values']

                fields[name] = field

        for xml_field in self._type.get_fields(source=['xml']).values():
            field = {
                'name': xml_field['name'],
                'type': xml_field['type'],
                'definition': xml_field['definition'],
                'notnull': xml_field['notnull'],
                'query': False,
                'cost': 10
            }

            values = self._get_xsd_enum_values(xsd_schemas, xml_field)
            if values is not None:
                field['values'] = values

            fields[field['name']] = field

        for custom_field in self._type.get_fields(source=['custom']).values():
            field = {
                'name': custom_field['name'],
                'type': custom_field['type'],
                'definition': custom_field['definition'],
                'notnull': custom_field['notnull'],
                'query': False,
                'cost': 1
            }
            fields[field['name']] = field

        return fields

    def _pre_search_validation(self, location, query, sort_by,
                               return_fields, max_features):
        """Perform validation on the parameters of the search query.

        Parameters
        ----------
        location : pydov.util.location.AbstractLocationFilter
            Location filter limiting the features to retrieve.
        query : owslib.fes.OgcExpression
            OGC filter expression to use for searching. This can contain any
            combination of filter elements defined in owslib.fes. The query
            should use the fields provided in `get_fields()`. Note that not
            all fields are currently supported as a search parameter.
        sort_by : owslib.fes.SortBy, optional
            List of properties to sort by.
        return_fields : list<str> or tuple<str> or set<str>
            A list of fields to be returned in the output data. This should
            be a subset of the fields provided in `get_fields()`.
        max_features : int
            Limit the maximum number of features to request.

        Raises
        ------
        pydov.util.errors.InvalidSearchParameterError
            When not one of `location`, `query` or `max_features` is provided.

        pydov.util.errors.InvalidFieldError
            When at least one of the fields in `return_fields` is unknown.

            When a field that is only accessible as return field is used as
            a query parameter.

        """
        if location is None and query is None and max_features is None:
            raise InvalidSearchParameterError(
                'Provide either the location or the query parameter or the '
                'max_features parameter.'
            )

        if query is not None:
            if not isinstance(query, owslib.fes.OgcExpression):
                raise InvalidSearchParameterError(
                    "Query should be an owslib.fes.OgcExpression.")

            filter_request = FilterRequest()
            filter_request = filter_request.setConstraint(query)

            self._init_fields()
            for property_name in filter_request.findall(
                    './/{http://www.opengis.net/ogc}PropertyName'):
                name = property_name.text
                if name not in self._map_df_wfs_source \
                        and name not in self._wfs_fields:
                    if name in self._fields:
                        raise InvalidFieldError(
                            "Cannot use return field '{}' in query.".format(
                                name))
                    raise InvalidFieldError(
                        "Unknown query parameter: '{}'".format(name))

        if location is not None:
            self._init_fields()

        if sort_by is not None:
            if not isinstance(sort_by, owslib.fes.SortBy):
                raise InvalidSearchParameterError(
                    "SortBy should be an owslib.fes.SortBy")

            self._init_fields()
            for property_name in sort_by.toXML().findall(
                    './/{http://www.opengis.net/ogc}PropertyName'):
                name = property_name.text
                if name not in self._map_df_wfs_source \
                        and name not in self._wfs_fields:
                    if name in self._fields:
                        raise InvalidFieldError(
                            "Cannot use return field '{}' for sorting.".format(
                                name))
                    raise InvalidFieldError(
                        "Unknown query parameter: '{}'".format(name))

        if return_fields is not None:
            if type(return_fields) not in (list, tuple, set):
                raise AttributeError('return_fields should be a list, '
                                     'tuple or set')

            self._init_fields()
            for rf in return_fields:
                if rf not in self._fields:
                    if rf in self._map_wfs_source_df:
                        raise InvalidFieldError(
                            "Unknown return field: "
                            "'{}'. Did you mean '{}'?".format(
                                rf, self._map_wfs_source_df[rf]))
                    if rf.lower() in [i.lower() for i in
                                      self._map_wfs_source_df.keys()]:
                        sugg = [i for i in self._map_wfs_source_df.keys() if
                                i.lower() == rf.lower()][0]
                        raise InvalidFieldError(
                            "Unknown return field: "
                            "'{}'. Did you mean '{}'?".format(rf, sugg))
                    raise InvalidFieldError(
                        "Unknown return field: '{}'".format(rf))

    @staticmethod
    def _get_remote_wfs_feature(wfs, typename, location, filter,
                                sort_by, propertyname, max_features,
                                geometry_column):
        """Perform the WFS GetFeature call to get features from the remote
        service.

        Parameters
        ----------
        typename : str
            Layername to query.
        location : pydov.util.location.AbstractLocationFilter
            Location filter limiting the features to retrieve.
        filter : str of owslib.fes.FilterRequest
            Filter request to search on attribute values.
        sort_by : str of owslib.fes.SortBy, optional
            List of properties to sort by.
        propertyname : list<str>
            List of properties to return.
        max_features : int
            Limit the maximum number of features to request.
        geometry_column : str
            Name of the geometry column to use in the spatial filter.

        Returns
        -------
        bytes
            Response of the WFS service.

        """
        breakpoint()
        wfs_getfeature_xml = owsutil.wfs_build_getfeature_request(
            version=wfs.version,
            geometry_column=geometry_column,
            typename=typename,
            location=location,
            filter=filter,
            sort_by=sort_by,
            max_features=max_features,
            propertyname=propertyname
        )

        for hook in pydov.hooks:
            hook.wfs_search_init(typename)

        return owsutil.wfs_get_feature(
            baseurl=wfs.url,
            get_feature_request=wfs_getfeature_xml
        )

    def _search(self, location=None, query=None, return_fields=None,
                sort_by=None, max_features=None, extra_wfs_fields=[]):
        """Perform the WFS search by issuing a GetFeature request.

        Parameters
        ----------
        location : pydov.util.location.AbstractLocationFilter
            Location filter limiting the features to retrieve.
        query : owslib.fes.OgcExpression
            OGC filter expression to use for searching. This can contain any
            combination of filter elements defined in owslib.fes. The query
            should use the fields provided in `get_fields()`. Note that not
            all fields are currently supported as a search parameter.
        return_fields : list<str>
            A list of fields to be returned in the output data. This should
            be a subset of the fields provided in `get_fields()`. Note that
            not all fields are currently supported as return fields.
        sort_by : owslib.fes.SortBy, optional
            List of properties to sort by.
        max_features : int
            Limit the maximum number of features to request.
        extra_wfs_fields: list<str>
            A list of extra fields to be included in the WFS requests,
            regardless whether they're needed as return field. Optional,
            defaults to an empty list.

        Returns
        -------
        etree.Element
            XML tree of the WFS response containing the features matching
            the location or the query.

        Raises
        ------
        pydov.util.errors.InvalidSearchParameterError
            When not one of `location`, `query` or `max_features` is provided.

        pydov.util.errors.InvalidFieldError
            When at least one of the fields in `return_fields` is unknown.

            When a field that is only accessible as return field is used as
            a query parameter.

            When a field that can only be used as a query parameter is used as
            a return field.

        pydov.util.errors.FeatureOverflowError
            When the number of features to be returned is equal to the
            maxFeatures limit of the WFS server.

        """
        self._pre_search_validation(location, query, sort_by, return_fields,
                                    max_features)
        self._init_namespace()
        self._init_wfs()

        filter_request = None
        if query is not None:
            filter_request = FilterRequest()
            filter_request = filter_request.setConstraint(query)

        if filter_request is not None:
            for property_name in filter_request.findall(
                    './/{http://www.opengis.net/ogc}PropertyName'):
                property_name.text = self._map_df_wfs_source.get(
                    property_name.text, property_name.text)

            filter_request = etree.tostring(filter_request, encoding='unicode')

        if return_fields is None:
            wfs_property_names = [
                f['sourcefield'] for f in self._type.get_fields(
                    source=('wfs',)).values() if not f.get(
                    'wfs_injected', False)]
        else:
            wfs_property_names = [self._map_df_wfs_source[i]
                                  for i in self._map_df_wfs_source
                                  if i.startswith('pkey')]
            wfs_property_names.extend([self._map_df_wfs_source[i]
                                       for i in self._map_df_wfs_source
                                       if i in return_fields])

        wfs_property_names.extend(extra_wfs_fields)
        wfs_property_names = list(set(wfs_property_names))

        if sort_by is not None:
            sort_by_xml = sort_by.toXML()
            for property_name in sort_by_xml.findall(
                    './/{http://www.opengis.net/ogc}PropertyName'):
                property_name.text = self._map_df_wfs_source.get(
                    property_name.text, property_name.text)

            sort_by = etree.tostring(sort_by_xml, encoding='unicode')

        fts = self._get_remote_wfs_feature(
            wfs=self.__wfs,
            typename=self._layer,
            location=location,
            filter=filter_request,
            sort_by=sort_by,
            max_features=max_features,
            propertyname=wfs_property_names,
            geometry_column=self._geometry_column)

        tree = etree.fromstring(fts)

        if tree.get('numberOfFeatures') is None:
            raise WfsGetFeatureError(
                'Error retrieving features from DOV WFS server:\n{}'.format(
                    etree.tostring(tree).decode('utf8')))

        if int(tree.get('numberOfFeatures')) == 10000:
            raise FeatureOverflowError(
                'Reached the limit of {:d} returned features. Please split up '
                'the query to ensure getting all results.'.format(10000))

        for hook in pydov.hooks:
            hook.wfs_search_result(int(tree.get('numberOfFeatures')))

        return tree

    def get_description(self):
        """Get the description of this search layer.

        Returns
        -------
        str
            The description of this layer.

        """
        wfs_layer = self._get_layer()
        return wfs_layer.abstract

    def get_fields(self):
        """Get the metadata of the fields that are available.

        Returns
        -------
        fields : dict<str,dict>
            Dictionary containing the metadata of the available fields,
            where the metadata dictionary includes:

            name (str)
                The name of the field.

            definition (str)
                The definition of the field.

            type (str)
                The datatype of the field.

            notnull (boolean)
                Whether the field is mandatory (True) or can be null (False).

            query (boolean)
                Whether the field can be used in an attribute query.

            cost (integer)
                The cost associated with the request of this field in the
                output dataframe.

            Optionally, it can contain:

            values (list)
                A list of possible values for this field.

        """
        self._init_fields()
        return self._fields

    def search(self, location=None, query=None,
               sort_by=None, return_fields=None, max_features=None):
        """Search for objects of this type. Provide `location` and/or
        `query` and/or `max_features`.
        When `return_fields` is None, all fields are returned.

        Parameters
        ----------
        location : pydov.util.location.AbstractLocationFilter or \
                   owslib.fes.BinaryLogicOpType<AbstractLocationFilter> or \
                   owslib.fes.UnaryLogicOpType<AbstractLocationFilter>
            Location filter limiting the features to retrieve. Can either be a
            single instance of a subclass of AbstractLocationFilter, or a
            combination using And, Or, Not of AbstractLocationFilters.
        query : owslib.fes.OgcExpression
            OGC filter expression to use for searching. This can contain any
            combination of filter elements defined in owslib.fes. The query
            should use the fields provided in `get_fields()`. Note that not
            all fields are currently supported as a search parameter.
        sort_by : owslib.fes.SortBy, optional
            List of properties to sort by.
        return_fields : list<str> or tuple<str> or set<str>
            A list of fields to be returned in the output data. This should
            be a subset of the fields provided in `get_fields()`. Note that
            not all fields are currently supported as return fields.
        max_features : int
            Limit the maximum number of features to request.

        Returns
        -------
        pandas.core.frame.DataFrame
            DataFrame containing the output of the search query.

        Raises
        ------
        pydov.util.errors.InvalidSearchParameterError
            When not one of `location` or `query` or `max_features` is
            provided.

        pydov.util.errors.InvalidFieldError
            When at least one of the fields in `return_fields` is unknown.

            When a field that is only accessible as return field is used as
            a query parameter.

            When a field that can only be used as a query parameter is used as
            a return field.

        pydov.util.errors.FeatureOverflowError
            When the number of features to be returned is equal to the
            maxFeatures limit of the WFS server.

        AttributeError
            When the argument supplied as return_fields is not a list,
            tuple or set.

        """
        raise NotImplementedError
