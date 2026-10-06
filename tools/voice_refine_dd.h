/* RF-D laboratory double-pair arithmetic. No fast-math or reassociation.
 * Product operands: zero or 2^-400 <= abs(x) <= 2^400. This keeps products
 * and their exact FMA errors above underflow and below overflow. Outside
 * the declared domain we report failure, rather than silently approximate.
 */
#ifndef RF_DD_H
#define RF_DD_H
#include <math.h>
#include <float.h>
typedef struct { double hi, lo; } RFDD;
static int rf_operand(double x) {
    return isfinite(x) && (x==0.0 || (fabs(x)>=0x1p-400 && fabs(x)<=0x1p400));
}
static RFDD rf_two_sum(double a,double b) {
    RFDD r;double v;
    r.hi=a+b;v=r.hi-a;r.lo=(a-(r.hi-v))+(b-v);return r;
}
static int rf_good(RFDD x) { return isfinite(x.hi) && isfinite(x.lo); }
static int rf_product(double a,double b,RFDD *r) {
    if (!rf_operand(a) || !rf_operand(b)) return 0;
    r->hi=a*b;r->lo=fma(a,b,-r->hi);return rf_good(*r);
}
static RFDD rf_add(RFDD a,RFDD b) {
    RFDD s=rf_two_sum(a.hi,b.hi),t=rf_two_sum(a.lo,b.lo);
    RFDD e=rf_two_sum(s.lo,t.hi),u=rf_two_sum(s.hi,e.hi);
    return rf_two_sum(u.hi,u.lo+(e.lo+t.lo));
}
static int rf_ax(double a,RFDD x,RFDD *r) {
    RFDD p,q;
    if (!rf_product(a,x.hi,&p) || !rf_product(a,x.lo,&q))return 0;
    *r=rf_add(p,q);return rf_good(*r);
}
#endif
