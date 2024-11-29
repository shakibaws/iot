# IOT
Programming for IOT project

## Documentation
[docs](https://github.com/dagh3n/IOT/blob/main/Documentation/documentation.md)

## How to run microservices **with** docker (recommended)
First time can take a while  
Run  
```bash
docker compose up <service_name|empty for all> --build -d
```  
Or using script(same command as above)  
```bash
./launch
```  
Stop services  
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
- [!] fake sensor data for demo
- [!] data analysis count times plant got wet in the last month
- [!] data analysis compute how much water used in the last month
- [!] temperature average in the last month
- [!] score 1-100 how well you care for your plant
- [] web ui dashboard(per user)
- [] 3d model  
- [] slide presentation  
- [] video to show  
- [] prototype  
- [] restyle esp32 web page
