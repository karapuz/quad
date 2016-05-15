NX_DIR=/opt/vendorLibs/NxCore

EXEC_NAME=firstPassDump

all:main.cpp
	g++ main.cpp handlers.cpp -I${NX_DIR} -L${NX_DIR} -ldl -lnx -o ${EXEC_NAME} -g
clean:
	rm -f ${EXEC_NAME}
