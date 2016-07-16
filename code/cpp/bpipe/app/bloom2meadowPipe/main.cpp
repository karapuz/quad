// bloom2meadowPipe: main.cpp
// Application for streaming data from a Managed Bloomberg B-Pipe to the standard output

// main.cpp: program entry point

// Command line usage:
// bloom2meadowPipe -h <hostname:port> -n <applicationName>
// Where hostname:port corresponds to the server with the B-Pipe installation
// and where applicationName is the name authorized in Bloombergs EMRS
// Example: bloom2meadowPipe -h localhost:8195 -n MCM:TestApplication

// Program takes from Standard input the list of Bloomberg FLDS and list of Securities.

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <stdio.h>

#include "subscribedBpipe.h"
#include "eventHandlers.h"
#include "mmaparray.h"

using namespace std;
#define MAX_LINE_LENGTH 200
#define DEFAULT_PORT 8194
/* #define DEFAULT_PORT 8185 */

// const char* root = "/home/ipresman/projects/winston/shared/NYC_1/FIRM";

void parseArgs(configOptions & config, int argc, char ** argv)
{
	for (int i = 1; i < argc; ++i) {
		if (i == 0) 
			continue; // ignore the program name.

		if (!std::strcmp(argv[i],"-h") && i + 1 < argc) { // Host of form -h hostname:port
			string hostArg = argv[i+1];
			size_t pos;
			pos = hostArg.find(':');
			if( pos == string::npos) // Not found
			{
				config.bpipeHost = hostArg;
				config.bpipePort = DEFAULT_PORT;
			}
			else
			{
				config.bpipeHost = hostArg.substr(0,pos);
				config.bpipePort = atoi(hostArg.substr(pos+1).c_str());
			}
			i++;
		}
		else if (!std::strcmp(argv[i],"-n") &&  i + 1 < argc) {
			config.applicationName = argv[++i];
		} 
		else if (!std::strcmp(argv[i],"-p") &&  i + 1 < argc) {
			config.rootPath = argv[++i];
			cerr << "parseArgs: rootPath=" << config.rootPath  << endl;
		} 
	}
}

void printUsage(){
  cout << "bloom2MeadowPipe -h <hostname:port> -n <ApplicationName> -p <mmap directory path>" << endl;
}

int main(int argc, char **argv)
{
	configOptions configOpts;
	cout << "Meadowood Bloomberg B-Pipe Interface" << endl;
	
	parseArgs(configOpts, argc, argv);
	if(configOpts.bpipeHost.length() == 0){
	  printUsage();
	  return -1;
	}

	initName2MMap( configOpts.rootPath );

	// Connect to Pipe.
	subscribedBpipe thePipe;
	try{
	  if(!thePipe.init(configOpts))
	    {
	      cerr << "Pipe initialization failed!" << endl;
	      return -1;
	    }
	}catch(blpapi::Exception & e){
	  cerr << "Failed to initialize connection to BPipe.  "
	       << "Caught Exception: " << e.description() << endl;
	  return -1;
	}

	cout << "Enter the desired Bloomberg Fields (see FLDS<Go> in Bloomberg).  Separate by new lines, two newlines end." << endl;
	vector<string> vec;
	vector<stringWithAlias> secs;
	string line;
	getline(cin,line);
	while(line.length() > 0)
	{
		vec.push_back(line);
		getline(cin,line);
	}
	//Required fields are EID and MKTDATA_EVENT_TYPE, MKTDATA_EVENT_SUBTYPE
	vec.push_back("EID");
	vec.push_back("MKTDATA_EVENT_TYPE");
	vec.push_back("MKTDATA_EVENT_SUBTYPE");

	thePipe.setFields(vec);
	
	vec.clear();

	cout << "Enter the desired securities and alias (eg IBM US Equity,aliasIBM ).  Two new lines to end. " << endl;
	getline(cin,line);
	size_t delimLoc;
	stringWithAlias curSec;
	while(line.length() > 0)
	{
	  delimLoc = line.find(',');
	  curSec.name = line.substr(0,delimLoc);
	  if( delimLoc == string::npos )
	    curSec.alias = line;
	  else
	    curSec.alias = line.substr(delimLoc + 1);

	  cout << "SEC = " << curSec.name << "ALIAS =" << curSec.alias << "\n";

	  secs.push_back(curSec);
	  getline(cin,line);
	}
	thePipe.setSecurities(secs);
	cout << "Subscribing" << endl;
	thePipe.subscribe();

	cout << "Enter the set of approved EIDs and their alias (eg 39491,DelayedNYSE ).  Two new lines to end. "  << endl;
	getline(cin,line);
	string eidStr;
	while(line.length() > 0)
	{
	  delimLoc = line.find(',');
	  eidStr = line.substr(0,delimLoc);
	  if( delimLoc == string::npos )
	    handlerEIDaliasMap[atoi(eidStr.c_str())] = eidStr; //Set the alias to a string of the number if no delimeter
	  else
	    handlerEIDaliasMap[atoi(eidStr.c_str())] = line.substr(delimLoc + 1);
	  cout << "EID = " << eidStr << "\n";
	  getline(cin,line);
	}
	
	// thePipe.setEventHandler(bidAskTradeElements);
	thePipe.setEventHandler( bidAskTradeMMappedElements );

	// thePipe.setStatusEventHandler(simpleStatusEventHandler);
	thePipe.setStatusEventHandler( statusEventHandlerMMap );

	try{
	  thePipe.startEventLoop();
	}
	catch( char const * str ){
	  cout << str << endl;
	}

    return 0;
}
