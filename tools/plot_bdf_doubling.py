"""Plot stored numerical comparisons; never recompute or alter trajectories."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
# Optional plotting libraries are isolated from the circuit environment.
sys.path.insert(0,str(ROOT/"artifacts/plot-libs"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from loudness_latch_bdf_survey import trace
from loudness_latch_bdf_doubling_survey import OUTPUTS,SUMMARY as SURVEY
from loudness_latch_bdf_doubling_sampling import OUTPUT as OBSERVATIONS

OUTPUT=ROOT/"evidence/loudness_latch_bdf_doubling_comparison.png"
METADATA=OUTPUT.with_suffix(".json")


def generate():
    paths=(*OUTPUTS,SURVEY,OBSERVATIONS,Path(__file__).resolve(),ROOT/"requirements-plot.txt")
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    cases=[json.loads(gzip.decompress(p.read_bytes()))["case"] for p in OUTPUTS]
    report=json.loads(gzip.decompress(OBSERVATIONS.read_bytes()))
    survey=json.loads(SURVEY.read_text())
    (ta,va),(tb,vb)=[trace(c) for c in cases]
    start=max(ta[1],tb[1]);end=min(ta[-1],tb[-1])
    t=np.unique(np.concatenate((ta,tb)));t=t[(t>=start)&(t<=end)]
    av=np.column_stack([np.interp(t,ta,va[:,k]) for k in range(94)])
    bv=np.column_stack([np.interp(t,tb,vb[:,k]) for k in range(94)])
    delta=np.max(np.abs(av-bv),axis=1)
    rows=[r for r in report["rows"] if r["valid_both"]]
    qt=np.array([r["time_s"] for r in rows]);qv=np.array([r["maximum_node_difference_v"] for r in rows])
    center=report["sampled_comparison"]["maximum_difference_time_s"]
    with plt.rc_context({"font.size":10,"axes.spines.top":False,"axes.spines.right":False}):
        fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout="constrained")
        for ax in axes:
            ax.semilogy(t*1e3,np.maximum(delta*1e3,1e-9),color="#28628e",lw=1.3,label="Mallas interpoladas, máximo de 94 nodos")
            ax.scatter(qt*1e3,np.maximum(qv*1e3,1e-9),color="#dc7828",s=13,zorder=3,label="Consultas conservativas al mismo tiempo")
            ax.axhline(1.,color="#b63232",ls="--",lw=1.2,label="Gate: 1 mV")
            ax.set_xlabel("Tiempo (ms)");ax.set_ylabel("Diferencia máxima D4/E4 (mV)")
            ax.grid(alpha=.2,which="major")
        axes[0].set_xlim(0,end*1e3);axes[0].set_title("Desde DC hasta el destino común")
        axes[1].set_xlim(max(start,center-15e-6)*1e3,min(end,center+15e-6)*1e3)
        axes[1].set_title("Región del máximo consultado")
        axes[0].legend(loc="lower left",fontsize=8)
        fig.suptitle("RF-D · BDF2 con doble paso · comparación numérica",fontsize=14)
        fig.supxlabel("KEY 0→10 V · BUS=0 · R61=200 Ω · cargas sintéticas · consultas finitas, sin cota continua",fontsize=9)
        fig.savefig(OUTPUT,dpi=160)
        plt.close(fig)
    after={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if after!=before:raise ValueError("plot inputs changed")
    metadata=dict(schema="rf-d/bdf-doubling-plot/v1",source_sha256=before,numpy=np.__version__,
        matplotlib=matplotlib.__version__,image_sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        logarithmic_display_floor_mv=1e-9,
        interpolation_peak_v=float(np.max(delta)),sampled_peak_v=float(np.max(qv)),
        survey_interpolation_peak_v=survey["refinement"]["maximum_node_difference_v"],
        generated_from_saved_data_only=True,physical_switching_admitted=False,audio_admitted=False)
    METADATA.write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    return metadata


if __name__=="__main__":print(json.dumps(generate()))
