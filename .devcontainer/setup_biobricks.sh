#!/bin/bash

# Check if the BioBricks is already configured
if biobricks version &> /dev/null; then
  echo "BioBricks is already configured."
  exit 0
fi

# Prompt the user for their BioBricks token
read -p "Please enter your BioBricks token: " BIOBRICKS_TOKEN

# Set a default token if none is provided
if [ -z "$BIOBRICKS_TOKEN" ]; then
  BIOBRICKS_TOKEN="VQF6Q2U-NKktZ31ioVYa9w"
  echo "No token provided. Using default public token."
fi

# Configure BioBricks with the provided token
source /etc/bash.bashrc
biobricks configure --bblib=/mnt/biobricks --token=$BIOBRICKS_TOKEN --interactive=False

echo "BioBricks has been configured."
