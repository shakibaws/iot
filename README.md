# IOT
Programming for IOT project

## Documentation
[docs](https://github.com/dagh3n/IOT/blob/main/Documentation/documentation.md)

## How to run microservices
Create and activate python virtual environment:  
```bash
python -m venv <name of the venv folder(.venv | .env | venv | env)>
source <name of venv folder>/bin/activate
```  
Install libraries
```bash
pip install -r python_libraries.txt
```  
Run manually or auto matically by script  
Permission
```bash
chmod +x run_all.sh
```  
Run  
```bash
sh screen_run_all.sh
```  
Close **all** python process in background
```bash
pkill -9 python
```

## TO-DO List
- [!] data analysis count times plant got wet in the last month
- [!] data analysis compute how much water used in the last month
- [!] temperature average in the last month
- [!] score 1-100 how well you care for your plant
- [] web ui dashboard
- [] ngix router and kuberneetes
- [] restyle esp32 web page
