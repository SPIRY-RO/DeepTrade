#!/usr/bin/env python
#coding: utf-8

#python模拟linux的守护进程

import sys, os, time, atexit
import traceback
from signal import SIGTERM
import subprocess

class Daemon:
    def __init__(self,python_file, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        #需要获取调试信息，改为stdin='/dev/stdin', stdout='/dev/stdout', stderr='/dev/stderr'，以root身份运行。
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.python_file=python_file

    # 检测port对应节点是否存活
    def isRunning(self):
        try:
            process = len(os.popen('ps aux | grep '+self.python_file+' | grep -v grep').readlines())
            print("process",process)
            print(subprocess.getstatusoutput("ls"))
            recovery = "nohup python3 /mnt/python_files/BA/market_strategy/strategy/"+self.python_file+".py &"
            if process==0:  #判断i
                print("进程不存在，重启节点")
                result=subprocess.getstatusoutput(recovery)
                recovery_flag=os.system(recovery) #进程不存在，重启节点
                print("recovery_flag",recovery_flag,"subprocess",result)
            else :
                print("进程存在，进行监控")
        except:
            print("Check process ERROR!!!")



    def _daemonize(self):
        try:
            pid = os.fork()    #第一次fork，生成子进程，脱离父进程
            if pid > 0:
                sys.exit(0)      #退出主进程
        except OSError as e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        os.chdir("/")      #修改工作目录
        os.setsid()        #设置新的会话连接
        os.umask(0)        #重新设置文件创建权限

        try:
            pid = os.fork() #第二次fork，禁止进程打开终端
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

            #重定向文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        #启动监控
        self._daemonize()
        self._run()

    def _run(self):
        """ run your fun"""
        while True:
            self.isRunning()
            time.sleep(10)

if __name__ == '__main__':
    python_file='divergence_strategy'
    front_path=sys.path[0]
    dir=front_path+"/tmp_"+python_file
    if not( os.path.exists(dir)):
        os.mkdir(dir)

    pid=dir+'/process.pid'
    daemon = Daemon(python_file,pid, stdout =dir+'/watch_stdout.log')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            print('start')
            recovery = "nohup python "+python_file+".py &"
            result=subprocess.getstatusoutput(recovery)
            daemon.start()
        else:
            print('unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        daemon.start()
        print ('usage: %s start|stop|restart' % sys.argv[0])
        sys.exit(2)