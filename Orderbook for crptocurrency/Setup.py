from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("GetBook.pyx")
)

#python Setup.py build_ext --inplace