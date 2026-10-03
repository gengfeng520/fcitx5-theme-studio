"""Metadata for named designs stored locally."""
import json
from pathlib import Path

def metadata(title,description=''):
    return dict(title=str(title).strip()[:80] or '未命名作品',description=str(description)[:1000])

def read_meta(folder):
    d=json.loads((Path(folder)/'metadata.json').read_text())
    if not isinstance(d,dict):raise ValueError('作品信息无效')
    return metadata(d.get('title',''),d.get('description',''))
