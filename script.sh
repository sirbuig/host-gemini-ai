#!/bin/bash

echo "Set up Application Default Credentials..."

echo "Install the requirements..."
sudo apt-get update;
sudo apt-get install apt-transport-https ca-certificates gnupg curl;

echo "Installation..."
echo "Import the Google Cloud public key..."
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg;

echo "Add the gcloud CLI distribution URI as a package source..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list;

echo "Update and install the gcloud CLI..."
sudo apt-get update && sudo apt-get install google-cloud-cli;

echo "Run gcloud init to get started..."
gcloud init;

echo "Done."