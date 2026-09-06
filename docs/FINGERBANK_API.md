### Fingerbank 2 / Combinations / interrogate

GET /api/v2/combinations/interrogate
POST /api/v2/combinations/interrogate

## NOTE: 

If you’re migrating from the v1 API, read the following guidelines to adjust your requests
How it works
This method allows you to interrogate Fingerbank with different network patterns (DHCP informations, HTTP+UPnP User-Agents, MAC address, etc) and obtain the device that matches the most those attributes. It will also provide a confidence level (score) on a scale of 100 for the patterns you provided.

Providing more attributes will provide more accurate matching with a higher score. See the following page for a detailed example.

# CVEs (Vulnerabilities)
According to your role, you will get access to CVEs (Common Vulnerabilities and Exposures) related to the device directly in the response payload. The vulnerabilities object is included as a top-level key in the interrogate response.

The vulnerabilities object contains: * cve_devices: CVEs specific to the device hardware/model * cve_os: CVEs specific to the operating system * message: Additional information message

If you need to retrieve only the CVE vulnerabilities for a specific device by its ID, you can use the dedicated /api/v2/devices/:id/vulnerabilities endpoint.

# Scoring
The score is based on a scale of 0 to 100 and represents the confidence level Fingerbank has on the result it is providing (device and version)

# Computation of the score:
The score is computed by passing the attributes through all the patterns known by Fingerbank. Once all the patterns have been extracted, they are put together by which device that pattern matches. Fingerbank then analyses which device has the strongest patterns (for example matching DHCP informations has more weight than an HTTP User-Agent since the latest is easily spoofable).

Once it has found the device with the strongest matching patterns, it weights the score using the following rules:

33% of the score is related to the top scoring pattern that has matched the device itself.
33% of the score is related to the top scoring pattern that has matched the device itself or a device its related to (parent or derivation)
25% of the score is related to the ratio of patterns that have matched the device or a device its related to versus compared to the total amount of patterns that have matched.
9% of the score is related to the amount of patterns that have matched the device
Then this score can be decreased by up to 27% by the top competing pattern that has matched (not related to the device)
Interpretation of the score:
Lower than 30: very little confidence on the result that was returned.
Between 31 and 50: Moderate confidence on the result that was returned. Either the attributes didn’t match patterns on attributes that provide confidence (DHCP informations, TCP fingerprinting, etc) or the attributes matched competing patterns (ex: matched both Windows and Android patterns).
Between 51 and 75: High confidence on the result that was returned. The result will be based on at least an attribute that provide confidence and didn’t or almost didn’t match competing patterns.
Higher than 76: Very high confidence on the result that was returned. The result will be based on multiple attributes that provide confidence and didn’t or almost didn’t match competing patterns.
Supported Formats
Request : application/json, Response : application/json
Errors
Code	Description
401	This request is unauthorized. Either your key is invalid or wasn't specified.
403	This request is forbidden. Your account may have been blocked.
429	The amount of requests per minute has been exceeded. All accounts (even the unlimited ones) are rate limited to 250 requests per minute unless agreed otherwise with Inverse.
502	No API backend was able to process the request. The system may be overloaded, in maintenance or experiencing an issue. Retrying shortly after should work.
404	No device profiling result was found for the signatures that were provided.
Examples
Example body:
  {"dhcp_fingerprint":"1,15,3,6,44,46,47,31,33,121,249,43"}
