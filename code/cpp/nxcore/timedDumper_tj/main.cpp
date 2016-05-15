#include <stdlib.h>
#include "NxCoreAPI_Class.h"
#include <stdio.h>
#include <map>
#include <fstream>
#include <string>

#include "handlers.h"
#include "correctionList.h"

NxCoreClass NxCore;

int callback(const NxCoreSystem* system, const NxCoreMessage* msg);

int null(const NxCoreSystem *, const NxCoreMessage*){
  return  NxCALLBACKRETURN_CONTINUE;  
}

int init(NxCoreClass * curNxCore){
  //  reportTimeQueue.push_back(3600000 * 13);  // 4:00pm
  //  reportTimeQueue.push_back(3600000 * 24);  // Just to run the tape to the end rather than generate the exception
  reportTimeQueue.sort();

  ptrNxCore = curNxCore;
}

void initializeMaptest(){
  priceList empty;
  //symbIndexMap["eAAPL"] = empty;
  //symbIndexMap["eIBM"] = empty;
  //symbIndexMap["eWIN"] = empty;
  symbIndexMap["eSPY"] = empty;
}

void initializeMap(){
  priceList empty;
  ifstream inFile;
  //inFile.open("/local/home/tjia/chloe/code/cpp/nxcore/timedDumper_tj/SP501.txt");
  inFile.open("/home/tjia/chloe/code/cpp/nxcore/timedDumper_tj/SP501.txt");
  //std::string symbol;
  char cSymb[256];
  while (inFile.good()){
    inFile.getline(cSymb, 256);
    //cout << cSymb << endl; 
    symbIndexMap[cSymb] = empty;  
  }
  inFile.close();
  //boost::unordered_map<string, priceList>::iterator it;
  //cout << "(\'X\'";
  //for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++)
  //  cout << "," << "\'" << it->first << "\'" ;
  //cout << ")" << endl;
}



int main( int argc, char * argv[] ){

  if( argc < 2 ){
    printf("Usage: DataDumper <name-of-tapefile> [<name-of-correction-dump>]\n");
    return 1;
  }
  if( argc >= 3 ){
    if(!buildCorrectListsFromFile(canceledTrades, insertedTrades, argv[2])){
      fprintf(stderr,"Error reading correction list file\n");
      return 1;
    }
  }

  fprintf(stderr,"Input reporting times in milliseconds from midnight.  Two new lines to end\n");
  unsigned long reportTime;
  char buf[100];
  buf[0] = ' ';
  buf[1] = '\0';
  priceList zeroList;
  while( fgets(buf, sizeof(buf), stdin) != NULL && buf[0] != '\n' && strlen(buf) > 0){
    //Remove newline character
    //buf[strlen(buf) - 1] = '\0'; //No need when useing atol
    reportTime = atol(buf);
    if(reportTime)
      reportTimeQueue.push_back(reportTime);
  }

  //initializeMaptest();
  initializeMap();

  unsigned flags = 0;
  fprintf(stderr,"Processing the tape: %s\n", argv[1]);
  std::string fname = argv[1];

  if(NxCore.LoadNxCore("libnx.so")) {

    unsigned int apiVersion = NxCore.APIVersion();

    fprintf(stderr,"NxCore Library loaded: v.%u.%u.%u\n",
	    NxCORE_VER_MAJOR(apiVersion),
	    NxCORE_VER_MINOR(apiVersion),
	    NxCORE_VER_BUILD(apiVersion));

    init(&NxCore);
    fprintf(stderr,"Return value %d\n", 
	    NxCore.ProcessTape(fname.c_str(), 0, flags,0,(NxCoreCallback)&callback) );

  } else {
    fprintf(stderr,"Failed to load libnx.so. Make sure it's in your library path\n");
    return 1;
  }
  //    printf("Done Tape\n");
}

int callback(const NxCoreSystem* system, const NxCoreMessage* msg)
{
  int ret =  NxCALLBACKRETURN_CONTINUE;
  switch (msg->MessageType)
    {
    case NxMSG_STATUS:
      ret	= null(system,msg); //OnStatus(system,msg);
      break;
    case NxMSG_EXGQUOTE:
      ret	= OnPriceEvent(system,msg,NxMSG_EXGQUOTE);
      break;
    case NxMSG_MMQUOTE:
      ret	= OnPriceEvent(system,msg,NxMSG_MMQUOTE); //OnMMQuote(system,msg);
      break;
    case NxMSG_TRADE:
      ret	= OnPriceEvent(system,msg,NxMSG_TRADE); //OnTrade(system,msg);
      break;
    case NxMSG_CATEGORY:
      ret	= null(system,msg); //OnCategory(system,msg);		
      break;
    case NxMSG_SYMBOLCHANGE:
      ret	= null(system,msg); //OnSymbolChange(system,msg);	
      break;
    case NxMSG_SYMBOLSPIN:
      ret	= null(system,msg); //OnSymbolSpin(system,msg);	
      break;
    }
  return ret;
}

