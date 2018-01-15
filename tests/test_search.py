"""Module grouping tests for the search module."""
import datetime
import sys

import pytest
from numpy.compat import unicode
from owslib.fes import PropertyIsEqualTo
from pandas import DataFrame

import pydov
from pydov.search import BoringSearch
from pydov.types.boring import Boring
from pydov.util.errors import (
    InvalidSearchParameterError,
    InvalidFieldError,
)
from tests.test_types_boring import mp_boring_xml
from tests.test_util_owsutil import (
    mp_wfs,
    mp_remote_describefeaturetype,
    mp_remote_md,
    mp_remote_fc,
    wfs,
)


@pytest.fixture
def mp_remote_wfs_feature(monkeypatch):
    """Monkeypatch the call to get WFS features.

    Parameters
    ----------
    monkeypatch : pytest.fixture
        PyTest monkeypatch fixture.

    """
    def __get_remote_wfs_feature(*args, **kwargs):
        with open('tests/data/search/wfsgetfeature.xml',
                  'r') as f:
            data = f.read()
            if type(data) is not bytes:
                data = data.encode('utf-8')
        return data

    if sys.version_info[0] < 3:
        monkeypatch.setattr(
            'pydov.search.AbstractSearch._get_remote_wfs_feature',
            __get_remote_wfs_feature)
    else:
        monkeypatch.setattr(
            'pydov.search.AbstractSearch._get_remote_wfs_feature',
            __get_remote_wfs_feature)


@pytest.fixture
def boringsearch():
    """PyTest fixture returning an instance of pydov.search.BoringSearch.

    Returns
    -------
    pydov.search.BoringSearch
        An instance of BoringSearch to perform search operations on the DOV
        type 'Boring'.

    """
    return BoringSearch()


