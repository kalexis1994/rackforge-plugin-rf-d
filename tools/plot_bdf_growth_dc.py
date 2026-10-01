"""Saved-data figure: controller sensitivity, baseline gate and attempt counts."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"artifacts/plot-libs"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from loudness_latch_bdf_survey import trace
from loudness_latch_bdf_doubling_survey import OUTPUTS,SUMMARY as BASELINE
from loudness_latch_bdf_doubling_sampling import OUTPUT as BASELINE_QUERIES
from loudness_latch_bdf_growth_dc import OUTPUT as GROWTH,SUMMARY as SURVEY
from loudness_latch_bdf_growth_dc_sampling import OUTPUT as QUERIES

OUTPUT=ROOT/"evidence/loudness_latch_bdf_growth_dc_comparison.png"
METADATA=OUTPUT.with_suffix(".json")


def load_trace(path):
    case=json.loads(gzip.decompress(path.read_bytes()))["case"]
    return trace(case)


def maximum_curve(a,b):
    ta,va=a;tb,vb=b;start=max(ta[1],tb[1]);end=min(ta[-1],tb[-1])
    t=np.unique(np.concatenate((ta,tb)));t=t[(t>=start)&(t<=end)]
    av=np.column_stack([np.interp(t,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(t,tb,vb[:,k]) for k in range(94)])
    return t,np.max(np.abs(av-bv),axis=1)


def generate():
    paths=(*OUTPUTS,BASELINE,BASELINE_QUERIES,GROWTH,SURVEY,QUERIES,
           Path(__file__).resolve(),ROOT/"requirements-plot.txt")
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    traces=[load_trace(p) for p in (*OUTPUTS,GROWTH)]
    baseline=json.loads(BASELINE.read_text(encoding="utf-8"))
    survey=json.loads(SURVEY.read_text(encoding="utf-8"))
    rows=json.loads(gzip.decompress(QUERIES.read_bytes()))["contrasts"]
    old=json.loads(gzip.decompress(BASELINE_QUERIES.read_bytes()))
    pairs=((0,1,"D4 / E4 (original)","#737373",old["rows"]),
           (0,2,"D4 / E4G8","#28628e",rows[0]["rows"]),
           (1,2,"E4 / E4G8","#dc7828",rows[1]["rows"]))
    center=max((old["sampled_comparison"],*(r["sampled_comparison"] for r in rows)),
               key=lambda r:r["maximum_node_difference_v"])["maximum_difference_time_s"]
    maxima=[]
    with plt.rc_context({"font.size":10,"axes.spines.top":False,"axes.spines.right":False}):
        fig,axes=plt.subplots(1,3,figsize=(16,4.8),layout="constrained",width_ratios=(1.25,1.25,.8))
        for a,b,label,color,observed in pairs:
            t,v=maximum_curve(traces[a],traces[b]);valid=[r for r in observed if r["valid_both"]]
            qt=np.array([r["time_s"] for r in valid]);qv=np.array([r["maximum_node_difference_v"] for r in valid])
            maxima.append(dict(label=label,interpolated_v=float(np.max(v)),sampled_v=float(np.max(qv))))
            for ax in axes[:2]:
                ax.semilogy(t*1e3,np.maximum(v*1e3,1e-9),color=color,lw=1,label=label)
                ax.scatter(qt*1e3,np.maximum(qv*1e3,1e-9),color=color,s=9,zorder=3)
        for ax in axes[:2]:
            ax.axhline(1.,color="#b63232",ls="--",lw=1.2)
            ax.set_xlabel("Tiempo (ms)");ax.set_ylabel("Máximo de 94 nodos (mV)");ax.grid(alpha=.2)
        axes[0].set_xlim(0,3);axes[0].set_title("Trayectorias desde DC");axes[0].legend(loc="lower left",fontsize=8)
        axes[1].set_xlim((center-15e-6)*1e3,(center+15e-6)*1e3);axes[1].set_title("Región del máximo consultado")
        counts=[(c["accepted_trials"],c["rejected_trials"]) for c in baseline["cases"]]+[
            (survey["case"]["accepted_trials"],survey["case"]["rejected_trials"])]
        accepted,rejected=zip(*counts);x=np.arange(3)
        axes[2].bar(x,accepted,color="#28628e",label="Intentos aceptados")
        axes[2].bar(x,rejected,bottom=accepted,color="#dc7828",label="Rechazados")
        axes[2].set_xticks(x,("D4","E4","E4G8"));axes[2].set_title("Costo contado, sin deadline")
        axes[2].set_ylabel("Intentos");axes[2].legend(fontsize=8,loc="upper left")
        for k,(a,r) in enumerate(counts):axes[2].text(k,a+r+70,str(a+r),ha="center",fontsize=9)
        axes[2].set_ylim(0,max(a+r for a,r in counts)*1.22)
        fig.suptitle("RF-D · sensibilidad al crecimiento BDF2 · gate original: 1 mV",fontsize=14)
        fig.supxlabel("Líneas: interpolación · puntos: consultas conservativas · cargas sintéticas · selección finita, sin cota continua",fontsize=9)
        fig.savefig(OUTPUT,dpi=160);plt.close(fig)
    after={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if after!=before:raise ValueError("growth plot inputs changed")
    metadata=dict(schema="rf-d/bdf-growth-dc-plot/v1",source_sha256=before,
        numpy=np.__version__,matplotlib=matplotlib.__version__,
        image_sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        logarithmic_display_floor_mv=1e-9,comparisons=maxima,
        generated_from_saved_data_only=True,temporal_refinement_admitted=False,
        physical_switching_admitted=False,audio_admitted=False)
    METADATA.write_text(json.dumps(metadata,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return metadata


if __name__=="__main__":print(json.dumps(generate()))
