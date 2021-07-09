.. _tutorials:

=========
Tutorials
=========


These tutorials illustrate use cases the pydov package supports, split
up by different topics each setup as a `jupyter notebook`_
you can run yourself. The introductory tutorial bundles most
of the interesting features and methods of pydov and would be a good
start.

.. _jupyter notebook: http://jupyter.org/

.. note::
    These tutorials use a number of Python packages that are not required by the pydov package itself. For example `folium`_
    to create interactive maps. We keep track of these dependencies in the :code:`binder/requirements.txt` file. If you want to run the tutorials
    on your own computer, install these packages to your existing :code:`conda` or :code:`venv` environment by running:

    ::

        pip install -r binder/requirements.txt

.. _folium: https://pypi.org/project/folium/

To run these interactively online without installation, use the following binder link:

.. image:: https://mybinder.org/badge.svg
   :target: https://mybinder.org/v2/gh/dov-vlaanderen/pydov/master?filepath=docs%2Fnotebooks


.. toctree::
   :maxdepth: 1

   notebooks/introductory_tutorial.ipynb
   notebooks/search_boringen.ipynb
   notebooks/search_sonderingen.ipynb
   notebooks/search_grondwaterfilters.ipynb
   notebooks/search_grondwatermonsters.ipynb
   notebooks/search_grondwatervergunningen.ipynb
   notebooks/search_formele_stratigrafie.ipynb
   notebooks/search_informele_stratigrafie.ipynb
   notebooks/search_hydrogeologische_stratigrafie.ipynb
   notebooks/search_informele_hydrostratigrafie.ipynb
   notebooks/search_lithologische_beschrijvingen.ipynb
   notebooks/search_gecodeerde_lithologie.ipynb
   notebooks/search_geotechnische_codering.ipynb
   notebooks/search_quartaire_stratigrafie.ipynb
   notebooks/search_grondmonsters.ipynb
   notebooks/search_bodem.ipynb
   notebooks/search_aardewerk.ipynb
   notebooks/customizing_object_types.ipynb
   notebooks/spatial_querying.ipynb
   notebooks/caching.ipynb
