"""Locked, journaled pack replacement; only the user's pack store is modified."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil


class PackTransactionError(ValueError):pass


def tree_digest(root):
    digest=hashlib.sha256()
    if not root.is_dir():return None
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise PackTransactionError('PACK_RECOVERY_CONFLICT: symlink in pack store')
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode());digest.update(b'\0');digest.update(path.read_bytes())
    return digest.hexdigest()


@contextmanager
def install_lock(root):
    root.parent.mkdir(parents=True,exist_ok=True)
    path=root.parent/('.'+root.name+'-pack.lock')
    with path.open('a+b') as stream:
        if os.name=='nt':
            import msvcrt
            stream.seek(0);stream.write(b'0');stream.flush();stream.seek(0)
            try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            except OSError as error:raise PackTransactionError('PACK_INSTALL_BUSY') from error
            try:yield
            finally:stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise PackTransactionError('PACK_INSTALL_BUSY') from error
            try:yield
            finally:fcntl.flock(stream,fcntl.LOCK_UN)


def _write(root, data):
    temp=root/'.pack-transaction.tmp'
    with temp.open('w',encoding='utf-8') as stream:
        json.dump(data,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
    os.replace(temp,root/'.pack-transaction.json')


def _member(root, relative):
    from architect_framework.distribution_policy import safe_relative
    if not safe_relative(relative):raise PackTransactionError('PACK_RECOVERY_CONFLICT: invalid journal path')
    path=root/relative
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p!=root and root in p.parents):
        raise PackTransactionError('PACK_RECOVERY_CONFLICT: linked journal path')
    if root.resolve() not in path.resolve().parents:raise PackTransactionError('PACK_RECOVERY_CONFLICT: escaping journal')
    return path


def recover(root):
    journal=root/'.pack-transaction.json'
    if not journal.exists():return
    data=json.loads(journal.read_text(encoding='utf-8'))
    if data.get('format')!='aaf-pack-transaction/v1' or data.get('state') not in {'prepared','committed'}:
        raise PackTransactionError('PACK_RECOVERY_CONFLICT: unsupported journal')
    if data['state']!='committed':
        for row in reversed(data['rows']):
            dest,stage,old=(_member(root,row[k]) for k in ('dest','stage','old'))
            if old.exists():
                if dest.exists() and tree_digest(dest)!=row['new_digest']:
                    raise PackTransactionError('PACK_RECOVERY_CONFLICT: preserve modified destination '+row['dest'])
                if dest.exists():shutil.rmtree(dest)
                dest.parent.mkdir(parents=True,exist_ok=True);os.replace(old,dest)
            elif not row['had_old'] and not stage.exists() and dest.exists():
                if tree_digest(dest)!=row['new_digest']:
                    raise PackTransactionError('PACK_RECOVERY_CONFLICT: preserve modified destination '+row['dest'])
                shutil.rmtree(dest)
    for row in data['rows']:
        for key in ('stage','old'):
            path=_member(root,row[key])
            if path.exists():shutil.rmtree(path)
    journal.unlink()


def commit(root, rows):
    """rows contain stage/dest Paths; journal survives process termination."""
    records=[]
    for stage,dest in rows:
        old=stage.with_name(stage.name+'-old')
        records.append({'stage':stage.relative_to(root).as_posix(),'dest':dest.relative_to(root).as_posix(),
            'old':old.relative_to(root).as_posix(),'had_old':dest.exists(),'new_digest':tree_digest(stage)})
    data={'format':'aaf-pack-transaction/v1','state':'prepared','rows':records}
    _write(root,data)
    try:
        for row in records:
            stage,dest,old=(_member(root,row[k]) for k in ('stage','dest','old'))
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():os.replace(dest,old)
            os.replace(stage,dest)
        data['state']='committed';_write(root,data)
    except BaseException:
        recover(root)
        raise
    recover(root)
