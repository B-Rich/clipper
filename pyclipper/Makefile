
default : usage

usage :
	@echo "Usage:"
	@echo " make clipper.pyx"
	@echo " make clipper.o"
	@echo " make test.svg"

clipper.pyx :
	python hpp2pyx.py ../cpp/clipper.hpp clipper.pyx

clipper.o : clipper.pyx
	python setup.py build_ext --inplace

test.svg : clipper.o
	python clipper_demo.py

clean :
	$(RM) *.pyc
	$(RM) clipper.cpp
	$(RM) clipper.pyx
	$(RM) clipper.so
