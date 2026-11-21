import hashlib, subprocess, re, json, os, sys, difflib
repo = sys.argv[1]; inv = json.load(open('/home/claude/inv/datos.json'))
pairs = {
 'BO- DECRETO SUPREMO - LABORAL - DS-28699.pdf':'laboral/decreto-supremo-28699.pdf',
 'Ley-223-2012-Personas-con-discapacidad.pdf':'personas-con-discapacidad/ley-223.pdf',
 'Código de las familas y del proceso familiar.pdf':'familia/ley-603-codigo-de-las-familias.pdf',
 'Código niño niña adolescente.pdf':'familia/codigo-nina-nino-y-adolescente-ley-548.pdf',
 'Ley N° 2027 ESTATUTO DEL FUNCIONARIO PUBLICO.pdf':'administrativa/ley-2027.pdf',
 'ley348 - LEY INTEGRAL PARA GARANTIZAR A LAS MUJERES UNA VIDA LIBRE DEVIOLENCIA .pdf':'penal/ley-348.pdf',
}
def norm(t): return re.sub(r'[^a-z0-9áéíóúñ]+',' ', t.lower()).split()
allrepo = {}
for d,_,fs in os.walk(os.path.join(repo,'biblioteca/pdf')):
    for f in fs:
        if f.endswith('.pdf'):
            p=os.path.join(d,f); allrepo[hashlib.sha256(open(p,'rb').read()).hexdigest()]=os.path.relpath(p,repo)
p=os.path.join(repo,'jurisprudencia/pdf/resumenes-de-jurisprudencia-tsj-2022.pdf'); allrepo[hashlib.sha256(open(p,'rb').read()).hexdigest()]=p
for r in inv:
    if r['sha'] in allrepo: print('IDENTICO sha:', r['rel'], '->', allrepo[r['sha']])
for a,b in pairs.items():
    r = next(x for x in inv if x['rel']==a)
    ta = norm(open(f"/home/claude/inv/{r['sha'][:12]}.txt").read())
    pb = os.path.join(repo,'biblioteca/pdf',b)
    tb = norm(subprocess.run(['pdftotext',pb,'-'],capture_output=True,text=True).stdout)
    pages = re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo',pb],capture_output=True,text=True).stdout).group(1)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False) if len(ta)*len(tb) < 4e9 else None
    ratio = sm.quick_ratio()
    print(f"{a[:45]:45} | repo {b} ({os.path.getsize(pb)} B, {pages} p) | palabras {len(ta)} vs {len(tb)} | quick_ratio {ratio:.3f}")
