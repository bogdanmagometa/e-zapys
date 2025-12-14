scp -i ~/.ssh/ec2_instance.pem -o IdentitiesOnly=yes -r ../e-zapys/ ubuntu@51.20.96.182:/home/ubuntu

# EC2

sudo apt update -y

sudo apt install python3 python3-venv -y

cd e-zapys

python3 -m venv venv

source venv/bin/activate

pip install pip --upgrade
pip install -r requirements.txt

sudo apt install -y xvfb

playwright install-deps

playwright install

xvfb-run -a  python3 main.py
