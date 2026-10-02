"""Complete double-history tangent basis and Decimal product-rounding audit."""
from decimal import Decimal,localcontext
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from loudness_latch_bdf_static_precision_memory_long import OUTPUT as SOURCE,PATHS as OLD_PATHS
from loudness_latch_bdf_memory_transfer import CHARGE_SCALE_C_PER_V
from loudness_latch_bdf_doubling_survey import canonical,store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_basis.json.gz"
SUMMARY=ROOT/"evidence/loudness_latch_bdf_static_precision_memory_basis_summary.json"
PROTOCOL=ROOT/"docs/BIESTABLE_BASE_DOBLE_PROTOCOLO.md"
PATHS=tuple(dict.fromkeys((*OLD_PATHS,SOURCE,Path(__file__).resolve(),PROTOCOL)))
GATE=1e-8
PRECISIONS=(80,100)


def basis():
    return np.hstack((np.eye(25),np.zeros((25,25)))),np.hstack((np.zeros((25,25)),np.eye(25)))


def lift(matrix):
    return [[Decimal.from_float(float(v)) for v in row] for row in matrix]


def multiply(matrix,vector):
    """Ascending-index Decimal dot products; skip exact zeros only."""
    out=[]
    for row in matrix:
        values=[Decimal(0)]*len(vector[0])
        for k,c in enumerate(row):
            if not c:continue
            for i,v in enumerate(vector[k]):
                if v:values[i]+=c*v
        out.append(values)
    return out


def precise_step(operator,current,previous,precision):
    gamma=operator["coefficients"]["gamma"]
    a=Decimal.from_float(float(1+gamma));g=Decimal.from_float(float(gamma))
    with localcontext() as ctx:
        ctx.prec=precision
        virtual=[[a*u-g*v for u,v in zip(row,old)] for row,old in zip(current,previous)]
        return multiply(lift(operator["node_map"]),virtual),multiply(lift(operator["memory_map"]),virtual)


def rounded(matrix):return np.array([[float(v) for v in row] for row in matrix])
def digest(matrix):return hashlib.sha256(canonical([[str(v) for v in row] for row in matrix])).hexdigest()


def metrics(reference,candidate):
    delta=abs(candidate-reference);scaled=delta/(1+abs(reference))
    where=tuple(int(v) for v in np.unravel_index(np.argmax(scaled),scaled.shape))
    return dict(maximum_absolute_difference=float(np.max(delta)),maximum_scaled_difference=float(np.max(scaled)),
        row=where[0],column=where[1],reference_value=float(reference[where]),candidate_value=float(candidate[where]),
        passed=bool(np.isfinite(candidate).all() and np.max(scaled)<GATE))


def singular(matrix):
    _,s,v=np.linalg.svd(matrix,full_matrices=False)
    direction=v[0].copy();i=int(np.argmax(abs(direction)))
    if direction[i]<0:direction=-direction
    return dict(singular_values=s.tolist(),spectral_norm=float(s[0]),maximum_right_direction=direction.tolist())