Example response:
{
    "device": {
        "created_at": "2014-09-09T15:09:51.000Z",
        "id": 33,
        "name": "Microsoft Windows Kernel 6.0",
        "parent_id": 7536,
        "parents": [
            {
                "created_at": "2015-09-18T12:51:27.000Z",
                "id": 7536,
                "name": "Microsoft Windows Kernel 6.x",
                "parent_id": 1,
                "updated_at": "2015-09-22T08:11:35.000Z",
                "virtual_parent_id": null
            },
            {
                "created_at": "2014-09-09T15:09:50.000Z",
                "id": 1,
                "name": "Windows OS",
                "parent_id": 16879,
                "updated_at": "2017-09-20T15:46:53.000Z",
                "virtual_parent_id": null
            },
            {
                "created_at": "2017-09-14T18:41:06.000Z",
                "id": 16879,
                "name": "Operating System",
                "parent_id": null,
                "updated_at": "2017-09-18T16:33:18.000Z",
                "virtual_parent_id": null
            }
        ],
        "updated_at": "2015-09-18T12:53:32.000Z",
        "virtual_parent_id": null
    },
    "device_name": "Operating System/Windows OS/Microsoft Windows Kernel 6.x/Microsoft Windows Kernel 6.0",
    "manufacturer": {
      "can_be_more_precise": false,
      "child_devices_count": 0,
      "child_virtual_devices_count": 0,
      "created_at": "2017-09-04T16:41:59.000Z",
      "id": 0,
      "name": "",
      "parent_id": null,
      "parents": [],
      "updated_at": "2023-05-05T12:17:53.000Z",
      "virtual_parent_id": null
    },
    "operating_system": {
      "can_be_more_precise": true,
      "child_devices_count": 3,
      "child_virtual_devices_count": 3,
      "created_at": "2017-09-18T16:56:41.000Z",
      "id": 0,
      "name": "",
      "parent_id": null,
      "parents": [],
      "updated_at": "2023-05-05T12:18:54.000Z",
      "virtual_parent_id": null
    },
    "score": 75,
    "version": "Vista/Server 2008",
    "vulnerabilities": {
          "cve_devices": {},
          "cve_os": {},
          "message": "Thanks for using Fingerbank."
    },
    "request_id": "abcd1234efgh5678ijkl9012mnop3456"
  }
Example using curl using DHCPv4 fingerprint:
curl -X GET -d '{"dhcp_fingerprint":"1,15,3,6,44,46,47,31,33,121,249,43"}' --header 'Content-type: application/json' 'https://api.fingerbank.org/api/v2/combinations/interrogate?key='
Example using curl without a body payload:
curl 'https://api.fingerbank.org/api/v2/combinations/interrogate?dhcp_fingerprint=1,15,3,6,44,46,47,31,33,121,249,43&key='
Example using curl using DHCPv4 fingerprint, User-Agent and MAC address:
curl -X GET -d '{"dhcp_fingerprint":"1,121,3,6,15,119,252", "user_agents":["Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13G36 Safari/601.1"], "mac": "e0b9ba88158a"}' --header 'Content-type: application/json' 'https://api.fingerbank.org/api/v2/combinations/interrogate?key='
Example using curl with more advanced parameters:
curl  -X GET -d '{"dhcp_fingerprint":"1,15,3,6,44,46,47,31,33,121,249,43", "destination_hosts":["updates.microsoft.com"], "mdns_services":["_printer._tcp.local"]}' --header 'Content-type: application/json' 'https://api.fingerbank.org/api/v2/combinations/interrogate?key='
Params
Param name	Description
key
required	
Your API key (you can optionally use the Authorization header for improved security)

Validations:

Must be a String


Metadata:
Type: query parameter
Example: "?key=68989f507420b6187c7e4fa32245db311efed505"
client_hints
optional	
The HTTP client hints of the endpoint as seen in the various client hints headers (supports only sec-ch-ua, sec-ch-ua-platform, sec-ch-ua-model, sec-ch-ua-arch). The keys of the hash must be the value of the sec-ch-ua header, then the hash value must contain key value pairs of the different headers and their respective value.

Example:
Given the following set of headers in the HTTP request:

sec-ch-ua: My Example UA
sec-ch-ua-platform: ACME Corp
sec-ch-ua-model: Revolutionary Model 123
sec-ch-ua-arch: i386

You should provide the following as the parameter

{"My Example UA":{"sec-ch-ua-platform": "ACME Corp", "sec-ch-ua-model": "Revolutionary Model 123", "sec-ch-ua-arch": "i386"}}

It is also possible to supply data from multiple user agents and not all headers are necessary:

{"My Example UA":{"sec-ch-ua-platform": "ACME Corp", "sec-ch-ua-model": "Revolutionary Model 123", "sec-ch-ua-arch": "i386"}, "Browsinator 3000":{sec-ch-ua-arch: i386}}
Validations:

