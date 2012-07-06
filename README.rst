Django debug toolbar Neo4j panel
================================

Trace ``neo4jrestclient`` calls in your django application, this also works for ``neo4django``.

Installation
============

Install the module via git::

    pip install -e git://github.com/robinedwards/django-debug-toolbar-neo4j-panel.git

Add panel to your list of panels::

    DEBUG_TOOLBAR_PANELS = ('neo4j_panel.Neo4jPanel',)
