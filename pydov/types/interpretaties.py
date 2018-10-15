# -*- coding: utf-8 -*-
"""Module containing the DOV data types for interpretations, including
subtypes."""
import numpy as np

from pydov.types.abstract import (
    AbstractDovType,
    AbstractDovSubType,
)


class AbstractCommonInterpretatie(AbstractDovType):
    """Abstract base class for interpretations that can be linked to
    boreholes or cone penetration tests."""
    def __init__(self, pkey):
        """Initialisation.

        Parameters
        ----------
        pkey : str
            Permanent key of the Interpretatie (interpretations), being a
            URI of the form
            `https://www.dov.vlaanderen.be/data/interpretatie/<id>`.

        """
        super(AbstractCommonInterpretatie, self).__init__(
            'interpretatie', pkey)

    @classmethod
    def from_wfs_element(cls, feature, namespace):
        """Build an instance from a WFS feature element.

        Parameters
        ----------
        feature : etree.Element
            XML element representing a single record of the WFS layer.
        namespace : str
            Namespace associated with this WFS featuretype.

        Returns
        -------
        instance of this class
            An instance of this class populated with the data from the WFS
            element.

        """
        instance = cls(
            feature.findtext('./{%s}Interpretatiefiche' % namespace))

        typeproef = cls._parse(
            func=feature.findtext,
            xpath='Type_proef',
            namespace=namespace,
            returntype='string'
        )

        if typeproef == 'Boring':
            instance.data['pkey_boring'] = cls._parse(
                func=feature.findtext,
                xpath='Proeffiche',
                namespace=namespace,
                returntype='string'
            )
            instance.data['pkey_sondering'] = np.nan
        elif typeproef == 'Sondering':
            instance.data['pkey_sondering'] = cls._parse(
                func=feature.findtext,
                xpath='Proeffiche',
                namespace=namespace,
                returntype='string'
            )
            instance.data['pkey_boring'] = np.nan
        else:
            instance.data['pkey_boring'] = np.nan
            instance.data['pkey_sondering'] = np.nan

        for field in cls.get_fields(source=('wfs',)).values():
            if field['name'] in ['pkey_boring', 'pkey_sondering']:
                continue

            instance.data[field['name']] = cls._parse(
                func=feature.findtext,
                xpath=field['sourcefield'],
                namespace=namespace,
                returntype=field.get('type', None)
            )

        return instance


class AbstractBoringInterpretatie(AbstractDovType):
    """Abstract base class for interpretations that are linked to boreholes
    only."""
    def __init__(self, pkey):
        """Initialisation.

        Parameters
        ----------
        pkey : str
            Permanent key of the Interpretatie (interpretations), being a
            URI of the form
            `https://www.dov.vlaanderen.be/data/interpretatie/<id>`.

        """
        super(AbstractBoringInterpretatie, self).__init__(
            'interpretatie', pkey)

    @classmethod
    def from_wfs_element(cls, feature, namespace):
        """Build an instance from a WFS feature element.

        Parameters
        ----------
        feature : etree.Element
            XML element representing a single record of the WFS layer.
        namespace : str
            Namespace associated with this WFS featuretype.

        Returns
        -------
        instance of this class
            An instance of this class populated with the data from the WFS
            element.

        """
        instance = cls(
            feature.findtext('./{%s}Interpretatiefiche' % namespace))

        for field in cls.get_fields(source=('wfs',)).values():
            instance.data[field['name']] = cls._parse(
                func=feature.findtext,
                xpath=field['sourcefield'],
                namespace=namespace,
                returntype=field.get('type', None)
            )

        return instance


class InformeleStratigrafieLaag(AbstractDovSubType):

    _name = 'informele_stratigrafie_laag'
    _rootpath = './/informelestratigrafie/laag'

    _fields = [{
        'name': 'diepte_laag_van',
        'source': 'xml',
        'sourcefield': '/van',
        'definition': 'Diepte van de bovenkant van de laag informele '
                      'stratigrafie in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'diepte_laag_tot',
        'source': 'xml',
        'sourcefield': '/tot',
        'definition': 'Diepte van de onderkant van de laag informele '
                      'stratigrafie in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'beschrijving',
        'source': 'xml',
        'sourcefield': '/beschrijving',
        'definition': 'Benoeming van de eenheid van de laag informele '
                      'stratigrafie in vrije tekst (onbeperkt in lengte).',
        'type': 'string',
        'notnull': False
    }]


