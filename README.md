mig-website
===========

This repository contains all of the publicly accessible source code for the website for Michigan Gamma chapter of Tau Beta Pi. To see how this all comes together, visit [the website](https://tbp.engin.umich.edu), (note that most of the content is behind user authentication controls available only to members).

Developer Guide
---------
To develop TBP MIG website in your local environment, follow the instructions below.

### Preparation
* Clone this repository.
* Install [Docker](https://docs.docker.com/get-docker/).
* Install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
  * This is so that you can pull Docker images from our private registry.
  * Ask [#committee-website](https://app.slack.com/client/TFBHPDE1F/C02BDLKRH6C) to add you to our AWS organization.
* [Configure](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html) the AWS CLI.
  * You will have to create an Access Key/Secret Key pair through the AWS IAM console
  * Configure command:
    ```console
    $ aws configure --profile [username]
    ```

### Start Developing
1. Make sure your Docker daemon is up and running.
2. Under the project directory, run the following command:
```console
$ ./develop.sh
```
3. Ta-da, the website is up! You can access it at `http://localhost:8000`. The website backend will reload as you make changes to the code.
  - If you want to run command in the webserver’s Docker container, run `./develop.sh [COMMAND]`. For example, to make migrations, you can run:
  ```console
  $ ./develop.sh python manage.py makemigrations
  ```

License
---------
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License. A copy of the license is included in the repository.
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

This license must be included in any derivative work along with notifications of any change from the original source provided here.

Trademarks and logos
--------------------
The following list is presented as summary information and is not intended to be exhaustive. Any omission is not intended to convey the absence of applicable usage restrictions.

Tau Beta Pi logos and insignias may be used by TBP chapters and must follow the guidelines set forth by the [national organization](http://www.tbp.org/off/graphics.cfm).

The Block M of the University of Michigan is subject to the [usage policies](http://vpcomm.umich.edu/brand/usage-policies) set forth by the University. Of particular note, voluntary student organizations are not permitted to use the Block M.