class TestBoringSearch(object):
    """Class grouping tests for the pydov.search.BoringSearch class."""

    def test_get_description(self, mp_wfs, boringsearch):
        """Test the get_description method.

        Test whether the method returns a non-empty string.

        Parameters
        ----------
        mp_wfs : pytest.fixture
            Monkeypatch the call to the remote GetCapabilities request.
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        description = boringsearch.get_description()

        assert type(description) in (str, unicode)
        assert len(description) > 0

    def test_get_fields(self, mp_wfs, mp_remote_describefeaturetype,
                        mp_remote_md, mp_remote_fc, boringsearch):
        """Test the get_fields method.

        Test whether the returned fields match the format specified in the
        documentation.

        Parameters
        ----------
        mp_wfs : pytest.fixture
            Monkeypatch the call to the remote GetCapabilities request.
        mp_remote_describefeaturetype : pytest.fixture
            Monkeypatch the call to a remote DescribeFeatureType of the
            dov-pub:Boringen layer.
        mp_remote_md : pytest.fixture
            Monkeypatch the call to get the remote metadata of the
            dov-pub:Boringen layer.
        mp_remote_fc : pytest.fixture
            Monkeypatch the call to get the remote feature catalogue of the
            dov-pub:Boringen layer.
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        fields = boringsearch.get_fields()

        assert type(fields) is dict

        for field in fields:
            assert type(field) in (str, unicode)

            f = fields[field]
            assert type(f) is dict

            assert 'name' in f
            assert type(f['name']) in (str, unicode)
            assert f['name'] == field

            assert 'definition' in f
            assert type(f['name']) in (str, unicode)

            assert 'type' in f
            assert type(f['type']) in (str, unicode)
            assert f['type'] in ['string', 'float', 'integer', 'date',
                                 'boolean']

            assert 'notnull' in f
            assert type(f['notnull']) is bool

            assert 'cost' in f
            assert type(f['cost']) is int
            assert f['cost'] > 0

            if 'values' in f:
                assert sorted(f.keys()) == [
                    'cost', 'definition', 'name', 'notnull', 'type', 'values']
                for v in f['values']:
                    if f['type'] == 'string':
                        assert type(v) in (str, unicode)
                    elif f['type'] == 'float':
                        assert type(v) is float
                    elif f['type'] == 'integer':
                        assert type(v) is int
                    elif f['type'] == 'date':
                        assert type(v) is datetime.date
                    elif f['type'] == 'boolean':
                        assert type(v) is bool
            else:
                assert sorted(f.keys()) == ['cost', 'definition', 'name',
                                            'notnull', 'type']

    def test_search_nolocation_noquery(self, boringsearch):
        """Test the search method without providing a location or a query.

        Test whether an InvalidSearchParameterError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        with pytest.raises(InvalidSearchParameterError):
            boringsearch.search(location=None, query=None)

    def test_search_both_location_query(self, boringsearch):
        """Test the search method providing both a location and a query.

        Test whether an InvalidSearchParameterError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        with pytest.raises(InvalidSearchParameterError):
            query = PropertyIsEqualTo(propertyname='gemeente',
                                      literal='Blankenberge')
            boringsearch.search(location=(1, 2, 3, 4),
                                query=query)

    def test_search(self, mp_wfs, mp_remote_describefeaturetype, mp_remote_md,
                    mp_remote_fc, mp_remote_wfs_feature, mp_boring_xml,
                    boringsearch):
        """Test the search method with only the query parameter.

        Test whether the result is correct.

        Parameters
        ----------
        mp_wfs : pytest.fixture
            Monkeypatch the call to the remote GetCapabilities request.
        mp_remote_describefeaturetype : pytest.fixture
            Monkeypatch the call to a remote DescribeFeatureType of the
            dov-pub:Boringen layer.
        mp_remote_md : pytest.fixture
            Monkeypatch the call to get the remote metadata of the
            dov-pub:Boringen layer.
        mp_remote_fc : pytest.fixture
            Monkeypatch the call to get the remote feature catalogue of the
            dov-pub:Boringen layer.
        mp_remote_wfs_feature : pytest.fixture
            Monkeypatch the call to get WFS features.
        mp_boring_xml : pytest.fixture
            Monkeypatch the call to get the remote Boring XML data.
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boornummer',
                                  literal='GEO-04/169-BNo-B1')
        df = boringsearch.search(query=query)

        assert type(df) is DataFrame

        assert list(df) == ['pkey_boring', 'boornummer', 'x', 'y', 'mv_mtaw',
                            'start_boring_mtaw', 'gemeente',
                            'diepte_boring_van', 'diepte_boring_tot',
                            'datum_aanvang', 'uitvoerder', 'boorgatmeting',
                            'diepte_methode_van', 'diepte_methode_tot',
                            'boormethode']

        allfields = Boring.get_field_names()
        ownfields = Boring.get_field_names(include_subtypes=False)
        subfields = [f for f in allfields if f not in ownfields]

        for field in list(df):
            if field in ownfields:
                assert len(df[field].unique()) == 1
            elif field in subfields:
                assert len(df[field].unique()) == len(df)

        assert df.mv_mtaw.hasnans

        fields = Boring.get_fields()
        for field in list(df):
            if field == 'mv_mtaw':
                continue

            datatype = fields[field]['type']
            if datatype == 'string':
                assert df[field].dtype.name == 'object'
            elif datatype == 'float':
                assert df[field].dtype.name == 'float64'
            elif datatype == 'integer':
                assert df[field].dtype.name == 'integer'
            elif datatype == 'date':
                assert df[field].dtype.name == 'object'
            elif datatype == 'boolean':
                assert df[field].dtype.name == 'bool'

        assert len(df) == 2
        assert df.datum_aanvang.unique()[0] == datetime.date(2004, 12, 20)

    def test_search_returnfields(self, mp_remote_wfs_feature,
                                     boringsearch):
        """Test the search method with the query parameter and a selection of
        return fields.

        Test whether the output dataframe contains only the selected return
        fields.

        Parameters
        ----------
        mp_remote_wfs_feature : pytest.fixture
            Monkeypatch the call to get WFS features.
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boornummer',
                                  literal='GEO-04/169-BNo-B1')

        df = boringsearch.search(query=query,
                                 return_fields=('pkey_boring', 'boornummer',
                                                'diepte_boring_tot',
                                                'datum_aanvang'))

        assert type(df) is DataFrame

        assert list(df) == ['pkey_boring', 'boornummer', 'diepte_boring_tot',
                            'datum_aanvang']

    def test_search_returnfields_order(self, mp_remote_wfs_feature,
                                     boringsearch):
        """Test the search method with the query parameter and a selection of
        return fields in another ordering.

        Test whether the output dataframe contains only the selected return
        fields, in the order that is documented in
        docs/description_output_dataframes.rst

        Parameters
        ----------
        mp_remote_wfs_feature : pytest.fixture
            Monkeypatch the call to get WFS features.
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boornummer',
                                  literal='GEO-04/169-BNo-B1')

        df = boringsearch.search(query=query,
                                 return_fields=('pkey_boring', 'boornummer',
                                                'datum_aanvang',
                                                'diepte_boring_tot'))

        assert type(df) is DataFrame

        assert list(df) == ['pkey_boring', 'boornummer', 'diepte_boring_tot',
                            'datum_aanvang']

    def test_search_wrongreturnfields(self, boringsearch):
        """Test the search method with the query parameter and an inexistent
        return field.

        Test whether an InvalidFieldError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boornummer',
                                  literal='GEO-04/169-BNo-B1')

        with pytest.raises(InvalidFieldError):
            boringsearch.search(query=query,
                                return_fields=('pkey_boring', 'onbestaand'))

    def test_search_wrongreturnfields_queryfield(self, boringsearch):
        """Test the search method with the query parameter and a query-only
        field as return field.

        Test whether an InvalidFieldError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boornummer',
                                  literal='GEO-04/169-BNo-B1')

        with pytest.raises(InvalidFieldError):
            boringsearch.search(query=query,
                                return_fields=('pkey_boring', 'doel'))

    def test_search_wrongreturnfieldstype(self, boringsearch):
        """Test the search method with the query parameter and a single
        return field as string.

        Test whether an AttributeError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boornummer',
                                  literal='GEO-04/169-BNo-B1')

        with pytest.raises(AttributeError):
            boringsearch.search(query=query,
                                return_fields='datum_aanvang')

    def test_search_query_wrongfield(self, boringsearch):
        """Test the search method with the query parameter using an
        inexistent query field.

        Test whether an InvalidFieldError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='onbestaand',
                                  literal='Geotechnisch onderzoek')

        with pytest.raises(InvalidFieldError):
            boringsearch.search(query=query)

    def test_search_query_wrongfield_returnfield(self, boringsearch):
        """Test the search method with the query parameter using an
        return-only field as query field.

        Test whether an InvalidFieldError is raised.

        Parameters
        ----------
        boringsearch : pytest.fixture returning pydov.search.BoringSearch
            An instance of BoringSearch to perform search operations on the DOV
            type 'Boring'.

        """
        query = PropertyIsEqualTo(propertyname='boormethode',
                                  literal='Geotechnisch onderzoek')

        with pytest.raises(InvalidFieldError):
            boringsearch.search(query=query)
