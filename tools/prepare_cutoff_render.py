"""Declare the existing full audio/CLI gates with seven segments and cutoff codec."""
from prepare_vco1_portable import ROOT
from prepare_release_voice import once
from joint_cycles_analysis import require
def renderer():
 s=(ROOT/'tools/render_voice_retrigger.py').read_text(encoding='utf8').replace('retrigger','cutoff').replace('RETRIGGER','CUTOFF')
 s=s.replace('from render_long_tail import joined_trace as previous_trace,inputs as previous_inputs,CODEC','from render_voice_retrigger import joined_trace as previous_trace,inputs as previous_inputs\nCODEC=struct.Struct(\'<8sQ6IdQ2d458d\')')
 s=s.replace('BOUNDARIES,KEY,SHORT,DECAY','BOUNDARIES,KEY,SHORT,DECAY,ALPHA')
 s=s.replace('tail,cutoff):','tail,retrigger,cutoff):').replace('previous_inputs(held,release,controlled,extended,tail)','previous_inputs(held,release,controlled,extended,tail,retrigger)').replace('previous_trace(held,release,controlled,extended,tail)','previous_trace(held,release,controlled,extended,tail,retrigger)').replace('a=tail.read_text','a=retrigger.read_text')
 s=s.replace("'long-tail01','voice-cutoff01'", "'long-tail01','voice-retrigger01','voice-cutoff01'")
 s=s.replace('len(raw)==3728','len(raw)==3736').replace("b'RFDCY001'", "b'RFCTF001'").replace('q[5:11]==(phase,1,1+2*int(SHORT[phase]),KEY[phase],0,DECAY)', 'q[5:12]==(phase,1,1+2*int(SHORT[phase]),KEY[phase],0,DECAY,ALPHA[phase])').replace('raw[64:]','raw[72:]').replace('after[64:]','after[72:]').replace('before[56:]==after[56:]','before[56:64]==after[56:64] and before[72:]==after[72:] and before[32:56]==after[32:56]')
 old=" recipe(cutoff.with_name('incoming-original.ckp').read_bytes(),START,0,new);recipe(cutoff.with_name('final.ckp').read_bytes(),START+SPAN,2,last)"
 new=""" original=cutoff.with_name('incoming-original.ckp').read_bytes();require(len(original)==3728 and original[:8]==b'RFDCY001' and original[28:32]==struct.pack('<I',2),'own previous cutoff codec');converted=bytearray(original[:64]+struct.pack('<d',1.)+original[64:]);converted[:8]=b'RFCTF001';converted[28:32]=struct.pack('<I',0);recipe(converted,START,0,new);recipe(cutoff.with_name('final.ckp').read_bytes(),START+SPAN,2,last)"""
 s=once(s,old,new)
 s=s.replace('7104','7872').replace('148ms','164ms').replace('148 ms','164 ms').replace('.148008','.164012')
 s=s.replace("keyboard_v=KEY[i],short=SHORT[i])", "keyboard_v=KEY[i],short=SHORT[i],cutoff_fraction=ALPHA[i],previous_cutoff_fraction=ALPHA[i-1])")
 return s.replace('Join six actual traces','Join seven actual traces')
def cli():
 s=(ROOT/'tools/retrigger_render_cli.py').read_text(encoding='utf8').replace('retrigger','cutoff').replace('RETRIGGER','CUTOFF').replace('BOUNDARIES,KEY,SHORT,DECAY','BOUNDARIES,KEY,SHORT,DECAY,ALPHA')
 s=s.replace("'tail','cutoff']", "'tail','retrigger','cutoff']").replace("'assembly','assembly']", "'assembly','assembly','assembly']")
 s=s.replace("keyboard_v=KEY[i],short=SHORT[i])", "keyboard_v=KEY[i],short=SHORT[i],cutoff_fraction=ALPHA[i],previous_cutoff_fraction=ALPHA[i-1])")
 return s.replace('Render six native segments','Render seven native segments').replace('sample_rate_hz=48000,cutoff_hz=18000','sample_rate_hz=48000,resampling_cutoff_hz=18000')
def checker():
 s=(ROOT/'tools/check_retrigger_cli_attempt01.py').read_text(encoding='utf8').replace('retrigger','cutoff')
 s=s.replace("'long-tail01','voice-cutoff01']", "'long-tail01','voice-retrigger01','voice-cutoff01']").replace("'tail','cutoff']", "'tail','retrigger','cutoff']").replace('7104','7872').replace('73632055296','82022760448')
 anchor=" scope={'__name__':'cutoff_cli_harness'}"
 extra=''' s=s.replace("for n in ['incoming-original.ckp','final.ckp']:", "for n in ['incoming-original.ckp','final.ckp','event1-before.ckp','event1-after.ckp','event2-before.ckp','event2-after.ckp']:")
 s=s.replace("names=['tools/check_extended_cli.py'", "names=['tools/prepare_cutoff_render.py','tools/render_voice_retrigger.py','tools/check_extended_cli.py'")
'''
 return once(s,anchor,extra+anchor)
def main():
 for n,s in [('tools/render_voice_cutoff.py',renderer()),('tools/cutoff_render_cli.py',cli()),('tools/check_cutoff_cli.py',checker())]:
  p=ROOT/n;require(not p.exists(),'exclusive audio source');compile(s,n,'exec');p.write_text(s,encoding='utf8',newline='\n')
 print('CUTOFF_RENDER_PREPARED')
if __name__=='__main__':main()
