# Makefile for examples
UNAME := $(shell uname)
BLOOMAPI_DIR := /opt/vendorLibs/bloombergAPI/APIv3/C++API

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

all: bloom2MeadowPipe

clean:
	cd $(BUILD_DIR); $(RM) bloom2MeadowPipe

bloom2MeadowPipe: $(BUILD_DIR)/bloom2MeadowPipe

$(BUILD_DIR)/bloom2MeadowPipe: $(wildcard *.cpp) $(wildcard *.h)
	$(LINK.cc) -I$(BLOOMAPI_DIR)/include $(wildcard *.cpp) \
	-o $(BUILD_DIR)/bloom2MeadowPipe \
	-L$(BLOOMAPI_DIR)/Linux -lblpapi3_$(BITS) \
	-lboost_filesystem
