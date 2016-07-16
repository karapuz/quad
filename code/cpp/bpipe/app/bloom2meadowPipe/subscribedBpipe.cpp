// bloom2meadowPipe: main.cpp
// Application for streaming data from a Managed Bloomberg B-Pipe to the standard output

// subscribedBpipe.cpp: interaction with Bloomberg API.
// Chunks of code extracted from SimpleSubscriptionExample from Bloomberg.

#include "subscribedBpipe.h"
#include <iostream>

#include <blpapi_session.h>
#include <blpapi_correlationid.h>

const Name AUTHORIZATION_SUCCESS("AuthorizationSuccess");
const Name AUTHORIZATION_FAILURE("AuthorizationFailure");
const Name TOKEN_SUCCESS("TokenGenerationSuccess");
const Name TOKEN_FAILURE("TokenGenerationFailure");
const Name TOKEN("token");

const char *MKTDATA_SVC = "//blp/mktdata";
const char *AUTH_SVC = "//blp/apiauth";

// const std::string configOptions::authMethod = "OS_LOGON";
// const std::string configOptions::authMethod = "USER_APP";
const std::string configOptions::authMethod = "APPLICATION";
// const std::string configOptions::authMethod = "USER_APP";
//const std::string configOptions::authMethod = "USER_APP_KEY";

bool subscribedBpipe::init(configOptions config_in)
{
	config = config_in;
	if(!startSession())
		std::cerr << "Error in startSession()!" << std::endl;

	if (strcmp(authOptions.c_str(), "NONE")) {
		if (!authorize()) {
			std::cerr << "Error in authorize()" << std::endl;
			return false;
		}
	}

	if (!d_session->openService(MKTDATA_SVC)) {
		std::cerr <<"Failed to open " << MKTDATA_SVC << std::endl;
		return false;
	}

	return true;
}

bool subscribedBpipe::subscribe(){
	//// Build Field string
	//std::string fieldString;
	//for(std::vector<std::string>::iterator curField = bloombergFields.begin();
	//	curField != bloombergFields.end();
	//	curField++)
	//{
	//	fieldString += *curField + ",";
	//}
	//fieldString.resize(fieldString.size() - 1); // Remove trailing comma

	for(std::vector<stringWithAlias>::iterator curSec = securities.begin();
		curSec != securities.end();
		curSec++)
	{
		std::vector<std::string> empty;
		subscriptions.add(curSec->name.c_str(),bloombergFields,empty,CorrelationId((char*)curSec->alias.c_str()));
	}

	std::cout << "Sending subscriptions" <<  std::endl;
	if (!strcmp(authOptions.c_str(), "NONE")) {
		d_session->subscribe(subscriptions);
	} else {
		if (d_identity.getSeatType() == Identity::BPS) {
			std::cout << "BPS User" << std::endl;
		} else if (d_identity.getSeatType() == Identity::NONBPS) {
			std::cout << "NON-BPS User" << std::endl;
		} else if (d_identity.getSeatType() == Identity::INVALID_SEAT) {
			std::cout << "Invalid User" << std::endl;
		}
		d_session->subscribe(subscriptions, d_identity);
	}

	return true;
}

void subscribedBpipe::startEventLoop(){
  try{
	while (true) {
		Event event = d_session->nextEvent();
		if (event.eventType() == Event::SUBSCRIPTION_STATUS )
		  statusEventHandler(event);
		else if (event.eventType() == Event::SUBSCRIPTION_DATA)
		  eventHandler(event);
		else
		  std::cerr << "Unknown event type: " << event.eventType() << std::endl;
	}
  } catch (Exception & e) {
    std::cerr << "Unhandled Exception in Event Loop: " << e.description().c_str() << std::endl; 
  }
}


bool subscribedBpipe::startSession(){

	SessionOptions sessionOptions;


	std::cout << "Connecting to port " << config.bpipePort << " on server: " << config.bpipeHost << std::endl; 

    sessionOptions.setServerAddress(config.bpipeHost.c_str(), config.bpipePort , 0);

	sessionOptions.setServerPort(config.bpipePort);
	sessionOptions.setAutoRestartOnDisconnection(true);
	sessionOptions.setNumStartAttempts(1);
	authOptions = getAuthOptions();
	if (authOptions.size() > 0) {
		sessionOptions.setAuthenticationOptions(authOptions.c_str());
	}
	d_session = new Session(sessionOptions);

	if (!d_session->start()) {
		std::cerr << "Failed to connect!" << std::endl;
		return false;
	}

	return true;
}

