# OpenImageIo-Docker

Steps to create a local docker registry in the server and install OpenImageIO-Docker. 

### Install Docker and create OpenImageIO in local machine
#### Install Docker
```
curl -sSL https://get.docker.com | sh
```
#### Pull the centos7 docker from docker hub
```
docker pull centos:7
```
#### Create a container by running the docker images
```
docker run -dit --name 3de_oiio -v /Shares/T:/Shares/T centos /bin/bash        (/Shares/T is a server path . we mount that as a volume)
```
#### Enter into the docker container by starting interactively
```
docker start -ai 3de_oiio
```
#### Build OpenImageIO as instructed into the ASWF documentation

### Create a local registry in a absolute server path 
#### Create name server
```vim /etc/resolv.conf```
add 



