import pyisotools
import setuptools
import os

with open("README.md", "r", encoding="utf-8") as fh:
    longDescription = fh.read()

setuptools.setup(
    name='pyisotools',
    version=pyisotools.__version__,    
    description='Simple python library for extracting and rebuilding ISOs',
    long_description=longDescription,
    long_description_content_type="text/markdown",
    url='https://github.com/JoshuaMKW/pyisotools',
    author='JoshuaMK',
    author_email='joshuamkw2002@gmail.com',
    license='GNU General Public License v3.0',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=["dolreader"],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.8',
)