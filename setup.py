from setuptools import setup, find_packages

# See:
# https://packaging.python.org/guids/distruting-packages-using-setuptools

setup(
    name="cigarbox",
    version="0.1.0",
    description="utility libraries",
    long_description="utility libraries",
    long_description_content_type="text/plain",
    url="https://github.com/smherwig/cigarbox",
    author="Stephen M. Herwig",
    author_email="smherwig@cs.umd.edu",
    classifiers=[
        "Developement Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        ],
    keywords="data structures",
    packages=find_packages(),
    python_requires='>=2.7',
    )

