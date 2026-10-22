"""Publish only the explicit, verified source snapshots in the release plan.

Runs in GitHub Actions with the repository's short-lived contents token.
Never reads local recordings, external directories or user credentials.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile,zipfile


def command(*args,check=True):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} failed: '+result.stderr.decode(errors='replace'))
    return result


def api(endpoint,payload=None):
    args=['gh','api',endpoint]
    if payload is not None:args+=['--method','POST','--input','-']
    result=subprocess.run(args,input=None if payload is None else json.dumps(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
    return json.loads(result.stdout)


def source_files(commit):
    rows=command('git','ls-tree','-rz',commit).stdout.split(b'\0')
    for row in rows:
        if not row:continue
        meta,name=row.split(b'\t',1);mode,kind,sha=meta.split()
        name=name.decode()
        if name.startswith(('.github/','scripts/')):continue
        if kind!=b'blob' or mode not in [b'100644',b'100755']:raise RuntimeError('Unsupported source entry: '+name)
        yield name,int(mode,8),command('git','cat-file','blob',sha.decode()).stdout


def package(commit,tag,directory):
    entries=list(source_files(commit));data={name:content for name,_,content in entries}
    manifest=data['MANIFEST.sha256'].decode().splitlines()
    for line in manifest:
        expected,name=line.split('  ',1)
        if name not in data or hashlib.sha256(data[name]).hexdigest()!=expected:raise RuntimeError('Checksum mismatch: '+name)
    archive=directory/f'fringe-counter-{tag}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
        for name,mode,content in entries:
            info=zipfile.ZipInfo(f'fringe-counter-{tag}/{name}',date_time=(2026,10,22,0,0,0))
            info.create_system=3;info.external_attr=mode<<16;info.compress_type=zipfile.ZIP_DEFLATED
            output.writestr(info,content)
    sums=directory/f'fringe-counter-{tag}.sha256'
    sums.write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    return archive,sums


def main():
    repo=os.environ['GH_REPO'];head=os.environ['GITHUB_SHA']
    plan=json.loads(Path('.github/release-plan.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        for release in plan['releases']:
            tag=release['tag'];commit=head if release['commit']=='HEAD' else release['commit']
            if not re.fullmatch(r'v\d+\.\d+\.\d+',tag) or not re.fullmatch(r'[0-9a-f]{40}',commit):raise RuntimeError('Invalid release plan')
            command('git','merge-base','--is-ancestor',commit,head)
            archive,sums=package(commit,tag,Path(temp))
            existing=command('gh','api',f'repos/{repo}/releases/tags/{tag}',check=False)
            if existing.returncode==0:
                record=json.loads(existing.stdout)
                ref=api(f'repos/{repo}/git/ref/tags/{tag}')['object']
                while ref['type']=='tag':ref=api(f'repos/{repo}/git/tags/'+ref['sha'])['object']
                if ref['sha']!=commit:raise RuntimeError('Existing tag points to a different snapshot: '+tag)
                if not record['draft']:
                    if release.get('refresh_notes'):
                        notes=command('git','show',f'{head}:docs/releases/{tag}.md').stdout.decode()
                        payload=dict(body=notes,make_latest='true' if release.get('latest') else 'false')
                        result=subprocess.run(['gh','api',f'repos/{repo}/releases/{record["id"]}','--method','PATCH','--input','-'],input=json.dumps(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                        if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
                        print('Release notes updated; assets retained:',record['html_url'])
                    else:print('Already published; retained:',record['html_url'])
                    continue
            else:
                notes=command('git','show',f'{commit}:docs/releases/{tag}.md').stdout.decode()
                record=api(f'repos/{repo}/releases',dict(tag_name=tag,target_commitish=commit,name=release['name'],body=notes,draft=True,prerelease=False,make_latest='false'))
            command('gh','release','upload',tag,str(archive),str(sums),'--repo',repo,'--clobber')
            payload=dict(draft=False,make_latest='true' if release.get('latest') else 'false')
            result=subprocess.run(['gh','api',f'repos/{repo}/releases/{record["id"]}','--method','PATCH','--input','-'],input=json.dumps(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
            print('Published:',json.loads(result.stdout)['html_url'])


if __name__=='__main__':main()