Must be a Hash


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
dhcp_fingerprint
optional	
The DHCP fingerprint of the endpoint. Must be a comma-delimited list of numbers following this standard: 1,2,3,4,5,6,7. The order of the options must be the same as in the DHCP packet and nothing else than commas and numbers are allowed in this field.

Validations:

Must be a String


Metadata:
Type: payload
Example: '128,229,32,44,52,64,17'
dhcp6_fingerprint
optional	
The DHCPv6 fingerprint of the endpoint. Must be a comma-delimited list of numbers following this standard: 1,2,3,4,5,6,7. The order of the options must be the same as in the DHCP packet and nothing else than commas and numbers are allowed in this field.

Validations:

Must be a String


Metadata:
Type: payload
Example: '24,25,58,24'
dhcp_vendor
optional	
The DHCP vendor of the endpoint as seen in the DHCP packet.

Validations:

Must be a String


Metadata:
Type: payload
Example: MSFT 5.0
dhcp6_enterprise
optional	
The DHCPv6 enterprise of the endpoint. Must be the identifier present in the packet (a number)

Validations:

Must be a String


Metadata:
Type: payload
mac
optional	
The MAC address of the device following any of the following formats: 001122334455, 00-11-22-33-44-55, 00:11:22:33:44:55

Validations:

Must be a String


Metadata:
Type: payload
destination_hosts
optional	
The destination hosts (domains) this endpoint has send data to

Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
hostname
optional	
The hostname of the endpoint.

Validations:

Must be a String


Metadata:
Type: payload
ja3_fingerprints
optional	
The JA3 fingerprints detected for this endpoint. The signatures must be the MD5 of the full JA3 fingerprint.

Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
Example: b32309a26951912be7dba376398abc3b
ja3_data
optional	
The JA3+JA3s fingerprints detected for this endpoint with their matching server host and port. The signatures must be the MD5 of the full fingerprint.

Example:
For a TLS connection performed on https://api.fingerbank.org on port 443, having the JA3 signature b32309a26951912be7dba376398abc3b and the JA3s signature 36856d086af670bd60710ecad0ed2b25
You should provide the following as the ja3_data parameter

{"api.fingerbank.org:443":["b32309a26951912be7dba376398abc3b;36856d086af670bd60710ecad0ed2b25"]}


Note that the JA3 and JA3s are joined together with a semi-colon. Multiple JA3+JA3s can be provided for the same host+port.
Here is a more complex example to illustrate this:

{"api.fingerbank.org:443":["b32309a26951912be7dba376398abc3b;36856d086af670bd60710ecad0ed2b25"], "www.inverse.ca:443":["97b33baaeeec3cdf3eb4d053a8bb3440;fe1d51cf85a3d7c9d8ef94275fa442b1", "a55a17a2e48c91c5d1ee64e67f565c99;fe1d51cf85a3d7c9d8ef94275fa442b1"]}
Validations:

Must be a Hash


Metadata:
Type: payload
Limit: The amount of elements must be limited to 10 keys (host+port) and each key
  in the hash must contain an array that doesn't have more than 3 JA3+JA3s couples
mdns_services
optional	
The MDNS services that this endpoint has advertised

Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
upnp_user_agents
optional	
The UPnP User Agents (USER-AGENT header) that this endpoint has advertised

Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
upnp_server_strings
optional	
The UPnP Server strings (SERVER header) that this endpoint has advertised

Validations:

Must be an array of String


Metadata:
Type: payload
tcp_syn_signatures
optional	
The TCP SYN signatures detected for this endpoint. The signatures must follow the p0f standard.

# Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
Example: 4:128+0:0:1460:8192,2:mss,nop,ws,nop,nop,sok:df,id+:0
tcp_syn_ack_signatures
optional	
The TCP SYN-ACK signatures detected for this endpoint. The signatures must follow the p0f standard.

Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
Example: 4:128+0:0:1460:8192,2:mss,nop,ws,nop,nop,sok:df,id+:0
user_agents
optional	
The HTTP User Agents of the endpoint as seen in the User-Agent header of the HTTP requests the endpoint does.