class InformeleStratigrafie(AbstractCommonInterpretatie):
    """Class representing the DOV data type for 'informele stratigrafie'
    interpretations."""

    _subtypes = [InformeleStratigrafieLaag]

    _fields = [{
        'name': 'pkey_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Interpretatiefiche',
        'type': 'string'
    }, {
        'name': 'pkey_boring',
        'source': 'custom',
        'type': 'string',
        'definition': 'URL die verwijst naar de gegevens van de boring '
                      'waaraan deze informele stratigrafie gekoppeld is ('
                      'indien gekoppeld aan een boring).',
        'notnull': False
    }, {
        'name': 'pkey_sondering',
        'source': 'custom',
        'type': 'string',
        'definition': 'URL die verwijst naar de gegevens van de sondering '
                      'waaraan deze informele stratigrafie gekoppeld is ('
                      'indien gekoppeld aan een sondering).',
        'notnull': False
    }, {
        'name': 'betrouwbaarheid_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Betrouwbaarheid',
        'type': 'string'
    }, {
        'name': 'x',
        'source': 'wfs',
        'sourcefield': 'X_mL72',
        'type': 'float'
    }, {
        'name': 'y',
        'source': 'wfs',
        'sourcefield': 'Y_mL72',
        'type': 'float'
    }]


class HydrogeologischeStratigrafieLaag(AbstractDovSubType):

    _name = 'hydrogeologische_stratigrafie_laag'
    _rootpath = './/hydrogeologischeinterpretatie/laag'

    _fields = [{
        'name': 'diepte_laag_van',
        'source': 'xml',
        'sourcefield': '/van',
        'definition': 'Diepte van de bovenkant van de laag hydrogeologische '
                      'stratigrafie in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'diepte_laag_tot',
        'source': 'xml',
        'sourcefield': '/tot',
        'definition': 'Diepte van de onderkant van de laag hydrogeologische '
                      'stratigrafie in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'aquifer',
        'source': 'xml',
        'sourcefield': '/aquifer',
        'definition': 'code van de watervoerende laag waarin de laag '
                      'Hydrogeologische stratigrafie zich bevindt.',
        'type': 'string',
        'notnull': False
    }]


class HydrogeologischeStratigrafie(AbstractBoringInterpretatie):
    """Class representing the DOV data type for 'hydrogeologische
    stratigrafie' interpretations."""

    _subtypes = [HydrogeologischeStratigrafieLaag]

    _fields = [{
        'name': 'pkey_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Interpretatiefiche',
        'type': 'string'
    }, {
        'name': 'pkey_boring',
        'source': 'wfs',
        'type': 'string',
        'sourcefield': 'Proeffiche'
    }, {
        'name': 'betrouwbaarheid_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Betrouwbaarheid',
        'type': 'string'
    },  {
        'name': 'x',
        'source': 'wfs',
        'sourcefield': 'X_mL72',
        'type': 'float'
    }, {
        'name': 'y',
        'source': 'wfs',
        'sourcefield': 'Y_mL72',
        'type': 'float'
    }]


class LithologischeBeschrijvingLaag(AbstractDovSubType):

    _name = 'lithologische_beschrijving_laag'
    _rootpath = './/lithologischebeschrijving/laag'

    _fields = [{
        'name': 'diepte_laag_van',
        'source': 'xml',
        'sourcefield': '/van',
        'definition': 'Diepte van de bovenkant van de laag lithologische '
                      'beschrijving in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'diepte_laag_tot',
        'source': 'xml',
        'sourcefield': '/tot',
        'definition': 'Diepte van de onderkant van de laag lithologische '
                      'beschrijving in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'beschrijving',
        'source': 'xml',
        'sourcefield': '/beschrijving',
        'definition': 'Lithologische beschrijving van de laag in vrije tekst '
                      '(onbeperkt in lengte)',
        'type': 'string',
        'notnull': False
    }]


class LithologischeBeschrijvingen(AbstractBoringInterpretatie):
    """Class representing the DOV data type for 'lithologische
    beschrijvingen' interpretations."""

    _subtypes = [LithologischeBeschrijvingLaag]

    _fields = [{
        'name': 'pkey_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Interpretatiefiche',
        'type': 'string'
    }, {
        'name': 'pkey_boring',
        'source': 'wfs',
        'type': 'string',
        'sourcefield': 'Proeffiche',
    }, {
        'name': 'betrouwbaarheid_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Betrouwbaarheid',
        'type': 'string'
    },  {
        'name': 'x',
        'source': 'wfs',
        'sourcefield': 'X_mL72',
        'type': 'float'
    }, {
        'name': 'y',
        'source': 'wfs',
        'sourcefield': 'Y_mL72',
        'type': 'float'
    }]


