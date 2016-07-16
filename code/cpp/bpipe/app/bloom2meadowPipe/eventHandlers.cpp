// bloom2meadowPipe: main.cpp
// Application for streaming data from a Managed Bloomberg B-Pipe to the standard output

// eventHandlers for handling the Bloomberg subscription.  Set in main.cpp with the subscribedBpipe::setEventHandler( . )
// Add a declaration to eventHandlers.h to ensure accessibility from main.cpp

#include <blpapi_message.h>
#include "eventHandlers.h"
#include "mmaparray.h"

#include <iostream>
#include <string>
#include <sstream>

std::map<int, std::string> handlerEIDaliasMap;

void exampleHandler(Event event)
{
	MessageIterator msgIter(event);
	while (msgIter.next()) {
		Message msg = msgIter.message();
		if (event.eventType() == Event::SUBSCRIPTION_STATUS ||
			event.eventType() == Event::SUBSCRIPTION_DATA) {
				const char *topic = (char *)msg.correlationId().asPointer();
				std::cout << topic << " - ";
		}
		msg.print(std::cout) << std::endl;
	}
}

void testHandler(Event event){
	MessageIterator msgIter(event);
	while (msgIter.next()){
		Message msg = msgIter.message();
		using namespace std;
		cout << "messageType().string(): " << msg.messageType().string() << endl;
		cout << "topicName(): " << msg.topicName() << endl;
		if (event.eventType() == Event::SUBSCRIPTION_STATUS ||
			event.eventType() == Event::SUBSCRIPTION_DATA) {
				cout << "msg.correlationId().asPointer(): " << (char *)msg.correlationId().asPointer() << endl;
		}

		//		cout << "service().name(): " << msg.service().name() << endl;
		cout << "numCorrelationIds: " << msg.numCorrelationIds() << endl;
		cout << "numElements: " << msg.numElements() << endl;
		cout << "asElement().print(cout)" << endl; 
		msg.asElement().print(cout,2);
	}
}

void selectedElements(Event event){
	MessageIterator msgIter(event);
	while (msgIter.next()){
		Message msg = msgIter.message();
		using namespace std;
		if (event.eventType() != Event::SUBSCRIPTION_STATUS &&
			event.eventType() != Event::SUBSCRIPTION_DATA)
			continue;
	
		cout << (char *)msg.correlationId().asPointer() << endl;
	
		if( msg.hasElement("EID") )
		{
			cout << "\t EID: " << msg.getElementAsInt32("EID") << endl;
		}
		if( msg.hasElement("LAST_PRICE") )
		{
			cout << "\t LAST_PRICE: " << msg.getElementAsString("LAST_PRICE") << endl;
		}
	}
}

const char messageStart = '(';
const char messageEnd = ')';
const char stringStart = '\'';
const char stringEnd = '\'';
const char itemSep = ',';

// Helper function
std::string date2str( Datetime time ){
  std::stringstream ss;
  ss << messageStart
     << time.hours() << itemSep
     << time.minutes() << itemSep
     << time.seconds() << itemSep
     << time.milliSeconds()
     << messageEnd;
  return ss.str();
}

void handleBid(Message & msg, std::stringstream & ss)
{
  ss << msg.getElementAsFloat64("BID") << itemSep
     << msg.getElementAsInt32("BID_SIZE") << itemSep
     << date2str(msg.getElementAsDatetime("BID_UPDATE_STAMP_RT"));
}

void handleAsk(Message & msg, std::stringstream & ss)
{
  ss << msg.getElementAsFloat64("ASK") << itemSep
     << msg.getElementAsInt32("ASK_SIZE") << itemSep
     << date2str(msg.getElementAsDatetime("ASK_UPDATE_STAMP_RT"));
}

void handleTrade(Message & msg, std::stringstream & ss)
{
  //TODO check new
    ss << msg.getElementAsFloat64("LAST_PRICE") << itemSep
       << msg.getElementAsInt32("EVT_TRADE_SIZE_RT") << itemSep 
       << date2str(msg.getElementAsDatetime("TRADE_UPDATE_STAMP_RT"));
}

// "TRADE", "ASK", "BID", "SYMBOL", "CUM_TRADE", "TRADE_QUOTE_COUNT", "LAST_EVENT_TIME"

