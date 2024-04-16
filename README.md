# How to host Gemini AI on a local environment

[![Python >= 3.8](https://img.shields.io/badge/Python->=3.8-blue.svg)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/OS-Linux-blue.svg)](https://www.kernel.org/)
![Debian 9+](https://img.shields.io/badge/Debian-9%2B-red)
![Ubuntu 18.04+](https://img.shields.io/badge/Ubuntu-18.04%2B-orange)
![Gemini](https://img.shields.io/badge/Gemini-1.5%20Pro-8E75B2)

<br>

This is a super fast tutorial on how to host Gemini AI on a local environment. This guide is mostly for users from EU who don't have (yet) access to the Gemini API.

Although the tutorials from Google are far more comprehensive, for a newbie they can be quite overwhelming so this contains only the bare minimum to experiment with the Gemini models.

Even if the links provided will perhaps be useful, for more elaborate projects I advise you to follow another guide.

<br>

> [!WARNING]
> These steps were tested on Ubuntu 22.04 LTS and Linux Mint 21.3 "Virginia".
> If you have a different OS (not Debian-based) or a different version you can still follow the tutorial, however you will have to check the links/ search for alternatives. The steps remain the same.

<br>

## I - Vertex AI

Using [Google Cloud Computing Service](https://cloud.google.com/?hl=en) connect to the _Free Trial_, then **Try Gemini 1.5 Pro**. You will be redirected to **Vertex AI**.
<br>
Create a new project (remember the name) and experiment with the models and settings.

<br>

## II - [Virtualenv](https://cloud.google.com/python/docs/reference/aiplatform/latest/index.html)

Clone this repo and open the terminal.

```shell
pip install virtualenv
virtualenv <your-env>
source <your-env>/bin/activate
python3 -m pip install -r requirements.txt
```

> [!NOTE]
> If you encounter `Command 'virtualenv' not found`, use `sudo apt install python3-virtualenv` instead.

<br>

## III - [Set up Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc#local-dev)

Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install#deb).

For a faster setup use the script.

> [!NOTE]
> If you do not have the same OS or you have a different version of it, please follow the guide from the link provided adjusted to your case!

```shell
chmod +x script.sh
./script.sh
```

You will be redirected to a login screen, then asked to choose the project (see Step I). Follow the steps accordingly.

If succesful, you will be redirected to this [page](https://cloud.google.com/sdk/auth_success).

Now create your credential file using
`gcloud auth application-default login`.

If succesful, you should see the same [page](https://cloud.google.com/sdk/auth_success) again.

<br>

## IV - [Google Cloud console](https://cloud.google.com/storage/docs/discover-object-storage-console)

For enabling PDF prompts and analysis, the object must be uploaded in a Bucket. Follow the steps accordingly.

<br>

## V - Have fun!

Modify `main.py` to your liking and enjoy the newest Gemini model!

Don't forget `python3 main.py` to run it.

<br>

> [!TIP]
> If you have any suggestions or you want to add explanations/ commands or you faced some errors I did not, you are free to contribute!
>
> This is a quick guide I made in the middle of the night after some hours spent figuring out how I can use Gemini locally.
