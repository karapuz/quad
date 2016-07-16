#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#include <errno.h>
#include <string.h>
#include <map>

#include <memory>

#include <boost/shared_ptr.hpp>
#include <boost/filesystem.hpp>
#include <iostream>
namespace fs = boost::filesystem;

class MMapArray 
{
	private:
		int    fd;
		float *map;
		bool   read;
		int    n, l;
		std::string path;

	protected:
		void initRead();
		void initWrite();

	public:
		MMapArray( const char* path, int n, bool read );
		~MMapArray();
		float *access() { return this->map; }
		int size(){ return this->n; }
};

typedef boost::shared_ptr<MMapArray> MMapArrayPtr;
extern std::map< std::string, MMapArrayPtr > name2mmap;
void initName2MMap( const std::string & );
