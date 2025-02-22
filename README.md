# IOT
Programming for IOT project

## Documentation
[docs](https://github.com/dagh3n/IOT/blob/main/Documentation/documentation.md)

## How to run microservices **with** docker (recommended)
First time can take a while to build  
### With make
Build and run
```bash
make build-<all|logs|microservices>
```    
Start  
```bash
make start-<logs|microservices>
```  
Restart  
```bash
make restart-<logs|microservices>
```
Clean --> stop every containers and clean logs  
```bash
make restart-<logs|microservices>
```  
### Directly with docker
Build and run
```bash
docker compose up <service_name|empty for all> --build -d
```  
Stop  
```bash
docker compose down <service_name|empty for all>
```  
## How to run microservices **without** docker
Create and activate python virtual environment:  
```bash
python -m venv <name of the venv folder(.venv | .env | venv | env)>
source <name of venv folder>/bin/activate
```  
Install libraries
```bash
pip install -r python_libraries.txt
```  
Run manually each service or auto matically by script(using linux screen utils)  
Permission
```bash
chmod +x screen_run_all.sh
```  
Run  
```bash
sh screen_run_all.sh
```  

Reattach to a service  
```bash
screen -r <service_name>
```  

Detach from service = Ctrl+a -> d(detach)  

Close **all** python process in background
```bash
pkill -9 python
```

## TO-DO List
- [] score 1-100 how well you care for your plant
- [] web ui dashboard (User frontend)
- [] prototype 
