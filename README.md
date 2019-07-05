# smsActions
Turn sms messages into home automation actions.

This project retrieves SMS messages from an account on voip.ms and then
takes action based on the sender and/or content of the message.

## Getting Started

There are three directories:

* IRdefender - Code which defends an area and provides a web page for control.
* IRrecvDemo - Code to determine the protocol of the laser tag.
* IRsendDemo - Code to test out the firing code found in IRrecvDemo.

### Prerequisites

This directory has python 3 code to handle
a callback from voip.ms when a new sms
message is available to be handled.

The server lives at port 8321 and it is intended to be
exposed behind a reverse proxy such as nginx with TLS encryption.

The docker image exposes port 8321 and which can then
be exposed to nginx.

The docker images needs access to various configuration
information (such as hue bridge password and voip account information)
which is done by mapping a directory on the host onto /opt/external in
the docker image. The path to the configuration file (as seen from
inside the docker image) is included
in the docker startup script and can be changed as needed. The format
of the configuration file is a python dictionary.

Shell scripts are provided to build and run the docker container image.

## Deployment

This project uses a Docker container for deployment.

## Contributing

Please send pull requests for updates or changes.

## Authors

* **Charles Spirakis** - *Initial work*

## License

This project is licensed under the LGPL License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* Thanks to quentinsf for the [qhue](https://github.com/quentinsf/qhue) library.
* Thanks to my coworkers for the inspriation for creating this program.

