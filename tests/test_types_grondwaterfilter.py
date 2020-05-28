"""Module grouping tests for the pydov.types.boring module."""
from pydov.types.grondwaterfilter import GrondwaterFilter
from pydov.util.dovutil import build_dov_url
from tests.abstract import AbstractTestTypes
from tests.test_search_grondwaterfilter import (location_dov_xml,
                                                location_wfs_feature,
                                                location_wfs_getfeature,
                                                mp_dov_xml, wfs_feature,
                                                wfs_getfeature)


class TestGrondwaterFilter(AbstractTestTypes):
    """Class grouping tests for the
    pydov.types.grondwaterfilter.GrondwaterFilter class."""

    datatype_class = GrondwaterFilter
    namespace = 'http://dov.vlaanderen.be/grondwater/gw_meetnetten'
    pkey_base = build_dov_url('data/filter/')

    field_names = [
        'pkey_filter', 'pkey_grondwaterlocatie', 'gw_id',
        'filternummer', 'filtertype', 'x', 'y',
        'start_grondwaterlocatie_mtaw', 'mv_mtaw',
        'gemeente', 'meetnet_code', 'aquifer_code',
        'grondwaterlichaam_code', 'regime',
        'diepte_onderkant_filter', 'lengte_filter',
        'datum', 'tijdstip', 'peil_mtaw',
        'betrouwbaarheid', 'methode', 'filterstatus', 'filtertoestand']
    field_names_subtypes = [
        'datum', 'tijdstip', 'peil_mtaw', 'betrouwbaarheid',
        'methode']
    field_names_nosubtypes = [
        'pkey_filter', 'pkey_grondwaterlocatie', 'gw_id',
        'filternummer', 'filtertype', 'x', 'y',
        'start_grondwaterlocatie_mtaw', 'mv_mtaw',
        'gemeente', 'meetnet_code', 'aquifer_code',
        'grondwaterlichaam_code', 'regime',
        'diepte_onderkant_filter', 'lengte_filter']

    valid_returnfields = ('pkey_filter', 'meetnet_code')
    valid_returnfields_subtype = ('pkey_filter', 'peil_mtaw')

    inexistent_field = 'onbestaand'
