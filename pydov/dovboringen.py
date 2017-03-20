"""
This module handles the selection of borehole data from the DOV webservice.

It's development was made possible by the financing of Vlaio (Flanders, Belgium) and AGT n.v (www.agt.be).
"""
__author__ = ['Pieter Jan Haest', "Johan Van De Wauw"]
__copyright__ = 'Copyright 2017, DOV-Vlaanderen'
__credits__ = ["Stijn Van Hoey"]
__license__ = "MIT"
__version__ = '0.1'
__maintainer__ = "Pieter Jan Haest"
__email__ = "geo.haest@gmail.com"
__status__ = "Development"

from owslib.wfs import WebFeatureService
from owslib import fes
import xmltodict
import requests
import pandas as pd


class DOVVariableError(Exception):
    pass


class DovBoringen(object):
    """
    Examples
    --------
    >>>dov = DovBoringen()
    >>>extracted_locations = dov.get_boringen(query_string="diepte_tot_m > 10" , bbox=(160000, 200000, 178100, 215100))

    """

    def __init__(self, url='https://www.dov.vlaanderen.be/geoserver/wfs', version='2.0.0', layer='dov-pub:Boringen',
                 maxfeatures=10000, timeout=30, outputformat='xml', epsg='31370'):
        """ Initialize DovBoringen instance to read borehole data for selected locations in xml

        Parameters
        ----------
        url: str
            url string
        version: str
            the version on the wfs_boring
        layer: str
            the layer with the general borehole data
        maxfeatures: int
            the maximum number of features that will be obtained from the wfs_boring
        timeout: int
            time in seconds after which requests should time-out
        outputformat: str
            the format that is returned from the wfs_boring
        epsg: int
            the epsg code in which data should be retrieved. Default value for Lamber72: 31370
        """
        # define general wfs_boring info
        self.layer = layer
        self.outputformat = 'application/'+outputformat
        self.timeout = timeout
        self.wfs_boring = WebFeatureService(url=url, version=version)
        # check version
        self.version = self.wfs_boring.identification.version
        # check contents through: self.wfs_boring.contents['dov-pub:Boringen']
        self.maxfeatbool = False    # a boolean indicating that a limit exists on the queryable features
        self.srsname = 'urn:x-ogc:def:crs:EPSG:'+epsg

        try:
            server_maxfeatures = int(self.wfs_boring.constraints['DefaultMaxFeatures'].values[0])
            if server_maxfeatures < maxfeatures:
                self.maxfeatures = server_maxfeatures
                self.maxfeatbool = True
            else:
                self.maxfeatures = maxfeatures
        except:
            self.maxfeatures = maxfeatures

        # define variables
        self.interpretations = ['gecodeerde_lithologie', 'geotechnische_codering', 'hydrogeologische_stratigrafie',
                                'informele_hydrostratigrafie', 'informele_stratigrafie', 'lithologische_beschrijving', ]
        self.property_names = ['diepte_tot_m', 'dikte_quartair', 'formele_stratigrafie', 'gecodeerde_lithologie',
                               'geotechnische_codering', 'hydrogeologische_stratigrafie', 'informele_hydrostratigrafie',
                               'informele_stratigrafie', 'lithologische_beschrijving', ]

    def get_boringen(self, query_string='', bbox=None, add_props=[]):
        """Query the wfs_boring for a all boreholes within a selected bounding box or given constraints.

        A dataframe containing the selected variables is returned. The following variables are always included:
        'boornummer', 'fiche', 'X_ml72', 'Y_ml72', 'Z_mTAW', 'methode', 'diepte_tot_m', 'dikte_quartair',
        'formele_stratigrafie', 'gecodeerde_lithologie', 'geotechnische_codering', 'hydrogeologische_stratigrafie',
        'informele_hydrostratigrafie', 'informele_stratigrafie', 'lithologische_beschrijving'
         Additional variables from the xml can be selected by providing the PropertyName in the list of add_props.
        The following variables are remapped to a more readable name in the resulting dataframe:
        {fiche: url_data, X_ml72: x, Y_ml72: y, Z_mTAW: z_mv}.

        Parameters:
        -----------
        query_string: str
            A string containing the query that will be used as constrained in the WFS call
        bbox: tuple of floats
            The X, Y coordinates of the bounding box as (xmin, ymin, xmax, ymax)
        add_props: list of strings
            A list with the PropertyNames of attributes in the queried layer that need to be selected in addition
            to the default ones

        Return:
        -------
        boringen_df: dataframe
            A dataframe with the selected attributes of the selected borehole locations

        """
        # extract data with user-defined column names
        user_defined = ['boornummer', 'url_data', 'x', 'y', 'z_mv', 'methode']
        dov_defined = ['boornummer', 'fiche', 'X_mL72', 'Y_mL72', 'Z_mTAW', 'methode']
        # get list with queried properties (different for version 1.1.0 and 2.0.0):
        variables1 = dov_defined + self.property_names + add_props
        variables2 = ['dov-pub:' + x for x in variables1]
        propertynames = variables1 if self.version == '1.1.0' else variables2
        # query the wfs layer for the given constraints in the bounding box
        filterxml = self.compose_query(query_string, bbox, self.wfs_filters)
        response = self.wfs_boring.getfeature(typename=self.layer,
                                              propertyname=propertynames,  # gives service exception for version 1.1.0
                                              maxfeatures=self.maxfeatures,
                                              # filter=filterxml,           # took ages to query, bbox is faster
                                              bbox=bbox,
                                              # outputFormat=self.outputformat,  # xml is only option and possible error
                                              # srsname=self.srsname  # does not work for version 2.0.0
                                              )
        if self.version == '1.1.0':
            boringen_df = pd.DataFrame(self.parse_wfs(response, self.layer, self.version),
                                       columns=variables1
                                       ).rename(columns=dict(zip(dov_defined, user_defined)))
        elif self.version == '2.0.0':
            boringen_df = pd.DataFrame(self.parse_wfs(response, self.layer, self.version),
                                       columns=variables2
                                       ).rename(columns=dict(zip(['dov-pub:'+x for x in dov_defined], user_defined)))
        return boringen_df

    @staticmethod
    def parse_wfs(response, layer, version):
        """A generator to parse the response from a wfs, depending on the server version

        Parameters:
        -----------
        response: StringIO
            The response from a wfs.getfeature() query (OWSlib)
        layer: str
            The wfs layer that is queried
        version: str
            The version of the WFS server: only '1.1.0' and '

        """
        if version == "1.1.0":
            # convert layer preposition to null
            layer = 'null:' + layer.split(':')[1]
            # convert the response to a dictionary
            doc = xmltodict.parse(response)
            # yield the layers of the dict
            for a in doc['wfs:FeatureCollection']['gml:featureMembers']:
                yield (a[layer])
        elif version == "2.0.0":
            # convert the response to a dictionary
            doc = xmltodict.parse(response.read())
            # yield the layers of the dict
            for a in doc['wfs:FeatureCollection']['wfs:member']:
                yield (a[layer])

    @staticmethod
    def compose_query(query_string, bbox, wfs_filters):
        """Compose a wfs filter query from a string

        The query string should be composed as: "property_name operator literal". The property names and operators are
         initialized with the DovBoringen class.
         Multiple filters can be added by comma separation e.g.:
         "property_name1 operator1 literal1, property_name2 operator2 literal2"
         The PropertyIsBetween operator requires a lower and upper boundary, it is given by a tuple in the string, e.g.:
         "diepte_tot_m << (20,100)"

        Parameters:
        -----------
        query_string: str
            A string containing the query that will be used as constrained in the WFS call. See also: get_boringen()
        bbox: tuple of floats, or empty tuple
            The X, Y coordinates of the bounding box as (xmin, ymin, xmax, ymax)
        wfs_filters: dict
            A dictionary mapping the operator in the query string to the comparison operator of the wfs call

        Returns:
        --------
        filterxml: str
            A string of the xml constraint for a wfs call using owslib

        """
        filters = []
        # extract criteria
        if query_string:
            query_raw = [x.strip(' ,') for x in query_string.split(' ')]
            if len(query_raw) % 3 != 0:
                raise ValueError('The query string is not correct. '
                                 'It should be composed of "property operator literal"')
            idx = 1
            for fltr in query_raw[1::3]:
                if fltr != '<<':
                    filters.append(wfs_filters[fltr](propertyname=query_raw[idx-1],
                                                     literal=query_raw[idx+1]))
                else:
                    lb, ub = [x.strip(['(', ')']) for x in query_raw[idx+1].split(',')]
                    filters.append(wfs_filters[fltr](propertyname=query_raw[idx - 1],
                                                     lowerboundary=lb, upperboundary=ub))
                    idx += 3
        if bbox:
            filters.append(fes.BBox(bbox))
        if len(filters) == 1:
            filter = fes.FilterRequest().setConstraint(filters[0])
        elif len(filters) > 1:
            # only logical AND is evaluated (constraint = [[a, b]])
            filter = fes.FilterRequest().setConstraintList([filters])
        else:
            return ''

        filterxml = fes.etree.tostring(filter, encoding="utf-8", method='xml')
        return filterxml

if __name__ == '__main__':
    dov = DovBoringen(maxfeatures=10)
    query_str = 'diepte_tot_m > 20'
    extracted_locations = dov.get_boringen(query_string=query_str, bbox=(160000, 200000, 178100, 215100))
    a = 1
    df_boringen = dov.get_boringen_data(extracted_locations)