Validations:

Must be an array of String


Metadata:
Type: payload
Limit: The amount of elements must be limited to 5 elements. If not, only the 5 first
  will be taken into account in the discovery process.
Returns
Code: 200
Description:
Device profiling result

Param name	Description
device
required	
The device object that was profiled using the input parameters

Validations:

Must be a Hash

device[can_be_more_precise]
required	
Whether or not the result can be more precise than the one that is returned. This can be used as an indicator that the profiling result cannot be improved.

Validations:

Must be one of: true, false.

device[child_devices_count]
required	
The amount of direct childs the device has

Validations:

Must be a Integer

device[child_virtual_devices_count]
required	
The amount of virtual childs the device has

Validations:

Must be a Integer

device[created_at]
required	
The date that the device was created in Fingerbank

Validations:

Must be a Date

device[id]
required	
The numeric identifier of the device in Fingerbank

Validations:

Must be a Integer

device[name]
required	
The name of the device

Validations:

Must be a String

device[parent_id]
required	
The numeric identifier of the parent of this device

Validations:

Must be a Integer

device[parents]
required	
A list of simple representations of the parents of this device

Validations:

Must be an Array of nested elements

device[parents][created_at]
required	
The date that the device was created in Fingerbank

Validations:

Must be a Date

device[parents][id]
required	
The numeric identifier of the device in Fingerbank

Validations:

Must be a Integer

device[parents][name]
required	
The name of the device

Validations:

Must be a String

device[parents][parent_id]
required	
The numeric identifier of the parent of this device

Validations:

Must be a Integer

device[parents][updated_at]
required	
The date that the device was last updated in Fingerbank

Validations:

Must be a Date

device[parents][virtual_parent_id]
required	
The numeric identifier of the virtual parent of this device (if any, defaults to null if there is none). Virtual parents are non-mandatory and will usually link a physical device (ex: Generic Android) with its operating system (Android OS)

Validations:

Must be a Date

device_name
required	
The unique device name with all its hierarchy separated by the ‘/’ character

Validations:

Must be a String

manufacturer
required	
Optional object that follows the exact same structure as the ‘device’ attribute of the response. When present, it will contain the manufacturer of the device that was profiled. For example, in the case of a Samsung Galaxy S8, this will contain the hardware manufacturer Samsung. This will only be true if enough information is provided to tie the Samsung Galaxy S8 result to Samsung and will not be present for that device if for example only the HTTP User-Agent is provided which doesn’t allow to tie the device to the manufacturer. In our current example tying the device to the manufacturer is done through the MAC address of the device.

Validations:

Must be a Hash

manufacturer[can_be_more_precise]
required	
Whether or not the result can be more precise than the one that is returned. This can be used as an indicator that the profiling result cannot be improved.

Validations:

Must be one of: true, false.

manufacturer[child_devices_count]
required	
The amount of direct childs the device has

Validations:

Must be a Integer

manufacturer[child_virtual_devices_count]
required	
The amount of virtual childs the device has

Validations:

Must be a Integer

manufacturer[created_at]
required	
The date that the device was created in Fingerbank

Validations:

Must be a Date

manufacturer[id]
required	
The numeric identifier of the device in Fingerbank

Validations:

Must be a Integer

manufacturer[name]
required	
The name of the device

Validations:

Must be a String

manufacturer[parent_id]
required	
The numeric identifier of the parent of this device

Validations:

Must be a Integer

manufacturer[parents]
required	
A list of simple representations of the parents of this device

Validations:

Must be an Array of nested elements

manufacturer[parents][created_at]
required	
The date that the device was created in Fingerbank

Validations:

Must be a Date

manufacturer[parents][id]
required	
The numeric identifier of the device in Fingerbank

Validations:

Must be a Integer

manufacturer[parents][name]
required	
The name of the device

Validations:

Must be a String

manufacturer[parents][parent_id]
required	
The numeric identifier of the parent of this device

Validations:

Must be a Integer

manufacturer[parents][updated_at]
required	
The date that the device was last updated in Fingerbank

