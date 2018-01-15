# -*- coding: utf-8 -*-
"""Module containing the base DOV data types."""

import datetime
import types
from collections import OrderedDict
from distutils.util import strtobool

from owslib.etree import etree
from owslib.util import openURL

from pydov.util.errors import InvalidFieldError


class AbstractCommon(object):
    """Class grouping methods common to AbstractDovType and
    AbstractDovSubType."""

    def _parse_xml_data(self):
        """Get remote XML data for this DOV object, parse the raw XML and
        save the results in the data object.

        Raises
        ------
        NotImplementedError
            This is an abstract method that should be implemented in a
            subclass.

        """
        raise NotImplementedError('This should be implemented in a subclass.')

    @classmethod
    def _parse(cls, func, xpath, namespace, returntype):
        """Parse the result of an XML path function, stripping the namespace
        and adding type conversion.

        Parameters
        ----------
        func : reference to function
           Function to call.
        xpath : str
            XML path of the element, used as the argument of `func`.
        namespace : str or None
            Namespace to be added to each item in the `xpath`. None to use
            the xpath as is.
        returntype : str
            Parse the text found with `func` to this output datatype. One of
            `string`, `float`, `integer`, `date`, `boolean`.

        Returns
        -------
        str or float or int or datetime.date
            Returns the parsed value of the output from calling `func` on
            `xpath`, converted to the type described by `returntype`.

        """
        if returntype == 'string':
            def typeconvert(x):
                return str(x).strip()
        elif returntype == 'integer':
            def typeconvert(x):
                return int(x)
        elif returntype == 'float':
            def typeconvert(x):
                return float(x)
        elif returntype == 'date':
            def typeconvert(x):
                return datetime.datetime.strptime(x, '%Y-%m-%dZ').date() + \
                       datetime.timedelta(days=1)
        elif returntype == 'boolean':
            def typeconvert(x):
                return strtobool(x) == 1
        else:
            def typeconvert(x):
                return x

        if namespace is not None:
            ns = '{%s}' % namespace
            text = func('./' + ns + ('/' + ns).join(xpath.split('/')))
        else:
            text = func('./' + xpath.lstrip('/'))

        if text is None:
            return None
        return typeconvert(text)


class AbstractDovSubType(AbstractCommon):

    _name = None
    _rootpath = None

    _UNRESOLVED = "{UNRESOLVED}"
    _fields = []

    def __init__(self, name):
        """Initialisation.

        Parameters
        ----------
        name : str
            The name associated with this subtype.

        """
        self._name = name

        self.data = dict(
            zip(self.get_field_names(),
                [AbstractDovSubType._UNRESOLVED] * len(self.get_field_names()))
        )

    @classmethod
    def from_xml(cls, xml_data):
        """Build instances of this subtype from XML data.

        Parameters
        ----------
        xml_data : bytes
            Raw XML data of the DOV object that contains information about
            this subtype.

        Yields
        ------
            An instance of this type for each occurence of the rootpath in
            the XML document.

        """
        tree = etree.fromstring(xml_data)
        for element in tree.findall(cls._rootpath):
            yield cls.from_xml_element(element)

    @classmethod
    def from_xml_element(cls, element):
        """Build an instance of this subtype from a single XML element.

        Parameters
        ----------
        element : etree.Element
            XML element representing a single record of this subtype.

        Raises
        ------
        NotImplementedError
            This is an abstract method that should be implemented in a
            subclass.

        """
        raise NotImplementedError('This should be implemented in a subclass.')

    @classmethod
    def get_field_names(cls):
        """Return the names of the fields available for this type.

        Returns
        -------
        list<str>
            List of the field names available for this type. These are also
            the names of the columns in the output dataframe for this type.

        """
        return [f['name'] for f in cls._fields]

    @classmethod
    def get_fields(cls):
        """Return the metadata of the fields available for this type.

        Returns
        -------
        collections.OrderedDict<str,dict>
            Ordered dictionary mapping the field (column) name to the
            dictionary containing the metadata of this field.

            This metadata dictionary includes at least:

            name (str)
                The name of the field in the output data.

            source (str)
                The source of the field (either `wfs` or `xml`).

            sourcefield (str)
                The name of the field in the source (source + sourcefield
                identify the origin of the data).

            type (str)
                Datatype of the output data field (one of `string`, `float`,
                `integer`, `date`, `datetime`).

            definition (str)
                The definition of the field.

            notnull (boolean)
                Whether the field is mandatory (True) or can be null (False).

        """
        return OrderedDict(
            zip([f['name'] for f in cls._fields],
                [f for f in cls._fields]))

    @classmethod
    def get_name(cls):
        """Return the name associated with this subtype.

        Returns
        -------
        name : str
            The name associated with this subtype.

        """
        return cls._name

    @classmethod
    def get_root_path(cls):
        """Return the root XPath of the XML element of this subtype.

        Returns
        -------
        xpath : str
            The XPath of the XML root element of this subtype.

        """
        return cls._rootpath


