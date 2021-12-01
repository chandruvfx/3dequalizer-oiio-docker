# OpenImageIo-Docker :+1: :muscle:

 ___
      An 3dequalizer oiio docker utility tool used to convert dpx and exr to jpg's. Loading dpx and exr image sequences directly into the background image made 3dequalizer heavy. This tool convert published shotgrid exr scans into jpg's and publish it into shotgrid again. Matchmovers load the lightwight images into 3dequalizer
 ___
     
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

```docker run -dit --name 3de_oiio -v /Shares/T:/Shares/T centos /bin/bash ``` (/Shares/T is a server path . we mount that as a volume)

#### Enter into the docker container by starting interactively
```
docker start -ai 3de_oiio
```
#### Build OpenImageIO as instructed into the ASWF documentation
 ___

### Create a local registry in a absolute server path 
#### Create name server
```vim /etc/resolv.conf``` and append line at last  ```nameserver 0.0.0.0```

#### Change docker deamon config
Open
```
/etc/docker/daemon.json
```
include following lines
```
{
        "insecure-registries": [ "0.0.0.0:5000" ]
}
```
#### Run Commands to restart docker and docker service to affect the updates
```
systemctl daemon-reload
service docker restart
systemctl enable docker.service
systemctl enable containerd.service
```

#### Install Local registry in the server
create the folder /Shares/T/tools/docker/images
```
docker run -d -e REGISTRY_STORAGE_DELETE_ENABLED=true -e REGISTRY_HTTP_ADDR=0.0.0.0:5000 -p 5000:5000 --restart=always --name registry -v /Shares/T/tools/docker/images:/var/lib/registry registry:2
```
Now docker registry created with the volume mount /Shares/T/tools/docker/images

#### Check the images and containers
```docker images ``` ```docker ps -a``` 

#### Create a OpenimageIo image by using the 3de_oiio container
```docker commit <container_id> localhost:5000/oiio/python3.6.12:v1``` 

#### Once oiio docker image created from the container push it to the local registry 
```docker push localhost:5000/oiio/python3.6.12:v1```

#### Apart from the local registry image delete all images. Then pull the newly created image.
```
docker pull localhost:5000/oiio/python3.6.12:v1
docker run -dit --name 3de_oiio -v /Shares/T:/Shares/T localhost:5000/oiio/python3.6.12:v1 /bin/bash
docker start 3de_oiio
```
This time oiio image docker pulled from the local registry not from the docker hub. You can now access the shared mount to convert images..:grin::grin:
