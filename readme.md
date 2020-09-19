### put this in crontab as root user
```
SHELL=/bin/bash
0 0 * * * python3 -u /home/alaa/webp/webp.py >> /home/alaa/webp/log.txt 2>&1
```