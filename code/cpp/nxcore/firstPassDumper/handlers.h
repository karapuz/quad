#include <vector>
#include "NxCoreAPI_Class.h"
#include <list>
#include <boost/unordered_set.hpp>
#include <string>

int OnPriceEvent(const NxCoreSystem*,const NxCoreMessage*, unsigned int messageType);

typedef boost::unordered_set< std::string > symbSet;

extern NxCoreClass * ptrNxCore;
extern symbSet * inFileSymbs;

void dumpSymbs( symbSet & symbs );