// construct authentication option string
std::string subscribedBpipe::getAuthOptions()
{
	std::string authOptions;
	if (!std::strcmp(config.authMethod.c_str(),"APPLICATION")) { //  Authenticate application
		// Set Application Authentication Option
		authOptions = "AuthenticationMode=APPLICATION_ONLY;";
		authOptions+= "ApplicationAuthenticationType=APPNAME_AND_KEY;";
		// ApplicationName is the entry in EMRS.
		authOptions+= "ApplicationName=" + config.applicationName;
	} else if (!strcmp(config.authMethod.c_str(), "NONE")) {
		// do nothing
	} else if (!strcmp(config.authMethod.c_str(), "USER_APP")) {
		// Set User and Application Authentication Option
		authOptions = "AuthenticationMode=USER_AND_APPLICATION;";
		authOptions += "ApplicationAuthenticationType=APPNAME_AND_KEY;";
		authOptions += "ApplicationName=" + config.applicationName + ";";
		authOptions += "AuthenticationType=OS_LOGON";
		// ApplicationName is the entry in EMRS.
	} else if (!strcmp(config.authMethod.c_str(), "USER_APP_KEY")) {
		// Set User and Application Authentication Option
		authOptions = "AuthenticationMode=USER_AND_APPLICATION;";
		authOptions += "ApplicationAuthenticationType=APPNAME_AND_KEY;";
		authOptions += "ApplicationName=" + config.applicationName + ";";
		// authOptions += "AuthenticationType=OS_LOGON";
		// ApplicationName is the entry in EMRS.

	} else if (!strcmp(config.authMethod.c_str(), "DIRSVC")) {		
		// Authenticate user using active directory service property
		authOptions = "AuthenticationType=DIRECTORY_SERVICE;";
		authOptions += "DirSvcPropertyName=" + config.applicationName;
	} else {
		// Authenticate user using windows/unix login name
		authOptions = "AuthenticationType=OS_LOGON";
	}

	std::cout << "Authentication Options = " << authOptions << std::endl;
	return authOptions;
}

bool subscribedBpipe::authorize()
{
	EventQueue tokenEventQueue;
	d_session->generateToken(CorrelationId(), &tokenEventQueue);
	std::string token;
	Event event = tokenEventQueue.nextEvent();
	if (event.eventType() == Event::TOKEN_STATUS) {
		MessageIterator iter(event);
		while (iter.next()) {
			Message msg = iter.message();
			msg.print(std::cout);
			if (msg.messageType() == TOKEN_SUCCESS) {
				token = msg.getElementAsString(TOKEN);
			}
			else if (msg.messageType() == TOKEN_FAILURE) {
				break;
			}
		}
	}
	if (token.length() == 0) {
		std::cout << "Failed to get token" << std::endl;
		return false;
	}

	d_session->openService(AUTH_SVC);
	Service authService = d_session->getService(AUTH_SVC);
	Request authRequest = authService.createAuthorizationRequest();
	authRequest.set(TOKEN, token.c_str());

	EventQueue authQueue;
	d_identity = d_session->createIdentity();
	d_session->sendAuthorizationRequest(
		authRequest, &d_identity, CorrelationId(), &authQueue);

	while (true) {
		Event event = authQueue.nextEvent();
		if (event.eventType() == Event::RESPONSE ||
			event.eventType() == Event::REQUEST_STATUS ||
			event.eventType() == Event::PARTIAL_RESPONSE) {
				MessageIterator msgIter(event);
				while (msgIter.next()) {
					Message msg = msgIter.message();
					msg.print(std::cout);
					if (msg.messageType() == AUTHORIZATION_SUCCESS) {
						return true;
					}
					else {
						std::cout << "Authorization failed" << std::endl;
						return false;
					}
				}
		}
	}
}
