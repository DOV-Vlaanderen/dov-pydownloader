"""Module grouping tests for the
pydov.types.interpretaties.FormeleStratigrafie class."""
from pydov.types.interpretaties import FormeleStratigrafie
from pydov.util.dovutil import build_dov_url
from tests.abstract import AbstractTestTypes
from tests.test_search_itp_formelestratigrafie import (location_dov_xml,
                                                       location_wfs_feature,
                                                       location_wfs_getfeature,
                                                       mp_dov_xml, wfs_feature,
                                                       wfs_getfeature)


class TestFormeleStratigrafie(AbstractTestTypes):
    """Class grouping tests for the
    pydov.types.interpretaties.FormeleStratigrafie class."""

    datatype_class = FormeleStratigrafie
    namespace = 'http://dov.vlaanderen.be/ocdov/interpretaties'
    pkey_base = build_dov_url('data/interpretatie/')

    field_names = [
        'pkey_interpretatie', 'pkey_boring',
        'pkey_sondering', 'betrouwbaarheid_interpretatie', 'x', 'y',
        'diepte_laag_van', 'diepte_laag_tot', 'lid1', 'relatie_lid1_lid2',
        'lid2']
    field_names_subtypes = [
        'diepte_laag_van', 'diepte_laag_tot', 'lid1', 'relatie_lid1_lid2',
        'lid2']
    field_names_nosubtypes = [
        'pkey_interpretatie', 'pkey_boring',
        'pkey_sondering', 'betrouwbaarheid_interpretatie', 'x', 'y']

    valid_returnfields = ('pkey_interpretatie', 'pkey_sondering')
    valid_returnfields_subtype = (
        'pkey_interpretatie', 'diepte_laag_van', 'diepte_laag_tot')

    inexistent_field = 'onbestaand'
