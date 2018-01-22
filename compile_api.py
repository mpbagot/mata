from distutils.core import setup
from Cython.Build import cythonize

setup(
#    ext_modules = cythonize("api/*.pyx")
    ext_modules = cythonize("api/*.pyx")+cythonize("api/gui/*.pyx")
)
