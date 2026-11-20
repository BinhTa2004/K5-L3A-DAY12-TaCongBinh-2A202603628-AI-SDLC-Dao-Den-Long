"""Publish only the verified v1.0.0 payload to this repository. Tokens never leave memory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
REPO='BinhTa2004/K5-L3A-DAY12-TaCongBinh-2A202603628-AI-SDLC-Dao-Den-Long'
API='https://api.github.com/repos/'+REPO


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected and urllib.parse.urlsplit(req.full_url).netloc!=urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--publish',action='store_true',help='Without this flag, show the reviewable payload only')
    args=parser.parse_args()
    assets=[ROOT/'artifacts/dao-den-long-v1.0.0.zip',ROOT/'docs/demo/demo.mp4',ROOT/'bench.json',ROOT/'soak.json']
    payload=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in assets]
    if not args.publish:
        print(json.dumps(dict(repository=REPO,tag='v1.0.0',assets=payload),indent=2));return
    gate=json.loads((ROOT/'docs/proof/phase-4/release-gate.json').read_text())
    if not gate['passed']:raise RuntimeError('Release gate is not green')
    for key,path in [('archive_sha256',assets[0]),('video_sha256',assets[1])]:
        if gate[key]!=hashlib.sha256(path.read_bytes()).hexdigest():raise RuntimeError('Artifact changed after validation')
    git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
    head=git('rev-parse','HEAD')
    if git('rev-parse','phase-4^{}')!=head or git('rev-parse','v1.0.0^{}')!=head:raise RuntimeError('Release tags do not match HEAD')
    remote=git('remote','get-url','origin')
    if remote!='https://github.com/'+REPO+'.git':raise RuntimeError('Unexpected release destination')
    env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'}
    credential=subprocess.run(['git','credential','fill'],cwd=ROOT,input='protocol=https\nhost=github.com\npath='+REPO+'.git\n\n',text=True,capture_output=True,env=env,check=True)
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    token=fields.get('password')
    if not token:raise RuntimeError('GitHub authentication unavailable')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),SafeRedirect())
    def request(url,method='GET',body=None,content_type='application/json'):
        if urllib.parse.urlsplit(url).hostname not in ['api.github.com','uploads.github.com']:raise RuntimeError('Unexpected API host')
        data=(json.dumps(body).encode() if isinstance(body,(dict,list)) else body)
        req=urllib.request.Request(url,data=data,method=method,headers={'Authorization':'Bearer '+token,'User-Agent':'LanternIsland-Release','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10','Content-Type':content_type})
        with opener.open(req,timeout=180) as response:return json.load(response)
    repository=request(API)
    if repository['private']:raise RuntimeError('Expected the already-public repository')
    if request(API+'/commits/v1.0.0')['sha']!=head:raise RuntimeError('Push and verify tags before publishing')
    releases=request(API+'/releases?per_page=100')
    release=next((r for r in releases if r['tag_name']=='v1.0.0'),None)
    notes=(ROOT/'docs/release-notes.md').read_text(encoding='utf-8')
    if release is None:
        release=request(API+'/releases','POST',dict(tag_name='v1.0.0',target_commitish=head,name='v1.0.0 — Đảo Đèn Lồng',body=notes,draft=True,prerelease=False))
    receipt=ROOT/'artifacts/release-receipt.json'
    receipt.write_text(json.dumps(dict(release_id=release['id'],url=release['html_url'],draft=release['draft']),indent=2),encoding='utf-8')
    existing=request(API+'/releases/'+str(release['id'])+'/assets')
    for path,info in zip(assets,payload):
        found=next((a for a in existing if a['name']==path.name),None)
        if found:
            if found.get('digest')!='sha256:'+info['sha256']:raise RuntimeError('Existing asset cannot be verified: '+path.name)
            continue
        upload=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(path.name)
        mime='video/mp4' if path.suffix=='.mp4' else 'application/zip' if path.suffix=='.zip' else 'application/json'
        request(upload,'POST',path.read_bytes(),mime)
    release=request(API+'/releases/'+str(release['id']),'PATCH',dict(draft=False,name='v1.0.0 — Đảo Đèn Lồng',body=notes))
    receipt.write_text(json.dumps(dict(release_id=release['id'],url=release['html_url'],draft=release['draft'],assets=[a['name'] for a in release['assets']]),indent=2),encoding='utf-8')
    print(json.dumps(dict(url=release['html_url'],draft=release['draft'],assets=[a['name'] for a in release['assets']]),indent=2))


if __name__=='__main__':main()