Validations:

Must be a Date

manufacturer[parents][virtual_parent_id]
required	
The numeric identifier of the virtual parent of this device (if any, defaults to null if there is none). Virtual parents are non-mandatory and will usually link a physical device (ex: Generic Android) with its operating system (Android OS)

Validations:

Must be a Date

operating_system
required	
Optional object that follows the exact same structure as the ‘device’ attribute of the response. When present, it will contain the most probable operating system for the device based on the result contained in the ‘device’ field of the response. For example, in the case of a Samsung Galaxy S8, this will contain the operating system Android OS. This will only be true if enough information is provided to tie the Samsung Galaxy S8 result to Android OS and will not be present for that device if for example only the hostname is provided which doesn’t allow to tie the device to the Android OS operating system. In our current example tying the device to the OS is done through the DHCP fields, HTTP User-Agent, etc.

Validations:

Must be a Hash

operating_system[can_be_more_precise]
required	
Whether or not the result can be more precise than the one that is returned. This can be used as an indicator that the profiling result cannot be improved.

Validations:

Must be one of: true, false.

operating_system[child_devices_count]
required	
The amount of direct childs the device has

Validations:

Must be a Integer

operating_system[child_virtual_devices_count]
required	
The amount of virtual childs the device has

Validations:

Must be a Integer

operating_system[created_at]
required	
The date that the device was created in Fingerbank

Validations:

Must be a Date

operating_system[id]
required	
The numeric identifier of the device in Fingerbank

Validations:

Must be a Integer

operating_system[name]
required	
The name of the device

Validations:

Must be a String

operating_system[parent_id]
required	
The numeric identifier of the parent of this device

Validations:

Must be a Integer

operating_system[parents]
required	
A list of simple representations of the parents of this device

Validations:

Must be an Array of nested elements

operating_system[parents][created_at]
required	
The date that the device was created in Fingerbank

Validations:

Must be a Date

operating_system[parents][id]
required	
The numeric identifier of the device in Fingerbank

Validations:

Must be a Integer

operating_system[parents][name]
required	
The name of the device

Validations:

Must be a String

operating_system[parents][parent_id]
required	
The numeric identifier of the parent of this device

Validations:

Must be a Integer

operating_system[parents][updated_at]
required	
The date that the device was last updated in Fingerbank

Validations:

Must be a Date

operating_system[parents][virtual_parent_id]
required	
The numeric identifier of the virtual parent of this device (if any, defaults to null if there is none). Virtual parents are non-mandatory and will usually link a physical device (ex: Generic Android) with its operating system (Android OS)

Validations:

Must be a Date

request_id
required	
The unique identifier of the request

Validations:

Must be a String

score
required	
The confidence level in the result that is provided. See the ‘Scoring’ section of this page for more details.

Validations:

Must be a Integer

version
required	
The version of the device. When it cannot be found, an empty string is provided. Example: A Samsung Galaxy S8 running Android version 9.0.0 will have the value ‘9.0.0’ in the version field if the input data allowed Fingerbank to detect the version properly.

Validations:

Must be a String

vulnerabilities
required	
CVE vulnerabilities information for the device (available based on your access role)

Validations:

Must be a Hash

vulnerabilities[cve_devices]
required	
Common Vulnerabilities and Exposures (CVEs) specific to the device hardware/model

Validations:

Must be a Hash

vulnerabilities[cve_os]
required	
Common Vulnerabilities and Exposures (CVEs) specific to the operating system

Validations:

Must be a Hash

vulnerabilities[message]
required	
Additional information message

Validations:

Must be a String

Code: 404
Description:
Unknown device profiling result

Param name	Description
errors
required	
The errors that have occured

Validations:

Must be a Hash

errors[details]
required	
An explanation on why the device profiling yielded an unknown result

Validations:

Must be a String

request_id
required	
The unique identifier of the request

Validations:

Must be a String

Headers
Header name	Description
Authorization
optional	Authorization header containing your API key (Bearer standard). Example value for the header: `Bearer 68989f507420b6187c7e4fa32245db311efed505`
