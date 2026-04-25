# NMS_Tools Suite Layout
The NMS_Tools suite is a collection of self‑contained Nagios/Icinga‑compatible Python plugins.
All required Python dependencies are bundled inside the suite, so no pip installation or virtual environment is required.

The suite installs into:

`/usr/local/nagios/NMS_Tools/`

and tools are executed directly by Nagios or NRPE.

## Directory Structure

NMS_Tools/
│
├── VERSION                 # Suite version
│
├── libs/                   # Bundled Python dependencies (vendored)
│                           # Tools automatically load these at runtime
│
├── check_weather/          # Weather monitoring plugin
│   └── check_weather.py
│
├── check_cert/             # Certificate expiration monitoring plugin
│   └── check_cert.py
│
├── check_html/             # HTTP/HTML endpoint monitoring plugin
│   └── check_html.py
│
└── man/                    # Man pages for each tool (optional)

## Installation

To install the suite:
`sudo make install-suite`
This copies the entire directory to:

`/usr/local/nagios/NMS_Tools/`

and sets correct permissions.

## Runtime Requirements

* Python 3.8+
* No pip
* No virtual environment
* No external dependencies

All tools automatically load their vendored libraries from `libs/`.

## Using the Tools
Each tool can be executed directly:

`/usr/local/nagios/NMS_Tools/check_cert/check_cert.py --help`

Nagios command definitions typically look like:

`command[check_cert]=/usr/local/nagios/NMS_Tools/check_cert/check_cert.py -H www.example.com`

## Man Pages (Optional)
If installed, man pages are available under:

`man1/   (individual tools)`
`man7/   (suite overview)`

## Support Model

* Tools are designed to run only inside the suite directory
* Individual scripts copied out of the suite are unsupported
* All dependencies are bundled in `libs/`
