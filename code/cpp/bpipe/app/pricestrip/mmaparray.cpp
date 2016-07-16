#include "mmaparray.h"

MMapArray::MMapArray( const char* path, int n, bool read )
{
	this->n = n;
	this->l = n * sizeof(float);
	this->path = path;
	this->read = read;
	if ( read )
		initRead();
	else
		initWrite();
	std::cout << "MMapArray::init opening fd=" << this->fd << " path=" << this->path << std::endl;
}

MMapArray::~MMapArray()
{
	if (munmap(this->map, this->l ) == -1) {
		perror("Error un-mmapping the file");
	}
	close(this->fd);
	std::cout << "closing fd=" << this->fd << " path=" << this->path << std::endl;
}

void MMapArray::initRead()
{
	this->fd = open(this->path.c_str(), O_RDONLY);

	if ( this->fd == -1 ) {
		perror("readData: Error opening file for reading");
		exit(EXIT_FAILURE);
	}

	this->map = ( float* )mmap( 0, this->l, PROT_READ, MAP_SHARED, this->fd, 0 );
	if (this->map == MAP_FAILED) {
		close(this->fd);
		perror("MMapArray::initRead: Error mmapping the file");
		exit(EXIT_FAILURE);
	}
}

void MMapArray::initWrite()
{
	int prot = ( PROT_READ | PROT_WRITE );
	int flags = MAP_SHARED;

	this->fd = open(this->path.c_str(), O_RDWR | O_CREAT | O_TRUNC, S_IRUSR| S_IWUSR );
	if (lseek(this->fd, this->l-1, SEEK_SET) == -1) {
		int myerr = errno;
		printf("MMapArray::initWrite: lseek failed (errno %d %s)\n", myerr, strerror(myerr));
		exit(EXIT_FAILURE);
	}
	int result = write(this->fd, "", 1);
	
	if (this->fd == 0) {
		int myerr = errno;
		printf("MMapArray::initWrite: open failed (errno %d %s)\n", myerr, strerror(myerr));
		exit(EXIT_FAILURE);
	}

	this->map = ( float* )mmap( 0, this->l, PROT_WRITE, MAP_SHARED, this->fd, 0 );
	for ( int i=0; i < this->n; i ++ )
		this->map[ i ] = 0.0;
}


const int   _centerLen = 7;
const char* _centerString[] = {
	"TRADE", "ASK", "BID", "SYMBOL", "CUM_TRADE", "TRADE_QUOTE_COUNT", "LAST_EVENT_TIME"
};
std::map< std::string, MMapArrayPtr > name2mmap;
void initName2MMap( const std::string & root )
{
	int i, j;
	fs::path dir( root );
	char mmapnamebuf[ 20 ];
	char varName[ 20 ];
	for (i = 0; i < _centerLen; ++i) 
	{
		for (j = 0; j < 3; ++j )
		{
    		std::string fileName = _centerString[ i ];
    		sprintf( mmapnamebuf, "-%d.mmap", j );
    		sprintf( varName, "%s-%d", fileName.c_str(), j );
    		fileName += mmapnamebuf;
    		fs::path file ( fileName );
    		fs::path full_path = dir / file;
				const char* filepath = full_path.string().c_str();
	    	MMapArrayPtr a( new MMapArray( filepath, 40000, false ) );
	    	std::string name( varName );
	    	name2mmap[ name ] = a;
    		std::cout << "MMapArray::initMap " << varName << "->" << full_path << std::endl;
		}
	}
}

