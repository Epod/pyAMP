# pyAMP 
A python based toolkit which allows for additional control of Cisco's AMP for endpoints not available within the GUI. 

## Why?
While AMP does allow for exporting of certain data via the web console, there are certain occurrences where exports are limited to a certain number of records, or certain data which cannot be exported through the web interface all together (such as Low Prevalence Executables). Data which is not accessible through the web console can provide vital information as it relates to a possible security event or incident which can only be obtained via the API. This allows responders/analysts to easily extract this data in a readable format. 

Additionally, in certain instances, the AMP Web Interface can sometimes be unresponsive or very time consuming when applying broad or complex filters (depending on the load at the given time). The API for AMP appears to be immune to this, allowing for exports even during times where the AMP web console is unavailable entirely.  

## Getting Started
### Quick Start
- Generate API Key From [https://console.amp.cisco.com/api_credentials](https://console.amp.cisco.com/api_credentials)
- (Optional) Write API credentials to `config.ini`
- Execute `python setup.py install`
- Launch `python pyamp.py`
### API Key
A read only API key is required. API keys for Cisco AMP can be found at [https://console.amp.cisco.com/api_credentials](https://console.amp.cisco.com/api_credentials). This URL might be different depending on your region (ie. APJC & EU). 

You may write these keys to the `config.ini` file if you do not wish to enter in the credentials every time the script is launched
### First Run/Dependencies

pyAMP leverages some dependencies in order to run. To ensure all dependencies are present, first launch the **setup.py** file included in the repository. 

For example:
`python setup.py install`

### Running pyAMP
The current implementation of pyAMP is interactive through a series of menus. Command line arguments at the moment are not accepted, as certain parameters can only be gathered through the API or other means (such as filters based on event IDs). Navigating through the menus are self explanatory.