class AbstractDovType(AbstractCommon):
    """Abstract DOV type grouping fields and methods common to all DOV
    object types. Not to be instantiated or used directly."""

    _subtypes = []

    _UNRESOLVED = "{UNRESOLVED}"
    _fields = []

    def __init__(self, typename, pkey):
        """Initialisation.

        Parameters
        ----------
        typename : str
            Name of the DOV object type.
        pkey : str
            Permanent key of this DOV object, being a URI of the form
            `https://www.dov.vlaanderen.be/data/typename/id`.

        """
        self.typename = typename
        self.pkey = pkey

        self.data = dict(
            zip(self.get_field_names(include_subtypes=False),
                [AbstractDovType._UNRESOLVED] * len(self.get_field_names()))
        )

        self.subdata = dict(
            zip([st.get_name() for st in self._subtypes],
                [] * len(self._subtypes))
        )

        self.data['pkey_%s' % self.typename] = self.pkey

    @classmethod
    def from_wfs_element(cls, feature, namespace):
        """Build an instance of this type from a WFS feature element.

        Parameters
        ----------
        feature : etree.Element
            XML element representing a single record of the WFS layer.
        namespace : str
            Namespace associated with this WFS featuretype.

        Raises
        ------
        NotImplementedError
            This is an abstract method that should be implemented in a
            subclass.

        """
        raise NotImplementedError('This should be implemented in a subclass.')

    @classmethod
    def from_wfs(cls, response, namespace):
        """Build instances of this type from a WFS response.

        Parameters
        ----------
        response : str or bytes or etree.Element or iterable<etree.Element>
            WFS response containing GML features.

            Can either be a GML `str` or `byte` sequence, in which case it
            will be parsed and scanned for `gml:featureMembers`.

            Can also be a single instance of `etree.Element` containing the
            parsed GML response.

            It can also be an iterable (list, tuple or generator) of
            `etree.Element` in which case it will be looped over.
        namespace : str
             Namespace associated with this WFS featuretype.

        Yields
        ------
            An instance of this type for each record in the WFS response.

        """
        if type(response) is str:
            response = response.encode('utf-8')

        if type(response) is bytes:
            response = etree.fromstring(response)

        element_type = type(etree.Element(b'xml'))
        if isinstance(response, element_type):
            feature_members = response.find('.//{http://www.opengis.net/gml}'
                                            'featureMembers')

            if feature_members is not None:
                for ft in feature_members:
                    yield (cls.from_wfs_element(ft, namespace))

        if type(response) in (list, tuple, set) \
                or isinstance(response, types.GeneratorType):
            for el in response:
                yield (cls.from_wfs_element(el, namespace))

    @classmethod
    def get_field_names(cls, return_fields=None, include_subtypes=True):
        """Return the names of the fields available for this type.

        Parameters
        ----------
        return_fields : list<str> or tuple<str> or set<str>
            List of fields to include in the data array. The order is
            ignored, the default order of the fields of the datatype is used
            instead. Defaults to None, which will include all fields.
        include_subtypes : boolean
            Whether to include fields defined in subtypes (True) or not (
            False). Defaults to True.

        Returns
        -------
        list<str>
            List of the field names available for this type. These are also
            the names of the columns in the output dataframe for this type.

        Raises
        ------
        AttributeError
            If the type of `return_fields` is not one of None, list, tuple or
            set.
        pydov.util.errors.InvalidFieldError
            If at least one of the fields listed in `return_fields` is unknown.

        """
        if return_fields is None:
            fields = [f['name'] for f in cls._fields]
            if include_subtypes:
                for st in cls._subtypes:
                    fields.extend(st.get_field_names())
        elif type(return_fields) not in (list, tuple, set):
            raise AttributeError(
                'return_fields should be a list, tuple or set')
        else:
            fields = [f['name'] for f in cls._fields if f['name'] in
                      return_fields]
            if include_subtypes:
                for st in cls._subtypes:
                    fields.extend([f for f in st.get_field_names() if f in
                                   return_fields])
            for rf in return_fields:
                if rf not in fields:
                    raise InvalidFieldError("Unkown return field: '%s'" % rf)
        return fields

    @classmethod
    def get_fields(cls, source=('wfs', 'xml'), include_subtypes=True):
        """Return the metadata of the fields available for this type.

        Parameters
        ----------
        source : list<str> or tuple<str> or iterable<str>
            A list of sources to include in the output. Can either be `wfs` or
            `xml` or `wfs, xml`.
        include_subtypes : boolean
            Whether to include fields defined in subtypes (True) or not (
            False). Defaults to True.

        Returns
        -------
        collections.OrderedDict<str,dict>
            Ordered dictionary mapping the field (column) name to the
            dictionary containing the metadata of this field.

            This metadata dictionary includes at least:

            name (str)
                The name of the field in the output data.

            source (str)
                The source of the field (either `wfs` or `xml`).

            sourcefield (str)
                The name of the field in the source (source + sourcefield
                identify the origin of the data).

            type (str)
                Datatype of the output data field (one of `string`, `float`,
                `integer`, `date`, `datetime`, `boolean`).

            The metadata dictionary additionally includes for fields with
            source `xml`:

            definition (str)
                The definition of the field.

            notnull (boolean)
                Whether the field is mandatory (True) or can be null (False).

        """
        fields = OrderedDict(
            zip([f['name'] for f in cls._fields if f['source'] in source],
                [f for f in cls._fields if f['source'] in source]))

        if include_subtypes and 'xml' in source:
            for st in cls._subtypes:
                fields.update(st.get_fields())

        return fields

    @classmethod
    def to_df_array(cls, iterable, return_fields=None):
        """Yield one or more dataframe arrays for each instance in the given
        iterable.

        Parameters
        ----------
        iterable : list<DovType> or tuple<DovType> or iterable<DovType>
            A list of instances of a DOV type.
        return_fields : list<str> or tuple<str> or set<str> or iterable<str>
            List of fields to include in the data array. The order is
            ignored, the default order of the fields of the datatype is used
            instead. Defaults to None, which will include all fields.

        Yields
        ------
        list
            List of the values of the instance in the same order as the
            field/column names, for inclusion in the result dataframe of a
            search operation.

        """
        for item in iterable:
            result = item.get_df_array(return_fields)
            if len(result) > 0:
                if isinstance(result[0], list):
                    for r in result:
                        yield r
                else:
                    yield result

    def _get_xml_data(self):
        """Return the raw XML data for this DOV object.

        Returns
        -------
        xml : bytes
            The raw XML data of this DOV object as bytes.

        """
        return openURL(self.pkey + '.xml').read()

    def _parse_subtypes(self, xml):
        """Parse the subtypes with the given XML data.

        Parameters
        ----------
        xml : bytes
            The raw XML data of the DOV object as bytes.

        """
        for subtype in self._subtypes:
            st_name = subtype.get_name()
            if st_name not in self.subdata:
                self.subdata[st_name] = []

            for subitem in subtype.from_xml(xml):
                self.subdata[st_name].append(subitem)

    def get_df_array(self, return_fields=None):
        """Return the data array of the instance of this type for inclusion
        in the resulting output dataframe of a search operation.

        Parameters
        ----------
        return_fields : list<str> or tuple<str> or set<str> or iterable<str>
            List of fields to include in the data array. The order is
            ignored, the default order of the fields of the datatype is used
            instead. Defaults to None, which will include all fields.

        Returns
        -------
        list
            List of the values of this instance in the same order as the
            field/column names, for inclusion in the result dataframe of a
            search operation.

        """
        fields = self.get_field_names(return_fields)
        ownfields = self.get_field_names(include_subtypes=False)
        subfields = [f for f in fields if f not in ownfields]

        if len(subfields) > 0:
            self._parse_xml_data()

        datadicts = []
        datarecords = []

        if len(self.subdata) == 0 or len(subfields) == 0:
            datadicts.append(self.data)
        else:
            for subtype in self.subdata:
                for subdata in self.subdata[subtype]:
                    datadict = {}
                    datadict.update(self.data)
                    datadict.update(subdata.data)
                    datadicts.append(datadict)

        for d in datadicts:
            datarecords.append([d[field] for field in fields])

        for d in datarecords:
            if self._UNRESOLVED in d:
                self._parse_xml_data()
                datarecords = self.get_df_array(return_fields)
                break

        return datarecords
