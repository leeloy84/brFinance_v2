import sys

import setuptools

if sys.version_info < (3, 7):
    raise RuntimeError('bolsa requires Python 3.7+')

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()




setuptools.setup(
    name='brfinance_v2',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.8',
    author='Leandro Eloy Sousa',
    author_email='leandroeloysousa@gmail.com',
    description=(
        'Biblioteca em Python com o objetivo de facilitar o acesso a '
        'dados financeiros periódicos de empresas brasileiras (B3/CVM).'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/leeloy84/brFinance_v2',
    project_urls={
        "Bug Tracker": "https://github.com/leeloy84/brFinance_v2/issues",
        "Source Code": "https://github.com/leeloy84/brFinance_v2",
    },
    install_requires=[
        'aiohttp>=3.11.12',
        'requests>=2.32.5',
        'pandas>=3.0.0',
        'beautifulsoup4>=4.13.3',
        'lxml>=5.3.1',
        'openpyxl>=3.1.2'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)