def generate():
    before=hashes(PATHS);env=environment()
    source=json.loads(gzip.decompress(SOURCE.read_bytes()));windows=[]
    for w in source["windows"]:
        if len(w["operators"])!=64 or not w["reference_complete"]:raise ValueError("frozen complete 64-map window required")
        current,previous=basis();precise={p:(lift(current),lift(previous)) for p in PRECISIONS}
        rows=[];stop=None
        for index,(operator,reference) in enumerate(zip(w["operators"],w["reference"])):
            gamma=operator["coefficients"]["gamma"]
            virtual=(1+gamma)*current-gamma*previous
            nodes=np.array(operator["node_map"])@virtual;memory=np.array(operator["memory_map"])@virtual
            if not np.isfinite(nodes).all() or not np.isfinite(memory).all():
                stop=dict(index=index,error="nonfinite binary64 cumulative basis",current=current.tolist(),previous=previous.tolist());break
            results={p:precise_step(operator,*precise[p],p) for p in PRECISIONS}
            n80,m80=results[80];n100,m100=results[100]
            rn80=rounded(n80);rm80=rounded(m80)
            node_comparison=metrics(rn80,nodes);memory_comparison=metrics(rm80,memory)
            same_nodes=np.array_equal(rn80,rounded(n100));same_memory=np.array_equal(rm80,rounded(m100))
            row=dict(index=index,time_s=reference["history"]["time_s"],
                cumulative_node_matrix=nodes.tolist(),cumulative_memory_matrix=memory.tolist(),
                decimal80_rounded_node_matrix=rn80.tolist(),decimal80_rounded_memory_matrix=rm80.tolist(),
                decimal80_node_sha256=digest(n80),decimal80_memory_sha256=digest(m80),
                decimal100_node_sha256=digest(n100),decimal100_memory_sha256=digest(m100),
                decimal80_100_rounded_nodes_equal=same_nodes,decimal80_100_rounded_memory_equal=same_memory,
                node_rounding_comparison=node_comparison,memory_rounding_comparison=memory_comparison,
                node_basis=singular(nodes),memory_basis=singular(memory),double_history_basis=singular(np.vstack((memory,current))),
                product_gate_passed=node_comparison["passed"] and memory_comparison["passed"] and same_nodes and same_memory)
            rows.append(row)
            for p in PRECISIONS:precise[p]=(results[p][1],precise[p][0])
            previous,current=current,memory
        windows.append(dict(name=w["name"],initial_time_s=w["initial"]["time_s"],rows=rows,stop=stop,complete=len(rows)==64))
        print(json.dumps(dict(window=w["name"],intervals=len(rows),product_passes=sum(r["product_gate_passed"] for r in rows),
            maximum_node_basis_gain=max(r["node_basis"]["spectral_norm"] for r in rows))),flush=True)
    if hashes(PATHS)!=before:raise ValueError("basis-audit sources changed during execution")
    return dict(schema="rf-d/bdf-static-precision-memory-basis/v1",environment=env,source_sha256=before,
        windows=windows,precisions=PRECISIONS,product_scaled_gate=GATE,input_dimension=50,intervals_per_window=64,
        charge_coordinate_scale_c_per_v=CHARGE_SCALE_C_PER_V,new_nonlinear_solves=0,new_spatial_solves=0,
        operator_coefficients_lifted_exactly_from_binary64=True,unit_basis_is_finite_physical_injection=False,
        initial_current_basis=basis()[0].tolist(),initial_previous_basis=basis()[1].tolist(),
        full_nonlinear_direction_validation=False,global_temporal_error_bound_admitted=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,diagnostic_only=True,
        limitation="homogeneous tangent products on a fixed archived orbit and coordinate scale; no truncation forcing, affine defect, nonlinear bound or accepted physical histories")


def save(report):
    storage=store(report,OUTPUT);windows=[]
    for w in report["windows"]:
        rows=w["rows"];peaks={}
        for name in ("node_basis","memory_basis","double_history_basis"):
            i=max(range(len(rows)),key=lambda i:rows[i][name]["spectral_norm"])
            peaks[name]=dict(index=i,time_s=rows[i]["time_s"],**rows[i][name])
        windows.append(dict(name=w["name"],initial_time_s=w["initial_time_s"],end_s=rows[-1]["time_s"],
            intervals=len(rows),complete=w["complete"],stop=w["stop"],peaks=peaks,
            product_passes=sum(r["product_gate_passed"] for r in rows),
            decimal80_100_rounded_node_passes=sum(r["decimal80_100_rounded_nodes_equal"] for r in rows),
            decimal80_100_rounded_memory_passes=sum(r["decimal80_100_rounded_memory_equal"] for r in rows),
            maximum_scaled_node_product_error=max(r["node_rounding_comparison"]["maximum_scaled_difference"] for r in rows),
            maximum_scaled_memory_product_error=max(r["memory_rounding_comparison"]["maximum_scaled_difference"] for r in rows)))
    summary={k:v for k,v in report.items() if k not in ("windows","initial_current_basis","initial_previous_basis")}|dict(storage=storage,windows=windows)
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return summary


if __name__=="__main__":save(generate())
