"""Owned Chrome/local-server session for benchmark, GUI verification and demo capture."""
import base64
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


class BrowserSession:
    def __init__(self,headless=True,unlimited=False,data_dir=None):
        import websocket
        self.ws=None;self.server=None;self.browser=None;self.counter=0;self.errors=[]
        self.port=free_port();debug=free_port()
        candidates=[os.environ.get('CHROME_BIN',''),shutil.which('google-chrome'),shutil.which('chromium'),r'C:\Program Files\Google\Chrome\Application\chrome.exe',r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
        chrome=next((c for c in candidates if c and Path(c).is_file()),None)
        if not chrome:raise RuntimeError('Install Chrome or set CHROME_BIN')
        profile=ROOT/'artifacts'/('chrome-'+str(uuid4()));profile.mkdir(parents=True)
        self.data_dir=Path(data_dir) if data_dir else profile/'data'
        flags=dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name=='nt' else {}
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            self.server=subprocess.Popen([sys.executable,str(ROOT/'tools/serve.py'),'--port',str(self.port),'--data-dir',str(self.data_dir)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**flags)
            arguments=[chrome,'--no-first-run','--no-default-browser-check','--no-proxy-server','--enable-gpu-rasterization','--disable-background-timer-throttling','--disable-renderer-backgrounding','--remote-debugging-port='+str(debug),'--remote-allow-origins=*','--window-size=1280,759','--user-data-dir='+str(profile)]
            if headless:arguments.append('--headless=new')
            if unlimited:arguments+=['--disable-frame-rate-limit','--disable-gpu-vsync']
            arguments.append('about:blank')
            self.browser=subprocess.Popen(arguments,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**flags)
            for _ in range(200):
                try:
                    tabs=json.load(self.opener.open(f'http://127.0.0.1:{debug}/json',timeout=1))
                    tab=next(t for t in tabs if t['type']=='page')
                    self.opener.open(f'http://127.0.0.1:{self.port}/',timeout=1).close()
                    break
                except Exception:time.sleep(.05)
            else:raise RuntimeError('Chrome/server startup timed out')
            self.ws=websocket.create_connection(tab['webSocketDebuggerUrl'],timeout=20,suppress_origin=True,http_proxy_host=None)
            self.call('Runtime.enable');self.call('Page.enable')
            self.call('Emulation.setDeviceMetricsOverride',dict(width=1280,height=720,deviceScaleFactor=1,mobile=False))
        except Exception:
            self.close();raise

    def call(self,method,params=None):
        self.counter+=1;self.ws.send(json.dumps(dict(id=self.counter,method=method,params=params or {})))
        while True:
            response=json.loads(self.ws.recv())
            if response.get('method')=='Runtime.exceptionThrown':self.errors.append(response['params']['exceptionDetails'])
            if response.get('id')==self.counter:
                if 'error' in response:raise RuntimeError(response['error'])
                return response.get('result',{})

    def evaluate(self,expression):
        result=self.call('Runtime.evaluate',dict(expression=expression,returnByValue=True,awaitPromise=True))
        if 'exceptionDetails' in result:raise RuntimeError(result['exceptionDetails'])
        return result['result'].get('value')

    def navigate(self,path='/'):
        url=f'http://127.0.0.1:{self.port}'+path
        self.call('Page.navigate',{'url':url})
        self.wait('location.href==='+json.dumps(url)+" && document.readyState==='complete'")

    def wait(self,expression,timeout=30):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:
                if self.evaluate(expression):return
            except RuntimeError as exc:
                if not any(s in str(exc) for s in ['Execution context was destroyed','Cannot find context']):raise
            time.sleep(.05)
        raise TimeoutError(expression)

    def screenshot(self,path):
        result=self.call('Page.captureScreenshot',{'format':'png'})
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        Path(path).write_bytes(base64.b64decode(result['data']))

    def key(self,code,key=None,down=True):
        self.call('Input.dispatchKeyEvent',{'type':'keyDown' if down else 'keyUp','code':code,'key':key or code})

    def close(self):
        if self.ws:
            try:self.ws.close()
            except Exception:pass
        for process in [self.browser,self.server]:
            if process and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
