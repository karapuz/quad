NX_DIR=/opt/vendorLibs/NxCore

all:main.cpp
	g++ main.cpp handlers.cpp correctionList.cpp -I${NX_DIR} -L${NX_DIR} -ldl -lnx -o nxCoreParse -g
clean:
	rm -f nxCoreParse
