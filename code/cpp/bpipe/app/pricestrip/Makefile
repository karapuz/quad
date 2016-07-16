# Makefile for examples
UNAME := $(shell uname)
# BLOOMAPI_DIR := /opt/vendorLibs/bloombergAPI/APIv3/C++API
BLOOMAPI_DIR := /opt/vendorLibs/bloombergAPI/APIv3/C++API/blpapi_cpp_3.10.7.1

#ifdef IS_64BIT
BITS=64
#else
#BITS=32
#endif

BUILD_DIR:=$(UNAME)

ifeq ($(UNAME), SunOS)
CXX=CC
CXXFLAGS+=-m$(BITS) -mt -D_POSIX_PTHREAD_SEMANTICS -g0
endif

ifeq ($(UNAME), Linux)
CXXFLAGS+=-m$(BITS) -D_POSIX_PTHREAD_SEMANTICS -g
endif

all: bbgpricestrip

clean:
	cd $(BUILD_DIR); $(RM) bbgpricestrip

bbgpricestrip: $(BUILD_DIR)/bbgpricestrip

$(BUILD_DIR)/bbgpricestrip: $(wildcard *.cpp) $(wildcard *.h)
	$(LINK.cc) -I$(BLOOMAPI_DIR)/include $(wildcard *.cpp) \
	-o $(BUILD_DIR)/bbgpricestrip \
	-L$(BLOOMAPI_DIR)/Linux -lblpapi3_$(BITS) \
	-lboost_filesystem -lboost_system
