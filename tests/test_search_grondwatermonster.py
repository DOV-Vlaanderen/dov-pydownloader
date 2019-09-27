"""Module grouping tests for the search grondwaterfilter module."""
import datetime

from owslib.fes import PropertyIsEqualTo
from pydov.search.grondwatermonster import GrondwaterMonsterSearch
from pydov.types.grondwatermonster import GrondwaterMonster
from tests.abstract import (
    AbstractTestSearch,
)

from tests.test_search import (
    mp_wfs,
    wfs,
    mp_remote_md,
    mp_remote_fc,
    mp_remote_describefeaturetype,
    mp_remote_wfs_feature,
    mp_remote_xsd,
    mp_dov_xml,
    mp_dov_xml_broken,
    wfs_getfeature,
    wfs_feature,
)

location_md_metadata = 'tests/data/types/grondwatermonster/md_metadata.xml'
location_fc_featurecatalogue = \
    'tests/data/types/grondwatermonster/fc_featurecatalogue.xml'
location_wfs_describefeaturetype = \
    'tests/data/types/grondwatermonster/wfsdescribefeaturetype.xml'
location_wfs_getfeature = 'tests/data/types/grondwatermonster/wfsgetfeature.xml'
location_wfs_feature = 'tests/data/types/grondwatermonster/feature.xml'
location_dov_xml = 'tests/data/types/grondwatermonster/grondwaterfilter.xml'
location_xsd_base = 'tests/data/types/grondwatermonster/xsd_*.xml'


class TestGrondwaterfilterSearch(AbstractTestSearch):
    def get_search_object(self):
        """Get an instance of the search object for this type.

        Returns
        -------
        pydov.search.grondwatermonster.GrondwaterMonsterSearch
            Instance of GrondwaterMonsterSearch used for searching.

        """
        return GrondwaterMonsterSearch()

    def get_type(self):
        """Get the class reference for this datatype.

        Returns
        -------
        pydov.types.grondwaterfilter.GrondwaterFilter
            Class reference for the GrondwaterFilter class.

        """
        return GrondwaterMonster

    def get_valid_query_single(self):
        """Get a valid query returning a single feature.

        Returns
        -------
        owslib.fes.OgcExpression
            OGC expression of the query.

        """
        return PropertyIsEqualTo(propertyname='filterfiche',
                                 literal='https://www.dov.vlaanderen.be/data/'
                                         'watermonster/2006-115684')

    def get_inexistent_field(self):
        """Get the name of a field that doesn't exist.

        Returns
        -------
        str
            The name of an inexistent field.

        """
        return 'onbestaand'

    def get_xml_field(self):
        """Get the name of a field defined in XML only.

        Returns
        -------
        str
            The name of the XML field.

        """
        return 'eenheid'

    def get_valid_returnfields(self):
        """Get a list of valid return fields from the main type.

        Returns
        -------
        tuple
            A tuple containing only valid return fields.

        """
        return ('pkey_grondwatermonster', 'datum_monstername')

    def get_valid_returnfields_subtype(self):
        """Get a list of valid return fields, including fields from a subtype.

        Returns
        -------
        tuple
            A tuple containing valid return fields, including fields from a
            subtype.

        """
        return ('pkey_grondwatermonster', 'eenheid', 'datum_monstername')

    def get_valid_returnfields_extra(self):
        """Get a list of valid return fields, including extra WFS only
        fields not present in the default dataframe.

        Returns
        -------
        tuple
            A tuple containing valid return fields, including extra fields
            from WFS, not present in the default dataframe.

        """
        return ('pkey_grondwatermonster', 'kationen')

    def get_df_default_columns(self):
        """Get a list of the column names (and order) from the default
        dataframe.

        Returns
        -------
        list
            A list of the column names of the default dataframe.

        """
        return ['pkey_grondwatermonster',
            'grondwatermonsternummer',
            'pkey_grondwaterlocatie',
            'pkey_filter',
            'gw_id',
            'filternummer',
            'x',
            'y',
            'mv_mtaw',
            'gemeente',
            'datum_monstername',
            'parameter',
            'eenheid',
            'detectie',
            'waarde',
            'parametergroep',
            'veld_labo']

    def test_search_date(self, mp_wfs, mp_remote_describefeaturetype,
                         mp_remote_md, mp_remote_fc, mp_remote_wfs_feature,
                         mp_dov_xml):
        """Test the search method with only the query parameter.

        Test whether the result is correct.

        Parameters
        ----------
        mp_wfs : pytest.fixture
            Monkeypatch the call to the remote GetCapabilities request.
        mp_remote_describefeaturetype : pytest.fixture
            Monkeypatch the call to a remote DescribeFeatureType.
        mp_remote_md : pytest.fixture
            Monkeypatch the call to get the remote metadata.
        mp_remote_fc : pytest.fixture
            Monkeypatch the call to get the remote feature catalogue.
        mp_remote_wfs_feature : pytest.fixture
            Monkeypatch the call to get WFS features.
        mp_dov_xml : pytest.fixture
            Monkeypatch the call to get the remote XML data.

        """
        df = self.get_search_object().search(
            query=self.get_valid_query_single())

        # specific test for the Zulu time wfs 1.1.0 issue
        assert df.datum.sort_values()[0] == datetime.date(2004, 4, 7)

    def test_search_xmlresolving(self, mp_remote_describefeaturetype,
                                 mp_remote_wfs_feature, mp_dov_xml):
        """Test the search method with return fields from XML but not from a
        subtype.

        Test whether the output dataframe contains the resolved XML data.

        Parameters
        ----------
        mp_remote_describefeaturetype : pytest.fixture
            Monkeypatch the call to a remote DescribeFeatureType.
        mp_remote_wfs_feature : pytest.fixture
            Monkeypatch the call to get WFS features.
        mp_dov_xml : pytest.fixture
            Monkeypatch the call to get the remote XML data.

        """
        df = self.get_search_object().search(
            query=self.get_valid_query_single(),
            return_fields=('pkey_grondwatermonster', 'parameter', 'waarde',
                           'eenheid'))

        assert df.meetnet_code[0] == 8