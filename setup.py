import os
import re
import setuptools

def read(f):
    return open(f, 'r', encoding='utf-8').read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('django_msal')

setuptools.setup(
    name='django_msal',
    version=version,
    author='Matt Langeman',
    author_email='Matthew_Langeman@dai.com',
    description='A small Django app that enables SSO with Microsoft Azure Active Directory',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/dai-ictgeo/django_msal',
    keywords='django auth msal microsoft azure',
    install_requires=['Django >= 2.2',
                      'msal >= 1.4.3'
                    ],
    python_requires=">=3.6",
    packages=setuptools.find_packages(),
    package_data={
        "django_msal": ["templates/*.html"],
    }
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ],
)