void updateLastTime( Datetime time )
{
	using namespace std;
	name2mmap[ "LAST_EVENT_TIME-0" ]->access()[ 0 ] = time.milliSeconds();
	name2mmap[ "LAST_EVENT_TIME-0" ]->access()[ 1 ] = time.seconds();
	name2mmap[ "LAST_EVENT_TIME-0" ]->access()[ 2 ] = time.minutes();
}

int eid( Message & msg )
{
	// Now handle common stuff EID
	using namespace std;
	map<int,string>::iterator thisEID;
	thisEID = handlerEIDaliasMap.find( msg.getElementAsInt32("EID") );
	if( thisEID == handlerEIDaliasMap.end() ) {
		cerr << "Unknown EID: " << msg.getElementAsInt32("EID") << stringEnd << std::endl;
		return -1;
	}
	else {
		return atoi( thisEID->second.c_str() );
	}
}

void handleAskMMap(Message & msg )
{
	int ix = atoi( (char*) msg.correlationId().asPointer() );
	float price = msg.getElementAsFloat64("ASK");
	float size 	= msg.getElementAsInt32("ASK_SIZE");
	name2mmap[ "ASK-0" ]->access()[ ix ]  = price;
	name2mmap[ "ASK-1" ]->access()[ ix ] += size * 100;
	name2mmap[ "ASK-2" ]->access()[ ix ]  = size * 100;

	name2mmap[ "TRADE_QUOTE_COUNT-1" ]->access()[ ix ] += 1;

	updateLastTime( msg.getElementAsDatetime("ASK_UPDATE_STAMP_RT") );
}

void handleBidMMap(Message & msg )
{
	int ix = atoi( (char*) msg.correlationId().asPointer() );
	float price = msg.getElementAsFloat64("BID");
	float size = msg.getElementAsInt32("BID_SIZE");

	name2mmap[ "BID-0" ]->access()[ ix ]  = price;
	name2mmap[ "BID-1" ]->access()[ ix ] += size * 100;
	name2mmap[ "BID-2" ]->access()[ ix ]  = size * 100;
	updateLastTime( msg.getElementAsDatetime("BID_UPDATE_STAMP_RT") );
}

void handleTradeMMap(Message & msg )
{
	int ix = atoi( (char*) msg.correlationId().asPointer() );
	float price = msg.getElementAsFloat64("LAST_PRICE");
	float size 	= msg.getElementAsInt32("EVT_TRADE_SIZE_RT");
	std::string date = date2str(msg.getElementAsDatetime("TRADE_UPDATE_STAMP_RT"));

	name2mmap[ "TRADE-0" ]->access()[ ix ]  = price;
	name2mmap[ "TRADE-1" ]->access()[ ix ] += size;
	name2mmap[ "TRADE-2" ]->access()[ ix ]  = size;

	name2mmap[ "CUM_TRADE-0" ]->access()[ ix ] += price * size;
	name2mmap[ "CUM_TRADE-1" ]->access()[ ix ] += size;
	name2mmap[ "CUM_TRADE-2" ]->access()[ ix ]  = price * size;

	name2mmap[ "TRADE_QUOTE_COUNT-0" ]->access()[ ix ] += 1;

	updateLastTime( msg.getElementAsDatetime("TRADE_UPDATE_STAMP_RT") );
}

void bidAskTradeMMappedElements(Event event)
{
	MessageIterator msgIter(event);
	std::string msgStr;

	while (msgIter.next()){
	  Message msg = msgIter.message();
	  using namespace std;

	  try{
		if( !msg.hasElement("MKTDATA_EVENT_TYPE") ){
		  continue;
		}

		msgStr = msg.getElementAsString("MKTDATA_EVENT_TYPE");

    cout << msg << "\n";

		if(msgStr == "QUOTE"){
		  msgStr = msg.getElementAsString("MKTDATA_EVENT_SUBTYPE");
		  if(msgStr == "ASK"){
		    handleAskMMap(msg);
		  }
		  else if(msgStr == "BID"){
		    handleBidMMap(msg);
		  }
		  else{
		    throw "Unknown MKTDATA_EVENT_SUBTYPE";
		  }
		}

		else if(msgStr == "TRADE"){
		  handleTradeMMap(msg);
		}
		else if(msgStr == "SUMMARY")
		  continue;
		else{
		  cerr  << "Unknown MKTDATA_EVENT_TYPE: " << msgStr << endl;
		  continue;
		    //		  throw "Unknown MKTDATA_EVENT_TYPE";
		}

	}

	catch( const Exception & e ) {
	    std::cerr << "Caught the exception: " << e.description()
		      << std::endl;
	    if( e.description().find("Attempt to access unavailable sub-element") != std::string::npos){
	      std::cerr << (char *)msg.correlationId().asPointer() << " - ";
	      msg.print(std::cerr);
	    }
	    else if( e.description().find("Attempt to access an empty scalar element") != std::string::npos ){
	      std::cerr << (char *)msg.correlationId().asPointer() << " - ";
	      msg.print(std::cerr);
	    }
	    else
	      throw e;
		}
	}
}

