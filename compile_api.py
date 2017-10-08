from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("api/biome_c.pyx")
)
