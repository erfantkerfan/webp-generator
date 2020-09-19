#Installation

#### install cwebp
```
sudo apt update
sudo apt install webp
```

#### put this in crontab as root user - runs at midnight
```
SHELL=/bin/bash
0 0 * * * python3 -u /home/alaa/webp/webp.py >> /home/alaa/webp/log.txt 2>&1
```