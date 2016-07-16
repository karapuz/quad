#include <string>
#include <vector>

#include <blpapi_session.h>

using namespace BloombergLP;
using namespace blpapi;

class stringWithAlias
{
 public:
  std::string name;
  std::string alias;
};

class configOptions
{
public:
	std::string bpipeHost;
	int bpipePort;
	const static std::string authMethod;
	std::string applicationName;
	std::string rootPath;
};

class subscribedBpipe
{
private:
	configOptions config;
	Session *d_session;
	Identity d_identity;
	std::string authOptions;
	SubscriptionList subscriptions;

	std::vector<std::string> bloombergFields;
	std::vector<stringWithAlias> securities;

	void (*eventHandler)(Event evnt);
	void (*statusEventHandler)(Event evnt);
	
	bool startSession();
	bool authorize();
	std::string getAuthOptions();
public:
	bool init(configOptions config);
	void setFields(	std::vector<std::string> & fields ){ bloombergFields = fields; }
	void setSecurities( std::vector<stringWithAlias> & securities_in ){ securities = securities_in; }
	bool subscribe();
	void setEventHandler(void (*fcn)(Event evnt)){ eventHandler = fcn; }
	void setStatusEventHandler(void (*fcn)(Event evnt)){ statusEventHandler = fcn; };
	void startEventLoop();
};

