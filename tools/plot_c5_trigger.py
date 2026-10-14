"""Plot measured native GRID observations without changing the trajectories."""
import csv,json
from pathlib import Path
from run_c5_trigger import ROOT,sha,write
def main():
    import xml.etree.ElementTree as ET
    receipt=json.loads((ROOT/'evidence/c5_trigger_native02.json').read_text());inputs={};series={}
    for p in receipt['profiles']:
        if p['optional'] or p['maximum_us']!=4:continue
        path=ROOT/receipt['output_directory']/(p['label']+'.stdout');assert sha(path)==p['stdout_sha256'];inputs[path.relative_to(ROOT).as_posix()]=sha(path)
        samples=[]
        for row in csv.reader(path.read_text().splitlines()):
            if row[0]!='GRID':continue
            v=list(map(float,row[1:]));s=[h+l for h,l in zip(v[3:57],v[57:111])]
            samples.append(dict(ms=v[0]/1073741824/1000.,c5_v=s[38],c2_v=s[5],reset_driver_v=s[17]))
        series[p['mode']]=samples
    svg=ROOT/'evidence/c5_trigger_observation01.svg'
    root=ET.Element('svg',dict(xmlns='http://www.w3.org/2000/svg',width='1000',height='720',viewBox='0 0 1000 720'))
    def element(kind,attrs,text=None):
        node=ET.SubElement(root,kind,{k:str(v) for k,v in attrs.items()})
        if text is not None:node.text=text
    element('rect',dict(x=0,y=0,width=1000,height=720,fill='#fafafa'))
    def label(x,y,text,size=12,color='#333333'):
        element('text',dict(x=x,y=y,fill=color,**{'font-family':'Segoe UI, Arial, sans-serif','font-size':size}),text)
    label(78,38,'RF-D · ambos contornos con gatillo compartido',22)
    colors={'key':'#1767a6','s':'#c26510'}
    for mode,x in [('key',80),('s',340)]:
        element('line',dict(x1=x,y1=62,x2=x+22,y2=62,stroke=colors[mode],**{'stroke-width':3}))
        label(x+30,66,'Teclado: KEY 0/10 V' if mode=='key' else 'Contacto S abierto/cerrado')
    for field,title,top,ceiling in [('c5_v','Temporizador de filtro — C5',110,7),('c2_v','Temporizador de volumen — C2',290,7),('reset_driver_v','Reset compartido — colector Q12',470,10)]:
        height=135;left=78;width=868
        label(left,top-10,title,15)
        for start,end in [(1,10),(20,30)]:
            element('rect',dict(x=left+width*start/36,y=top,width=width*(end-start)/36,height=height,fill='#eeeeee'))
        for value in range(0,ceiling+1):
            y=top+height-height*value/ceiling
            element('line',dict(x1=left,y1=y,x2=left+width,y2=y,stroke='#dddddd',**{'stroke-width':.5}))
            if ceiling==7 or value%2==0:label(left-24,y+4,str(value),10)
        label(32,top+20,'V',12)
        for mode,data in series.items():
            points=' '.join(f"{left+width*v['ms']/36:.6f},{top+height-height*v[field]/ceiling:.6f}" for v in data)
            element('polyline',dict(points=points,fill='none',stroke=colors[mode],**{'stroke-width':2}))
        element('line',dict(x1=left,y1=top+height,x2=left+width,y2=top+height,stroke='#888888'))
    for value in [0,5,10,15,20,25,30,36]:label(78+868*value/36-6,627,str(value),11)
    label(388,650,'Tiempo simulado (ms)',13)
    label(78,678,'Modelo nominal · rieles/VCA/TAIL impuestos · observaciones cada 0,25 ms',11)
    label(78,697,'Bandas: excitación de entrada. C5/C2 conservan memoria al liberar y retrigger. Sin calibración de hardware.',11)
    ET.ElementTree(root).write(svg,encoding='utf-8',xml_declaration=True)
    svg.write_bytes(svg.read_bytes().replace(b'\r\n',b'\n')+b'\n')
    import subprocess
    node='C:/Users/kalex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    sharp='C:/Users/kalex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'
    png=ROOT/'references-local/c5-trigger-checkpoint01/contours.png'
    javascript='require('+json.dumps(sharp)+')('+json.dumps(str(svg))+').png().toFile('+json.dumps(str(png))+').catch(e=>{console.error(e);process.exit(1);});'
    subprocess.run([node,'-e',javascript],check=True,timeout=30)
    write(ROOT/'evidence/c5_trigger_observation01.json',dict(passed=True,input_sha256=inputs,code_sha256={'tools/plot_c5_trigger.py':sha(Path(__file__))},
          output_sha256={svg.relative_to(ROOT).as_posix():sha(svg)},private_sha256={png.relative_to(ROOT).as_posix():sha(png)},
          series=series,normalization=False,dc_removed=False,physical_fidelity=False))
    print('C5_TRIGGER_OBSERVATIONS',len(series['key']),len(series['s']))
if __name__=='__main__':main()
