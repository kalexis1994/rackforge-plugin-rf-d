"""Exact ideal time operators and manufactured nonlinear charge defect, offline."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import math
from circuit66_decimal_static import lift
from loudness_latch_directional_curvature import junction_values


def rational(value):
    value=F(value);return dict(numerator=value.numerator,denominator=value.denominator)


def weights(h,k):
    h=F(h);k=F(k)
    if h<=0 or k<=0 or h/k>2:raise ValueError('positive intervals and ratio <=2 required')
    return ((2*h+k)/(h*(h+k)),-(h+k)/(h*k),h/(k*(h+k)))


def lagrange_weights(times):
    """Derivative at the first timestamp; independent polynomial cardinal basis."""
    x=tuple(F(t) for t in times)
    if len(x)<2 or any(a<=b for a,b in zip(x,x[1:])):raise ValueError('strictly descending distinct times required')
    out=[]
    for i,ti in enumerate(x):
        others=[j for j in range(len(x)) if j!=i];den=math.prod(ti-x[j] for j in others)
        num=sum((math.prod(x[0]-x[j] for j in others if j!=m) for m in others),F(0))
        out.append(num/den)
    return tuple(out)


def kernel(h,k,u):
    h=F(h);k=F(k);u=F(u);weights(h,k)
    if u<-(h+k) or u>0:raise ValueError('point outside history interval')
    if u<-h:return -h*(u+h+k)**2/(2*k*(h+k))
    return u+(2*h+k)*u*u/(2*h*(h+k))


def kernel_polynomials(h,k):
    h=F(h);k=F(k);weights(h,k);s=h+k
    return ((-s,-h,{0:-h*s/(2*k),1:-h/k,2:-h/(2*k*s)}),
            (-h,F(0),{1:F(1),2:(2*h+k)/(2*h*s)}))


def polynomial(value,coefficients):
    return sum((c*value**i for i,c in enumerate(coefficients)),value*0)


def derivative(coefficients,order):
    result=list(coefficients)
    for _ in range(order):result=[i*c for i,c in enumerate(result)][1:]
    return result


def integrate_product(a,b,polys,coefficients):
    return sum((value*c*(b**(i+j+1)-a**(i+j+1))/F(i+j+1)
                for i,value in polys.items() for j,c in enumerate(coefficients)),F(0))


def peano_polynomial(h,k,coefficients):
    return sum((integrate_product(a,b,p,derivative(coefficients,3)) for a,b,p in kernel_polynomials(h,k)),F(0))


def decimal_fraction(value):
    value=F(value);return D(value.numerator)/D(value.denominator)


def charge_profile(parameters,junction,bias,time):
    t=lift(time);v=lift(bias)+100*t+20000*t*t+10000000*t*t*t
    velocity=100+40000*t+30000000*t*t;acceleration=40000+60000000*t;jerk=D(60000000)
    if junction=='be':dep=parameters.depletion_be;transit=parameters.transit_forward_s;scale=parameters.emission_be_v
    elif junction=='bc':dep=parameters.depletion_bc;transit=parameters.transit_reverse_s;scale=parameters.emission_bc_v
    else:raise ValueError('registered junction required')
    q,c,c2=junction_values(dep,transit,parameters.saturation_a,scale,v)
    potential=lift(dep.potential_v);grading=lift(dep.grading);cj=lift(dep.cj0_f)
    if v<lift(dep.forward_fraction*dep.potential_v):
        dep_c=cj*(-grading*(1-v/potential).ln()).exp()
        c3=dep_c*grading*(grading+1)/(potential-v)**2
    else:c3=D(0)
    exponent=v/lift(scale)
    if exponent>45:raise ValueError('charge exponential domain exceeded')
    c3+=lift(transit)*lift(parameters.saturation_a)*exponent.exp()/lift(scale)**3
    return dict(voltage_v=v,q_c=q,first_a=c*velocity,
                third_c_per_s3=c3*velocity**3+3*c2*velocity*acceleration+c*jerk)


def nonlinear_defect(parameters,junction,bias,h,k,precision=80):
    with localcontext() as ctx:
        ctx.prec=precision;h=F(h);k=F(k);w=weights(h,k)
        if junction not in ('be','bc'):raise ValueError('registered junction required')
        dep=parameters.depletion_be if junction=='be' else parameters.depletion_bc
        points=[charge_profile(parameters,junction,bias,decimal_fraction(t)) for t in (F(0),-h,-h-k)]
        knee=lift(dep.forward_fraction*dep.potential_v)
        if len({p['voltage_v']<knee for p in points})!=1:raise ValueError('manufactured profile crosses charge knee')
        # The chosen voltage polynomial has positive velocity everywhere:
        # discriminant 40000^2 - 4*30000000*100 <0, leading coefficient >0.
        value=sum((decimal_fraction(a)*p['q_c'] for a,p in zip(w,points)),D(0))-points[0]['first_a']
        return value


def nonlinear_integral(parameters,junction,bias,h,k,count,precision=80):
    if type(count) is not int or count<2 or count%2:raise ValueError('positive even Simpson count required')
    with localcontext() as ctx:
        ctx.prec=precision;h=F(h);k=F(k);nonlinear_defect(parameters,junction,bias,h,k,precision)
        total=D(0)
        for a,b,_ in kernel_polynomials(h,k):
            dt=(b-a)/count;values=[]
            for i in range(count+1):
                t=a+i*dt;factor=1 if i in (0,count) else 4 if i%2 else 2
                third=charge_profile(parameters,junction,bias,decimal_fraction(t))['third_c_per_s3']
                values.append(factor*decimal_fraction(kernel(h,k,t))*third)
            total+=decimal_fraction(dt)*sum(values,D(0))/3
        return total


def precision_metric(reference,candidate):
    with localcontext() as ctx:
        ctx.prec=80;r=abs(lift(candidate)-lift(reference))/(lift(1e-30)+lift(1e-8)*abs(lift(reference)))
        return dict(maximum_scaled_error=float(r),passed=r<1)


def series_terms(tau,effective_dt,capacitance,resistance):
    if effective_dt<=0 or capacitance<=0 or resistance<0:raise ValueError('positive RC domain required')
    beta=effective_dt/(effective_dt+capacitance*resistance)
    return beta,beta*tau,resistance*beta*tau
