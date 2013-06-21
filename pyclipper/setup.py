from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

  

ext =	Extension("pyclipper", 
                sources=["pyclipper.pyx", "./../cpp/clipper.cpp"],
	          	libraries=["stdc++"], # "ln", "util" ,"pthread" ,"rt" 
                language="c++",              # this causes Pyrex/Cython to create C++ source
				# library_dirs=["."],
				include_dirs=["./../cpp"],
				)


setup(
        ext_modules=[ext],
        cmdclass = {'build_ext': build_ext},
)


