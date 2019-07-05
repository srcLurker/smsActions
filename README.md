# smsActions
Turn sms messages into home automation actions.

This project retrieves SMS messages from an account on voip.ms and then
takes action based on the sender and/or content of the message.

## Getting Started

Create the Docker image by running the build_docker_sms.py script.

Next create a new configuration file in the config directory. One
can use the example.txt file as a template.

Finally, run the container image. There are two helper scripts
for this which may need to be modified depending on the location
of the cloned repository.

* run_docker_sms.sh - starts a docker image which
will restart itself even after reboot
* run_docker_test.sh - starts up the docker container but starts
up a bash shell instead of the python program. This can be used
for debugging and testing.

### Prerequisites

This repository uses Docker.

This repository creates a server. If the server is going
to be exposed to the internet, it is important to understand
the risks and take precautions. This generally includes
a reverse proxy in front of the server (such as nginx)
and encrypting communications between clients and servers
via TLS (such as letsencrypt). Finally, tools like
fail2ban are useful to limit unexpected access attempts
upon the server.

The server lives (by default) at port 8321. The choice
of port for the server is defined in main.py

The docker image exposes port 8321 (via Dockerfile_sms)
which can then be exposed to your reverse proxy.

The docker image needs access to various configuration
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

