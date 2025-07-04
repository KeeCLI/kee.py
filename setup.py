#!/usr/bin/env python3
"""
Setup script for Kee - AWS CLI Session Manager
"""

from setuptools import setup
import os


# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Kee - AWS CLI Session Manager"


setup(
    name='kee',
    version='1.0.0',
    description='AWS CLI Session Manager with SSO support',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Stefan Aichholzer',
    author_email='theaichholzer@gmail.com',
    url='https://github.com/keecli/kee.py',
    py_modules=['kee'],
    python_requires='>=3.7',
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
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
        'Programming Language :: Python :: 3.7',
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
