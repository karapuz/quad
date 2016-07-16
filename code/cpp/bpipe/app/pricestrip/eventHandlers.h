#ifndef _EVENTHANDLERS_H_
#include <blpapi_event.h>
#include <map>
#include <string>

using namespace BloombergLP;
using namespace blpapi;

extern std::map<int, std::string> handlerEIDaliasMap;

void exampleHandler(Event event);

void testHandler(Event event);

void selectedElements(Event event);

void bidAskTradeElements(Event event);

void bidAskTradeMMappedElements(Event event);

void simpleStatusEventHandler(Event event);

void statusEventHandlerMMap(Event event);

#endif

