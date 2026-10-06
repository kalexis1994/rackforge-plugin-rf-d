"""Conditional level-1 JFET as channel current plus two charged junctions.

Restricted to the frozen B=1, RD=RS=0, 25 C card. This is a numerical
representation experiment; the reference device and its failures remain.
"""
from pathlib import Path
import voice_port_behavioral as ports
import vco1_circuit_reference as vco

ROOT=vco.ROOT


def channel_expression(d,g,s,card):
    v=f'v({d},{s})';a=f'max(v({g},{s})-({card["VTO"]:.17g}),0)'
    b=f'max(v({g},{d})-({card["VTO"]:.17g}),0)'
    def region(u,w):
        z=f'min({u},{w})'
        return f'{card["BETA"]:.17g}*(1+{card["LAMBDA"]:.17g}*({w}))*({z})*(2*({u})-({z}))'
    return f'{v}>=0 ? ({region(a,v)}) : -({region(b,"(-"+v+")")})'


def decompose(deck):
    device=vco.read(vco.DEVICES);card=device['jfet']
    if device['temperature_c']!=25 or card['TNOM']!=25 or card['LEVEL']!=1 or card['B']!=1 or card['RD'] or card['RS']:
        raise ValueError('frozen level-1 zero-series 25 C card required')
    lines=[];manifest=[];models=0
    for line in deck.splitlines():
        if line.startswith('.model LAB_E402 NJF('):models+=1;continue
        if line.startswith('J') and line.split()[-1]=='LAB_E402':
            ref,d,g,s,_=line.split()
            lines.append(f'Bchannel_{ref} {d} {s} I={channel_expression(d,g,s,card)}')
            for kind,other,c0 in (('gs',s,card['CGS']),('gd',d,card['CGD'])):
                model='E402_'+kind.upper()
                lines.append(f'Djunction_{ref}_{kind} {g} {other} {model}')
            manifest.append(dict(ref=ref,terminals=[d,g,s],channel='level1-B=1',
                junctions='N=1, M=.5, VJ=PB, FC=FC, TT=0; original IS/CGS/CGD and numerical gmin'))
        else:lines.append(line)
    if models!=1 or not manifest:raise ValueError('one frozen JFET card and devices required')
    cards=[]
    for kind,c0 in (('GS',card['CGS']),('GD',card['CGD'])):
        cards.append(f'.model E402_{kind} D(IS={card["IS"]:.17g} N=1 CJO={c0:.17g} VJ={card["PB"]:.17g} M=.5 FC={card["FC"]:.17g} TT=0 TNOM=25)')
    text='\n'.join(lines)+'\n'
    if text.count('.options ')!=1:raise ValueError('single numerical option block required')
    text=text.replace('.options ','\n'.join(cards)+'\n.options ',1)
    return text,manifest


def port_factory(s,side,t,x,with_contour):
    original,vectors=ports.factory(s,side,t,x,with_contour)
    def generate(scene,export):
        deck,meta=original(scene,export)
        if side=='vco':deck,meta['decomposed_jfets']=decompose(deck)
        meta['jfet_representation']='channel-plus-charged-diodes' if side=='vco' else 'no-jfet'
        meta['diagnostic_only']=True
        meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
        return deck,meta
    return generate,vectors