class GecodeerdeLithologieLaag(AbstractDovSubType):

    _name = 'gecodeerde_lithologie_laag'
    _rootpath = './/gecodeerdelithologie/laag'

    _fields = [{
        'name': 'diepte_laag_van',
        'source': 'xml',
        'sourcefield': '/van',
        'definition': 'Diepte van de bovenkant van de laag gecodeerde'
                      ' lithologie in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'diepte_laag_tot',
        'source': 'xml',
        'sourcefield': '/tot',
        'definition': 'Diepte van de onderkant van de laag gecodeerde'
                      ' lithologie in meter.',
        'type': 'float',
        'notnull': False
    }, {
        'name': 'hoofdnaam1_grondsoort',
        'source': 'xml',
        'sourcefield': '/hoofdnaam[1]/grondsoort',
        'definition': 'Primaire grondsoort (als code) van de laag '
                      'gecodeerde lithologie',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'hoofdnaam2_grondsoort',
        'source': 'xml',
        'sourcefield': '/hoofdnaam[2]/grondsoort',
        'definition': 'Secundaire grondsoort (als code) van de laag '
                      'gecodeerde lithologie',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'bijmenging1_plaatselijk',
        'source': 'xml',
        'sourcefield': '/bijmenging[1]/plaatselijk',
        'definition': 'plaatselijk of niet-plaatselijk',
        'type': 'boolean',
        'notnull': False
    }, {
        'name': 'bijmenging1_hoeveelheid',
        'source': 'xml',
        'sourcefield': '/bijmenging[1]/hoeveelheid',
        'definition': 'aanduiding van de hoeveelheid bijmenging',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'bijmenging1_grondsoort',
        'source': 'xml',
        'sourcefield': '/bijmenging[1]/grondsoort',
        'definition': 'type grondsoort (als code) van de laag '
                      'gecodeerde lithologie of geotechnische '
                      'codering',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'bijmenging2_plaatselijk',
        'source': 'xml',
        'sourcefield': '/bijmenging[2]/plaatselijk',
        'definition': 'plaatselijk of niet-plaatselijk',
        'type': 'boolean',
        'notnull': False
    }, {
        'name': 'bijmenging2_hoeveelheid',
        'source': 'xml',
        'sourcefield': '/bijmenging[2]/hoeveelheid',
        'definition': 'aanduiding van de hoeveelheid bijmenging',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'bijmenging2_grondsoort',
        'source': 'xml',
        'sourcefield': '/bijmenging[2]/grondsoort',
        'definition': 'type grondsoort (als code) van de laag '
                      'gecodeerde lithologie of geotechnische '
                      'codering',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'bijmenging3_plaatselijk',
        'source': 'xml',
        'sourcefield': '/bijmenging[3]/plaatselijk',
        'definition': 'plaatselijk of niet-plaatselijk',
        'type': 'boolean',
        'notnull': False
    }, {
        'name': 'bijmenging3_hoeveelheid',
        'source': 'xml',
        'sourcefield': '/bijmenging[3]/hoeveelheid',
        'definition': 'aanduiding van de hoeveelheid bijmenging',
        'type': 'string',
        'notnull': False
    }, {
        'name': 'bijmenging3_grondsoort',
        'source': 'xml',
        'sourcefield': '/bijmenging[3]/grondsoort',
        'definition': 'type grondsoort (als code) van de laag '
                      'gecodeerde lithologie of geotechnische '
                      'codering',
        'type': 'string',
        'notnull': False
    }]


class GecodeerdeLithologie(AbstractBoringInterpretatie):
    """Class representing the DOV data type for 'gecodeerde
    lithologie' interpretations."""

    _subtypes = [GecodeerdeLithologieLaag]

    _fields = [{
        'name': 'pkey_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Interpretatiefiche',
        'type': 'string'
    }, {
        'name': 'pkey_boring',
        'source': 'wfs',
        'type': 'string',
        'sourcefield': 'Proeffiche',
    }, {
        'name': 'betrouwbaarheid_interpretatie',
        'source': 'wfs',
        'sourcefield': 'Betrouwbaarheid',
        'type': 'string'
    },  {
        'name': 'x',
        'source': 'wfs',
        'sourcefield': 'X_mL72',
        'type': 'float'
    }, {
        'name': 'y',
        'source': 'wfs',
        'sourcefield': 'Y_mL72',
        'type': 'float'
    }]
