from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    ext_modules=cythonize("Mask_Module.pyx", language_level="3"),
    include_dirs=[numpy.get_include()],
)
