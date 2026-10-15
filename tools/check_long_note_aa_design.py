"""Independent Decimal coefficient derivation and continuous-band interpolation bound."""
import json,math,re,traceback
from decimal import Decimal as D,localcontext,ROUND_FLOOR
import numpy as np
from prepare_dual_chain import ROOT,write
from affine_evidence import Sources
from prepare_long_note_aa import images
PI=D('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679')
def i0(x):
    z=x*x/4;term=total=D(1);k=0
    while True:
        k+=1;term*=z/(k*k);total+=term
        if abs(term)<D('1e-94'):return total
def sine(x):
    x-=((x+PI)/(2*PI)).to_integral_value(rounding=ROUND_FLOOR)*2*PI;term=total=x;k=0
    while True:
        k+=1;term*=-(x*x)/(2*k*(2*k+1));total+=term
        if abs(term)<D('1e-94'):return total
def decimal_taps(fs):
    M=fs//1000;beta=D('10.06126');out=[]
    for m in range(-M,M+1):
        arg=2*PI*22000*m/fs;sinc=sine(arg)/arg if m else D(1)
        out.append(D(44000)/fs*sinc*i0(beta*(1-(D(m)/M)**2).sqrt())/i0(beta))
    total=sum(out);return [x/total for x in out]
def coefficients(fs):
    s=(ROOT/'crates/rf-d-circuit/src/j7_antialias_coefficients.rs').read_text();body=re.search(rf'H{fs}:\[f64;\d+\]=\[(.*?)\];',s,re.S)[1]
    return np.array([float(v) for v in body.split(',') if v.strip()])
def audit():
    for n,s in images().items():assert (ROOT/n).read_bytes()==s.encode(),n
    reports=[]
    for fs in [192000,384000]:
        h=coefficients(fs);M=len(h)//2
        with localcontext() as ctx:
            ctx.prec=100;reference=decimal_taps(fs);error=max(abs(D.from_float(float(a))-b) for a,b in zip(h,reference))
        assert error<=D('2e-15');sym=float(max(abs(h-h[::-1])));dc=float(abs(sum(h)-1));assert sym<=1e-15 and dc<=1e-12 and M/fs==.001
        nfft=2**20;f=np.fft.rfftfreq(nfft,1/fs);z=np.fft.rfft(h,nfft);A=(z*np.exp(2j*np.pi*f*M/fs)).real
        def at(freq):return float(np.dot(h,np.cos(2*np.pi*freq*(np.arange(len(h))-M)/fs)))
        passvalues=np.r_[A[f<=20000],at(20000.)];stopvalues=np.r_[A[f>=24000],at(24000.),at(fs/2)]
        m=np.arange(1,M+1);curvature=float(2*(2*np.pi/fs)**2*np.sum(m*m*abs(h[M+1:])))
        allowance=curvature*(fs/nfft)**2/8+2e-12
        pass_low=float(min(passvalues)-allowance);pass_high=float(max(passvalues)+allowance);stop=float(max(abs(stopvalues))+allowance)
        assert pass_low>=10**(-.001/20) and pass_high<=10**(.001/20) and stop<=10**(-90/20)
        reports.append(dict(input_rate_hz=fs,taps=len(h),causal_delay_s=M/fs,dc_error=dc,symmetry_error=sym,decimal_coefficient_max_error=str(error),fft_points=nfft//2+1,curvature_bound_per_hz2=curvature,continuous_interpolation_and_roundoff_allowance=allowance,roundoff_allowance=2e-12,formal_interval_proof=False,passband_bound_db=max(abs(20*math.log10(pass_low)),abs(20*math.log10(pass_high))),stopband_bound_db=20*math.log10(stop),passband_max_hz=20000,stopband_min_hz=24000))
    return reports
def main():
    sources=Sources(['tools/check_long_note_aa_design.py','tools/prepare_long_note_aa.py','tools/j7_readout_probe.rs','tools/long_note_aa_probe.rs','crates/rf-d-circuit/src/j7_audio_readout.rs','crates/rf-d-circuit/src/j7_oversampled_readout.rs','crates/rf-d-circuit/src/j7_antialias_coefficients.rs','docs/LONG_NOTE_AA_PROTOCOLO.md']);r=dict(passed=False,**sources.fields(),numpy_version=np.__version__)
    try:r['filters']=audit();r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc()
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    sources.unchanged();k=1
    while(ROOT/f'evidence/long_note_aa_design{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/long_note_aa_design{k:02d}.json',r);print('LONG_NOTE_AA_DESIGN',r['passed'],r.get('filters'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