void bidAskTradeElements(Event event){
	MessageIterator msgIter(event);
	while (msgIter.next()){
	  Message msg = msgIter.message();
	  using namespace std;

	  try{
		if( !msg.hasElement("MKTDATA_EVENT_TYPE") ){
		  continue;
		}

		std::stringstream ss;
		ss << messageStart ;
		string msgStr;

		msgStr = msg.getElementAsString("MKTDATA_EVENT_TYPE");

		if(msgStr == "QUOTE"){
		  msgStr = msg.getElementAsString("MKTDATA_EVENT_SUBTYPE");
		  if(msgStr == "ASK"){
		    ss << stringStart << "A" << stringEnd << itemSep
		       << (char *)msg.correlationId().asPointer() << itemSep;
		    handleAsk(msg,ss);
		  }
		  else if(msgStr == "BID"){
		    ss << stringStart << "B" << stringEnd << itemSep
		       << (char *)msg.correlationId().asPointer() << itemSep;
		    handleBid(msg,ss);
		  }
		  else{
		    throw "Unknown MKTDATA_EVENT_SUBTYPE";
		  }
		}
		else if(msgStr == "TRADE"){
		  ss << stringStart << "T" << stringEnd << itemSep
		     << (char *)msg.correlationId().asPointer() << itemSep;
		  handleTrade(msg,ss);
		}
		else if(msgStr == "SUMMARY")
		  continue;
		else{
		  cerr  << "Unknown MKTDATA_EVENT_TYPE: " << msgStr << endl;
		  continue;
		    //		  throw "Unknown MKTDATA_EVENT_TYPE";
		}

		// Now handle common stuff EID
		map<int,string>::iterator thisEID;
		thisEID = handlerEIDaliasMap.find( msg.getElementAsInt32("EID") );
		if( thisEID == handlerEIDaliasMap.end() )
		  ss << itemSep << stringStart << "Unknown EID: " 
		     << msg.getElementAsInt32("EID") << stringEnd << messageEnd;
		else
		  ss << itemSep << thisEID->second << messageEnd;

		cout << ss.str() << endl;
	  }catch( const Exception & e ){
	    std::cerr << "Caught the exception: " << e.description()
		      << std::endl;
	    if( e.description().find("Attempt to access unavailable sub-element") != std::string::npos){
	      std::cerr << (char *)msg.correlationId().asPointer() << " - ";
	      msg.print(std::cerr);
	    }
	    else if( e.description().find("Attempt to access an empty scalar element") != std::string::npos ){
	      std::cerr << (char *)msg.correlationId().asPointer() << " - ";
	      msg.print(std::cerr);
	    }
	    else
	      throw e;
	  }
	}
}

void simpleStatusEventHandler(Event event){
  using namespace std;

  MessageIterator msgIter(event);
  
  while (msgIter.next()) {
    Message msg = msgIter.message();
    const char *topic = (char *)msg.correlationId().asPointer();

    std::stringstream ss;
    ss << messageStart << stringStart << 'S' << stringEnd << itemSep
       << stringStart << topic << stringEnd << itemSep
       << stringStart << msg.messageType().string() << stringEnd << messageEnd;

    if( strcmp(msg.messageType().string(),"SubscriptionStarted") != 0 ){
      cerr << topic << " - " ; 
      msg.print(std::cerr);
    }
    
    cout << ss.str() << endl;
  }
}

void statusEventHandlerMMap(Event event){
  using namespace std;

  MessageIterator msgIter(event);
  
  while (msgIter.next()) {
    Message msg = msgIter.message();

	int  ix = atoi( (char*) msg.correlationId().asPointer() );

	float subscribed;
    if( strcmp( msg.messageType().string(),"SubscriptionStarted") != 0 ){
		subscribed = 0.0;
	} else {
		subscribed = 1.0;
	}

	name2mmap[ "SYMBOL-0" ]->access()[ ix ] = subscribed;
  }
}
