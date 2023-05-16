import pyisotools
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    longDescription = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as r:
    requires = [x for x in r]

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
    # install_requires=[
    #     "bs4",
    #     "chardet",
    #     "dolreader",
    #     "qdarkstyle",
    #     "sortedcontainers",
    #     "pillow",
    #     "pygithub",
    #     "PySide6"
    # ],
    install_requires=requires,

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.8',
)
