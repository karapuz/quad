#include <vector>
#include "NxCoreAPI_Class.h"
#include <list>
#include <set>

int OnPriceEvent(const NxCoreSystem*,const NxCoreMessage*, unsigned int messageType);

extern std::set<std::string> symbSet;
extern std::list<unsigned long> reportTimeQueue;

extern NxCoreClass * ptrNxCore;
