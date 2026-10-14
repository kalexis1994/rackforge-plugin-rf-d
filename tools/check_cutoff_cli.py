"""Adapt four admitted CLI publication checks to explicit charged source events."""
from prepare_vco1_portable import ROOT
def main():
 s=(ROOT/'tools/check_extended_cli.py').read_text(encoding='utf8')
 s=s.replace('from render_extended_release import inputs','from render_voice_cutoff import inputs').replace('tools/check_extended_cli.py','tools/check_cutoff_cli.py').replace('tools/extended_render_cli.py','tools/cutoff_render_cli.py').replace('tools/render_extended_release.py','tools/render_voice_cutoff.py').replace('evidence/voice_extended_listening01.json','evidence/voice_cutoff_listening01.json').replace("'extended-release01']","'extended-release01','long-tail01','voice-retrigger01','voice-cutoff01']").replace('references-local/extended-cli01','references-local/cutoff-cli01').replace("['held','release','controlled','extended']","['held','release','controlled','extended','tail','retrigger','cutoff']").replace("meta['frames']==3264","meta['frames']==7872").replace("not meta['new_source_event']","meta['new_source_event']").replace('full extended seam state','full cutoff seam state').replace('BOUNDARY,0,23300407296','BOUNDARY,0,82022760448').replace('complete extended observations','complete cutoff observations').replace('evidence/voice_extended_cli01.json','evidence/voice_cutoff_cli01.json')
 s=s.replace("names=['tools/check_cutoff_cli.py'", "names=['tools/check_extended_cli.py','tools/render_extended_release.py','tools/render_long_tail.py','tools/check_cutoff_cli.py'")
 s=s.replace("for n in ['incoming-original.ckp','final.ckp']:", "for n in ['incoming-original.ckp','final.ckp','event1-before.ckp','event1-after.ckp','event2-before.ckp','event2-after.ckp']:")
 s=s.replace("names=['tools/check_extended_cli.py'", "names=['tools/prepare_cutoff_render.py','tools/render_voice_retrigger.py','tools/check_extended_cli.py'")
 scope={'__name__':'cutoff_cli_harness'};exec(compile(s,'<admitted-cli-checks-cutoff>','exec'),scope);scope['main']()
if __name__=='__main__':main()
