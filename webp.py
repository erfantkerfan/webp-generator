# -*- coding: utf-8 -*-

import os
import platform
import random
import subprocess
import threading
import time
from threading import Thread

from termcolor import cprint, colored

# user variables for setting up script
SIMULTANEOUS_THREADS = 20
EMPTY_WEBP_MIN_SIZE = 100
DIR_CDN = '/alaa_media/cdn'


class Logo(object):

    def __init__(self, run):
        self.run = run

    def loop(self):
        self.prepare_logo()
        while self.run:
            time.sleep(0.01)
            try:
                a = self.logo.pop()
            # if logo stack is empty fill it again
            except IndexError:
                spill_statistic_log()
                self.prepare_logo()
                a = self.logo.pop()
            cprint(a, self.color, end='', flush=True)

        for a in self.logo[::-1]:
            cprint(a, self.color, end='', flush=True)
        return None

    def prepare_logo(self):
        simple = """
 █████╗ ██╗      █████╗  █████╗     ████████╗██╗   ██╗
██╔══██╗██║     ██╔══██╗██╔══██╗    ╚══██╔══╝██║   ██║
███████║██║     ███████║███████║       ██║   ██║   ██║
██╔══██║██║     ██╔══██║██╔══██║       ██║   ╚██╗ ██╔╝
██║  ██║███████╗██║  ██║██║  ██║       ██║    ╚████╔╝ 
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝       ╚═╝     ╚═══╝  
"""
        large = """
               AAA               lllllll                                         TTTTTTTTTTTTTTTTTTTTTTTVVVVVVVV           VVVVVVVV
              A:::A              l:::::l                                         T:::::::::::::::::::::TV::::::V           V::::::V
             A:::::A             l:::::l                                         T:::::::::::::::::::::TV::::::V           V::::::V
            A:::::::A            l:::::l                                         T:::::TT:::::::TT:::::TV::::::V           V::::::V
           A:::::::::A            l::::l   aaaaaaaaaaaaa    aaaaaaaaaaaaa        TTTTTT  T:::::T  TTTTTT V:::::V           V:::::V 
          A:::::A:::::A           l::::l   a::::::::::::a   a::::::::::::a               T:::::T          V:::::V         V:::::V  
         A:::::A A:::::A          l::::l   aaaaaaaaa:::::a  aaaaaaaaa:::::a              T:::::T           V:::::V       V:::::V   
        A:::::A   A:::::A         l::::l            a::::a           a::::a              T:::::T            V:::::V     V:::::V    
       A:::::A     A:::::A        l::::l     aaaaaaa:::::a    aaaaaaa:::::a              T:::::T             V:::::V   V:::::V     
      A:::::AAAAAAAAA:::::A       l::::l   aa::::::::::::a  aa::::::::::::a              T:::::T              V:::::V V:::::V      
     A:::::::::::::::::::::A      l::::l  a::::aaaa::::::a a::::aaaa::::::a              T:::::T               V:::::V:::::V       
    A:::::AAAAAAAAAAAAA:::::A     l::::l a::::a    a:::::aa::::a    a:::::a              T:::::T                V:::::::::V        
   A:::::A             A:::::A   l::::::la::::a    a:::::aa::::a    a:::::a            TT:::::::TT               V:::::::V         
  A:::::A               A:::::A  l::::::la:::::aaaa::::::aa:::::aaaa::::::a            T:::::::::T                V:::::V          
 A:::::A                 A:::::A l::::::l a::::::::::aa:::aa::::::::::aa:::a           T:::::::::T                 V:::V           
AAAAAAA                   AAAAAAAllllllll  aaaaaaaaaa  aaaa aaaaaaaaaa  aaaa           TTTTTTTTTTT                  VVV            
"""
        logos = [simple, large]
        logo = list(random.choice(logos))
        # revere logo for printing in console
        logo = logo[::-1]
        colors = ['yellow', 'blue', 'magenta']
        color = random.choice(colors)
        self.logo = logo
        self.color = color


