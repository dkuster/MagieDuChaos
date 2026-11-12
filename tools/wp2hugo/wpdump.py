"""Lecture d'un dump MySQL (mysqldump) sans serveur MySQL.

Usage : load(path, tables) -> {table: [ {colonne: valeur}, ... ]}
"""
import re

create_re = re.compile(r'CREATE TABLE `([^`]+)`')
col_re = re.compile(r'^\s+`([^`]+)`')
esc = {'0':'\0','n':'\n','r':'\r','t':'\t','Z':'\x1a','b':'\b'}
def parse_values(s, i):
    out=[]
    n=len(s)
    while i<n:
        while i<n and s[i] in ' ,\n': i+=1
        if i>=n or s[i]==';': break
        assert s[i]=='(', s[i:i+50]
        i+=1; row=[]
        while True:
            c=s[i]
            if c=="'":
                i+=1; buf=[]
                while True:
                    c=s[i]
                    if c=='\\':
                        nx=s[i+1]; buf.append(esc.get(nx,nx)); i+=2
                    elif c=="'":
                        if s[i+1]=="'": buf.append("'"); i+=2
                        else: i+=1; break
                    else:
                        j=i
                        while s[j] not in "\\'": j+=1
                        buf.append(s[i:j]); i=j
                row.append(''.join(buf))
            else:
                j=i
                while s[j] not in ',)': j+=1
                v=s[i:j].strip(); row.append(None if v=='NULL' else v); i=j
            if s[i]==',': i+=1; continue
            if s[i]==')': i+=1; break
        out.append(row)
    return out

def load(path, tables):
    want = set(tables)
    cols = {}; rows = {t: [] for t in want}
    cur_table = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = create_re.match(line)
            if m:
                cur_table = m.group(1); cols[cur_table] = []; continue
            if cur_table and line.startswith(')'):
                cur_table = None; continue
            if cur_table:
                m = col_re.match(line)
                if m: cols[cur_table].append(m.group(1))
                continue
            if line.startswith('INSERT INTO `'):
                t = line[13:line.index('`', 13)]
                if t in want:
                    k = line.index('VALUES ') + 7
                    for r in parse_values(line, k):
                        rows[t].append(dict(zip(cols[t], r)))
    return rows
