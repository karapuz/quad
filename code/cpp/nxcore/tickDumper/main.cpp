#include <stdlib.h>
#include "NxCoreAPI_Class.h"
#include <stdio.h>

#include "handlers.h"

NxCoreClass NxCore;

int callback(const NxCoreSystem* system, const NxCoreMessage* msg);

int null(const NxCoreSystem *, const NxCoreMessage*){
  return  NxCALLBACKRETURN_CONTINUE;  
}

int init(NxCoreClass * curNxCore){
  reportTimeQueue.sort();

  ptrNxCore = curNxCore;
}

int main( int argc, char * argv[] ){

  if( argc < 2 ){
    printf("Usage: DataDumper <name-of-tapefile>\n");
    return 1;
  }

  fprintf(stderr,"Input start and end times in milliseconds from midnight.  Two new lines to end\n");
  unsigned long reportTime;
  char buf[100];
  buf[0] = ' ';
  buf[1] = '\0';
  while( fgets(buf, sizeof(buf), stdin) != NULL && buf[0] != '\n' && strlen(buf) > 0){
    //Remove newline character
    //buf[strlen(buf) - 1] = '\0'; //No need when useing atol
    reportTime = atol(buf);
    if(reportTime)
      reportTimeQueue.push_back(reportTime);
  }

  if(reportTimeQueue.size() > 2){
    printf("Please enter only two times.  A start and a end\n");
    return 1;
  }

  fprintf(stderr,"Input symbol list in NxCore format: eg eIBM  Two new lines to end\n");
  buf[0] = ' ';
  buf[1] = '\0';
  while( fgets(buf, sizeof(buf), stdin) != NULL && buf[0] != '\n' && strlen(buf) > 0){
    buf[strlen(buf) - 1] = '\0'; // Remove new line character
    symbSet.insert(std::string(buf));
  }

  unsigned flags = 0;
  for(int i = 1 ; i < argc ; i ++){
    fprintf(stderr,"Processing the tape: %s\n", argv[i]);
    std::string fname = argv[i];

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
  }
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

