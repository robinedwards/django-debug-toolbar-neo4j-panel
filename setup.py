from setuptools import setup

setup(
        name='django-debug-toolbar-neo4j-panel',
        version='0.0.1',
        description='Simple debug toolbar panel for the Neo4j rest client',
        author='Robin Edwards',
        author_email='robin.ge@gmail.com',
        url='http://github.com/robinedwards/django-debug-toolbar-neo4j-panel',
        license='MIT',
        py_modules=['neo4j_panel'],
        zip_safe=True,
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Framework :: Django',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules',
            ],
        )