def convert():
    global status1, status2
    threads = []
    # queue jobs in a list and fire them
    for dirpath, dirnames, filenames in os.walk(DIR_CDN):
        for file in filenames:
            count['all'] += 1
            fp = os.path.join(dirpath, file)

            # skip if it is symbolic link or not jpg file
            if os.path.islink(fp) or not fp.lower().endswith(('.jpg', '.jpeg', 'png')):
                continue

            count['jpg jpeg png'] += 1
            if os.path.exists(fp + '.webp') and os.path.getsize(fp + '.webp') > EMPTY_WEBP_MIN_SIZE:
                count['webp'] += 1
                continue

            # throttle the conversion parallel processes
            while threading.activeCount() > SIMULTANEOUS_THREADS:
                pass
            threads = [t for t in threads if t.is_alive()]
            threads.append(Thread(name='t: ' + str(fp), target=webp, args=(fp,)))
            threads[-1].start()

    # stay here until all threads are finished
    while any([t.is_alive for t in threads]):
        threads = [t for t in threads if t.is_alive()]


def webp(path):
    # main convert command execution process
    global count
    command = 'cwebp -quiet -mt -m 6 -q 80 -sharp_yuv -alpha_filter best -pass 10 -segments 4 -af \"' + path + '\" -o \"' + path + '.webp' + '\"'
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.wait() == 0:
            count['success'] += 1
        else:
            count['fail'] += 1
            errors.append(colored(command, 'red'))
    except:
        count['fail'] += 1
        errors.append(colored(command, 'red'))


def ownership():
    global status1, status2
    if PRODUCTION:
        try:
            chown = subprocess.Popen('sudo chown -R sftp:www-data ' + DIR_CDN, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)

            status1 = chown.wait()
        except:
            pass
        try:
            chmod = subprocess.Popen('sudo chmod -R 776 ' + DIR_CDN, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            status2 = chmod.wait()
        except:
            pass


def spill_error_log():
    global status1, status2

    print()
    cprint(' ' * 45 + 'Error Log:', 'red')
    cprint('↓' * 100, 'red')
    for e in errors:
        print(e)
    if PRODUCTION:
        if status1 != 0:
            cprint('chown -R sftp:www-data ' + DIR_CDN + ' ---> failed', 'red')
        if status2 != 0:
            cprint('chmod -R 776 ' + DIR_CDN + ' ---> failed', 'red')
    cprint('↑' * 100, 'red')


def spill_statistic_log():
    global status1, status2, count, start, end
    end = time.time()
    count['time'] = str(time.strftime('%H:%M:%S', time.gmtime(end - start)))
    print()
    cprint(' ' * 45 + 'Summary Log:', 'green')
    cprint('↓' * 100, 'green')
    cprint(str(count), 'green')
    if PRODUCTION:
        if status1 == 0:
            cprint('chown -R sftp:www-data ' + DIR_CDN + ' ---> success', 'green')
        if status2 == 0:
            cprint('chmod -R 776 ' + DIR_CDN + ' ---> success', 'green')
    cprint('↑' * 100, 'green')


if __name__ == '__main__':
    # system variables
    PRODUCTION = platform.system() != 'Windows'
    keys = ('all', 'jpg jpeg png', 'webp', 'fail', 'success', 'time')
    count = dict.fromkeys(keys, 0)
    errors = []
    status1 = None
    status2 = None

    # start timing and showing our logo
    start = time.time()
    logo = Logo(1)
    logo_thread = threading.Thread(name='t: Logo', target=logo.loop)
    logo_thread.start()

    # change ownership and permissions
    ownership()

    # start converting process
    convert()

    # change ownership and permissions of newly created files
    ownership()

    # stop logo and print final logs
    logo.run = 0
    logo_thread.join()
    spill_error_log()
    spill_statistic_log()
