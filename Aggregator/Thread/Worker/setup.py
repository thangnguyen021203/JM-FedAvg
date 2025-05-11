from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("Unmask_Module.pyx", language_level="3")
)
