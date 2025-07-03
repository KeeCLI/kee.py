#!/usr/bin/env python3
"""
Setup script for Kee - AWS CLI session manager
"""

from setuptools import setup
import os


# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Kee - AWS CLI session manager"


setup(
    name='kee',
    version='1.0.0',
    description='AWS CLI session manager with SSO support',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Stefan Aichholzer',
    author_email='theaichholzer@gmail.com',
    url='https://github.com/keecli/kee.py',
    py_modules=['kee'],
    python_requires='>=3.8',
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        'test': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'pytest-mock>=3.0',
        ],
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'pytest-mock>=3.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.800',
        ],
    },
    entry_points={
        'console_scripts': [
            'kee=kee:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    keywords='aws cli sso session manager credentials',
)
