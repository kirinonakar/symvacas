# Catalog function reference

Tap a template and fill its empty arguments (`[]`, `round(x,)`). Tap an example to insert it into the calculator. Search by function name, expression or description across all categories.

## Using the catalog
- Numeric trigonometry follows DEG/RAD/GRAD; explicit `pi` or `°` takes priority. Symbolic calculus uses radians.
- Enter matrices directly, for example `[[1,2],[3,4]]`.
- Saved functions appear under `Custom`. Import or export the library as JSON in Functions.
- In Python mode, the catalog inserts `calc.<function>(...)` and adds the shared import and symbols automatically.

## Step-by-step explanations

Equation mode includes explanations. In calculator mode, enable **Calc mode step by step** in Setup (off by default). Each result shows the available derivation, summary or verification.

- **Equations:** Linear/quadratic equations, factorable polynomials through degree 8, cubic Cardano steps, power substitutions and simple trigonometric/exponential/logarithmic equations, including Lambert W.
- **Systems:** Linear systems up to 6 equations and unknowns; substitution, symmetric quadratic systems and small two-variable polynomial elimination.
- **Inequalities:** One-variable polynomial/rational inequalities through degree 6: factors, interval signs and endpoint inclusion.
- **ODEs:** First-order separable/linear and homogeneous constant-coefficient second-order equations, with substitution checks.
- **Integration:** Substitution, parts and other available rules, including parameter cases. Example: `integrate(x*exp(x),x)`.
- **Differentiation:** Sum, product, quotient, power and chain rules through order 10.
- **Limits:** Cancellation, conjugates, L’Hôpital, highest powers, one-sided limits, local series and squeeze rules.

## Scientific
`sin(x)` — Sine of x (uses the current angle unit).
Example: sin(pi/6)
`cos(x)` — Cosine of x (uses the current angle unit).
Example: cos(0)
`tan(x)` — Tangent of x (uses the current angle unit).
Example: tan(pi/4)
`asin(x)` — Inverse sine; result is an angle in the current unit.
Example: asin(1)
`acos(x)` — Inverse cosine; result is an angle in the current unit.
Example: acos(0)
`atan(x)` — Inverse tangent; result is an angle in the current unit.
Example: atan(1)
`abs(x)` — Absolute value, magnitude or complex modulus |x|.
Example: abs(-3)
`floor(x)` — Greatest integer less than or equal to x.
Example: floor(2.7)
`ceil(x)` — Least integer greater than or equal to x.
Example: ceil(2.1)
`round(x,n)` — Round x to n decimal places using banker's rounding (half to even); n defaults to 0.
Example: round(2.5) → 2 (banker's rounding)
`roundh(x,n)` — Round x to n decimal places using round half up (half away from zero); n defaults to 0.
Example: roundh(2.5) → 3 (round half up)
`sign(x)` — Sign of x: −1, 0 or 1.
Example: sign(-5)
`sqrt(x)` — Principal square root.
Example: sqrt(16)
`cbrt(x)` — Cube root.
Example: cbrt(27)
`nthroot(x,n)` — Odd integer orders use the real root, including negative inputs; other orders use the principal root.
Example: nthroot(81,4)
`atan2(y,x)` — Angle of the point (x,y) across all four quadrants.
Example: atan2(1,1)
`frac(x)` — Fractional part, x − floor(x).
Example: frac(3.75)
`iPart(x)` — Integer part, truncating toward zero.
Example: iPart(-3.75)
`log(x,b)` — Logarithm of x to base b; base 10 is used when b is omitted.
Example: log(1000,10)
`ln(x)` — Natural logarithm.
Example: ln(e)
`exp(x)` — e raised to the power x.
Example: exp(1)
`sinc(x)` — sin(x) / x, with sinc(0) = 1.
Example: sinc(0)
`sinh(x)` — Hyperbolic sine.
Example: sinh(1)
`cosh(x)` — Hyperbolic cosine.
Example: cosh(0)
`tanh(x)` — Hyperbolic tangent.
Example: tanh(1)
`asinh(x)` — Inverse hyperbolic sine.
Example: asinh(1)
`acosh(x)` — Inverse hyperbolic cosine, defined for x ≥ 1.
Example: acosh(2)
`atanh(x)` — Inverse hyperbolic tangent, defined for |x| < 1.
Example: atanh(0.5)
`gamma(x)` — Gamma function.
Example: gamma(5)
`erf(x)` — Error function.
Example: erf(1)
`erfc(x)` — Complementary error function, 1 − erf(x).
Example: erfc(1)
`Ei(x)` — Exponential integral.
Example: Ei(1)
`Si(x)` — Sine integral.
Example: Si(1)
`Ci(x)` — Cosine integral.
Example: Ci(1)
`zeta(x)` — Riemann zeta function.
Example: zeta(2)
`factorial(n)` — n! for a non-negative integer.
Example: factorial(5)
`nCr(n,r)` — Binomial coefficient, combinations of n taken r at a time.
Example: nCr(5,2)
`nPr(n,r)` — Number of ordered permutations.
Example: nPr(5,2)
`gcd(a,b)` — Greatest common divisor.
Example: gcd(12,18)
`lcm(a,b)` — Least common multiple.
Example: lcm(4,6)
`prime(n)` — Returns the n-th prime number.
Example: prime(1000)
`isprime(n)` — Test primality for integers with |n| < 2^64; returns true or false.
Example: isprime(97)
`factorint(n)` — Prime factorization of a positive integer.
Example: factorint(360)
`divisors(n)` — Positive divisors of n in ascending order.
Example: divisors(28)
`rnd()` — Random real number in the interval [0,1).
Example: rnd()
`eng(x)` — Engineering notation with a power-of-three exponent.
Example: eng(12345)
`pol(x,y)` — Polar coordinates (r,θ) from rectangular (x,y).
Example: pol(1,1)
`rec(r,θ)` — Rectangular coordinates (x,y) from polar (r,θ).
Example: rec(1,0)
`randInt(a,b)` — Random integer in the inclusive range [a,b].
Example: randInt(1,6)
`sexagesimal(h,m,s)` — Hours, minutes and seconds converted to decimal degrees.
Example: sexagesimal(1,30,0)
`dms(x)` — Decimal degrees converted to degrees, minutes and seconds.
Example: dms(1.5)
`mixed(a,b,c)` — Mixed fraction a b/c.
Example: mixed(1,1,2)
`quotient(a,b)` — Integer quotient of a divided by b.
Example: quotient(17,5)
`remainder(a,b)` — Remainder of a divided by b.
Example: remainder(17,5)
`mod(a,b)` — Remainder of a divided by b; the mod operator gives the same result.
Example: mod(17,5)
`divmod(a,b)` — Integer quotient and remainder of a divided by b, as a list.
Example: divmod(17,5)
`sumdata(values)` — Sum of a list of values.
Example: sumdata([1,2,3])
`percent(x)` — x percent, x/100.
Example: percent(50)
`degree(x)` — An angle of x degrees converted to radians.
Example: degree(30)
`rad(x)` — Returns x unchanged and marks it as radians.
Example: rad(pi/2)
`gradian(x)` — An angle of x gradians converted to radians.
Example: gradian(100)
`fibonacci(n)` — n-th Fibonacci number.
Example: fibonacci(10)
`lucas(n)` — n-th Lucas number.
Example: lucas(10)
`bernoulli(n)` — n-th Bernoulli number.
Example: bernoulli(4)
`harmonic(n,m)` — Generalized harmonic number H(n,m); m defaults to 1.
Example: harmonic(5)
`subfactorial(n)` — Number of derangements of n items, !n.
Example: subfactorial(5)
`totient(n)` — Euler's totient φ(n).
Example: totient(10)
`divisor_sigma(n,k)` — Sum of the k-th powers of the divisors of n; k defaults to 1.
Example: divisor_sigma(12)
`primepi(x)` — Number of primes less than or equal to x.
Example: primepi(100)
`nextprime(n)` — Smallest prime greater than n.
Example: nextprime(100)
`prevprime(n)` — Largest prime less than n.
Example: prevprime(100)
`lambertw(x)` — Lambert W function, the inverse of x·e^x.
Example: lambertw(1)
`lambertw(z,k)` — Lambert W branch k (an integer). Branch 0 is the principal branch; branch −1 is also real on [−1/e,0).
Example: lambertw(-1,1)
`beta(a,b)` — Beta function B(a,b).
Example: beta(2,3)
`digamma(x)` — Logarithmic derivative of the gamma function.
Example: digamma(1)
`polygamma(n,x)` — n-th polygamma function.
Example: polygamma(1,1)
`besselj(n,x)` — Bessel function of the first kind.
Example: besselj(0,1)
`bessely(n,x)` — Bessel function of the second kind.
Example: bessely(0,1)
`besseli(n,x)` — Modified Bessel function of the first kind.
Example: besseli(0,1)
`besselk(n,x)` — Modified Bessel function of the second kind.
Example: besselk(0,1)

## Symbolic
`simplify(expr)` — Simplify an expression.
Example: simplify(sin(x)^2+cos(x)^2)
`expand(expr)` — Expand products and powers.
Example: expand((x+1)^3)
`factor(expr)` — Factor a polynomial over the rationals.
Example: factor(x^2-1)
`collect(expr,x)` — Collect terms as a polynomial in x.
Example: collect(x^2+2x+1,x)
`subs(expr,x,value)` — Substitute value for x.
Example: subs(x^2+1,x,3)
`diff(expr,x)` — First derivative with respect to x.
Example: diff(sin(x),x)
`diff(expr,x,n)` — n-th derivative with respect to x.
Example: diff(x^4,x,2)
`integrate(expr,x)` — Indefinite integral (antiderivative). Integral marks an unevaluated result; use nintegrate(expr,x,a,b) for numerical integration on valid finite bounds.
Example: integrate(x^2,x)
`integrate(sqrt(tan(x)),x)` — Uses t=sqrt(tan(x)) to reduce the integral to a rational function, returning logarithms, arctangents and C. Valid on continuous real intervals with tan(x)>0; the conditions are retained in Ans. The same rule covers suitable fractional tan/cot powers with affine real arguments and root order up to 4.
Example: integrate(sqrt(tan(x)),x)
`integrate(expr,x,a,b)` — Definite integral from a to b.
Example: integrate(x^2,x,0,1)
`limit(expr,x,a)` — Two-sided limit as x tends to a.
Example: limit(sin(x)/x,x,0)
`limit(expr,x,a,left)` — Limit approaching a from the left.
Example: limit(1/x,x,0,left)
`limit(expr,x,a,right)` — Limit approaching a from the right.
Example: limit(1/x,x,0,right)
`series(expr,x,a,n)` — Series expansion about a up to order n.
Example: series(exp(x),x,0,6)
`taylor(expr,x,a,n)` — Taylor polynomial of order n about a.
Example: taylor(sin(x),x,0,5)
`sum(expr,x,a,b)` — Summation of expr over integer x from a to b.
Example: sum(x^2,x,1,10)
`product(expr,x,a,b)` — Product of expr over integer x from a to b.
Example: product(x,x,1,5)
`solve(eq,x)` — Solve an equation or system for x; add real for real solutions. Unresolved simple one-variable equations can return partial numerical real roots from −10 to 10. ConditionSet marks an unresolved symbolic solution; use nsolve for a chosen interval.
Example: solve(x^2-5x+6=0,x)
`solve(eq,x,real)` — Explicitly restrict the domain for one equation and one variable; complex and integer are also supported. Existing assumptions still apply. Omit the domain to enable automatic real-domain retry for absolute-value equations.
Example: solve(abs(x-1)=3,x,real)
`solve(abs(x-1)=3,x)` — Absolute-value equations can be solved without setting a real assumption.
Example: solve(abs(x-1)=3,x) → {-2, 4}
`solve(exp(x)=x,x)` — Returns the entire complex family −LambertW(−1,k), k ∈ ℤ. An explicitly real domain returns EmptySet. Affine exponential equations can use this full-branch strategy; auxiliary solve results for other Lambert W equations are labeled partial rather than complete.

`solve(x*exp(x)=1,x)` — Lambert W solution: LambertW(1,k), k ∈ ℤ. Add real for LambertW(1) ≈ 0.5671432904.
Example: solve(exp(x)=x,x)
`solveset(expr,x,domain=S.Reals)` — Solution set of expr=0 or one equation, including periodic solutions. Domain: S.Reals / S.Complexes (default) / S.Integers / S.Rationals / S.Naturals / S.Naturals0. ConditionSet marks an unresolved result. Use RAD for this trigonometric example.
Example: solveset(sin(x) + 3*cos(x), x, domain=S.Reals)
`nsolve(expr,x,a,b)` — Numeric root search in the interval [a,b].
Example: nsolve(cos(x)-x,x,0,1)
`nintegrate(expr,x,a,b)` — Numeric definite integral from a to b.
Example: nintegrate(sin(x),x,0,pi)
`nderivative(expr,x,a)` — Numeric derivative evaluated at x = a.
Example: nderivative(sin(x),x,0)
`minimum(expr,x,a,b[,mode])` — Attained minimum on an interval, accounting for domain boundaries. Mode: closed=[a,b] (default), open=(a,b), leftopen=(a,b], rightopen=[a,b).
Example: minimum(x^2,x,-1,2)
`minimum(abs(x),x,-2,2)` — The minimum 0 is attained at x=0 even though the derivative is undefined there.
Example: minimum(abs(x),x,-2,2) → 0
`minimum(x,x,0,1,closed)` — The closed interval [0,1] includes x=0, so the minimum is 0.
Example: minimum(x,x,0,1,closed) → 0
`minimum(x,x,0,1,open)` — On (0,1): infimum 0, minimum none. Also applies to leftopen.
Example: minimum(x,x,0,1,open) → no minimum
`minimum(sqrt(x),x,-2,2)` — The real domain in this interval is [0,2]; the minimum 0 is attained at the domain boundary x=0.
Example: minimum(sqrt(x),x,-2,2) → 0
`minimum(1/x^2,x,-2,2)` — x=0 is excluded. The minimum 1/4 is attained at both x=-2 and x=2.
Example: minimum(1/x^2,x,-2,2) → 1/4
`minimum(x^2*(x/x),x,-2,2)` — The original domain excludes x=0: infimum 0, minimum none.
Example: minimum(x^2*(x/x),x,-2,2) → no minimum
`maximum(expr,x,a,b[,mode])` — Attained maximum on an interval, accounting for domain boundaries. Mode: closed=[a,b] (default), open=(a,b), leftopen=(a,b], rightopen=[a,b).
Example: maximum(x^2,x,-1,2)
`maximum(abs(x),x,-2,2)` — The maximum 2 is attained at both endpoints x=-2 and x=2.
Example: maximum(abs(x),x,-2,2) → 2
`maximum(abs(x),x,-2,2,open)` — On (−2,2): supremum 2, maximum none.
Example: maximum(abs(x),x,-2,2,open) → no maximum
`maximum(1/x^2,x,-2,2)` — Unbounded above as x approaches 0: maximum none.
Example: maximum(1/x^2,x,-2,2) → no maximum
`piecewise([expr,cond],...)` — Piecewise-defined function.
Example: piecewise([1,x>0],[0,true])

Graphs accept `{condition:value,...,default}` and use the first matching branch. Add `{condition}` after an expression to restrict its domain. Examples: `f(x)={x<0:x^2,x>=0:2*x}`, `y=x^2 {0<=x<=2}`.
Graph angles: select a curve and x (t for parametric/polar) for **Tangent angle** (0–180°). **Intersection angle** uses two Cartesian curves and an a–b interval to find the smaller tangent angles (0–90°). Results include degrees and radians; tap a point to select a branch.

`apart(expr,x)` — Partial-fraction decomposition in x.
Example: apart(1/(x*(x+1)),x)
`partfrac(expr,x)` — Partial fractions; alias of apart.
Example: partfrac(1/(x^2-1),x)
`together(expr)` — Combine terms into a single fraction.
Example: together(1/x+1/(x+1))
`cancel(expr)` — Cancel common factors in a rational expression.
Example: cancel((x^2-1)/(x-1))
`trigsimp(expr)` — Simplify using trigonometric identities.
Example: trigsimp(sin(x)^2+cos(x)^2)
`trigexpand(expr)` — Expand trigonometric functions of sums and multiples.
Example: trigexpand(sin(x+y))
`powsimp(expr)` — Combine powers that share a base.
Example: powsimp(x^a*x^b)
`powdenest(expr)` — Simplify nested powers and radicals.
Example: powdenest((x^2)^(1/2))
`hyperexpand(expr)` — Expand hypergeometric functions.
Example: hyperexpand(exp(x))
`nsimplify(expr)` — Guess an exact closed form for a numeric value.
Example: nsimplify(0.333333)
`comDenom(expr)` — Common denominator of a sum of fractions.
Example: comDenom(1/(x+1)+1/(x+2))
`numden(expr)` — Numerator and denominator of an expression.
Example: numden((x+1)/(x-1))
`coeff(expr,x)` — Coefficient of the indicated power of x.
Example: coeff(3x^2+2x+1,x)
`quo(a,b,x)` — Polynomial quotient of a divided by b in x.
Example: quo(x^3-1,x-1,x)
`rem(a,b,x)` — Polynomial remainder of a divided by b in x.
Example: rem(x^3-1,x-1,x)
`resultant(a,b,x)` — Resultant of two polynomials in x.
Example: resultant(x^2-1,x-2,x)
`discriminant(poly,x)` — Discriminant of a polynomial in x.
Example: discriminant(x^2-4x+3,x) → 4
`domain(expr,x)` — Real domain of the expression in x.
Example: domain(1/(x-1),x)
`range(expr,x)` — Range of the expression over its domain.
Example: range(x^2,x)
`roots(poly,x)` — Exact roots of a polynomial with their multiplicities.
Example: roots(x^2-1,x)
`real_roots(poly,x)` — Real roots of a polynomial.
Example: real_roots(x^3-1,x)

## Complex
`re(z)` — Real part of a complex number.
Example: re(3+4i)
`im(z)` — Imaginary part of a complex number.
Example: im(3+4i)
`conj(z)` — Complex conjugate.
Example: conj(3+4i)
`abs(z)` — Modulus (absolute value) of a complex number.
Example: abs(3+4i)
`arg(z)` — Argument (angle) of a complex number.
Example: arg(1+i)
`polar(r,θ)` — Complex number in polar form, r·e^(iθ).
Example: polar(2,pi/3)
`rectpolar(z)` — Rectangular and polar forms of a complex number.
Example: rectpolar(1+i)

## ODE & transforms
`dsolve(eq,y(t),t)` — Solve an ordinary differential equation. Classification is limited to 3 seconds and the selected method to 8 seconds. If symbolic solving is unavailable, use the numerical differential-equation graph with an initial value.
Example: dsolve(diff(y(t),t)=y(t),y(t),t)
`laplace(f,t,s)` — Laplace transform from the time variable t to s.
Example: laplace(sin(t),t,s)
`ilaplace(F,s,t)` — Inverse Laplace transform from s back to t.
Example: ilaplace(1/(s^2+1),s,t)
`fourier(f,t,w)` — Fourier transform from t to w using the e^(-2πiwt) kernel (ordinary frequency).
Example: fourier(exp(-t^2),t,w)
`ifourier(F,w,t)` — Inverse Fourier transform from w back to t.
Example: ifourier(exp(-w^2/4),w,t)
`fft(list)` — Discrete fast Fourier transform of a list.
Example: fft([1,0,0,0])
`ifft(list)` — Inverse discrete fast Fourier transform of a list.
Example: ifft([1,1,1,1])
`ztrans(f,n,z)` — Unilateral Z-transform of the sequence f(n): the sum of f(n)/z^n for n ≥ 0.
Example: ztrans(a^n,n,z)
`invztrans(F,z,n)` — Inverse Z-transform of a rational F(z), reconstructed from its poles.
Example: invztrans(z/(z-2),z,n)
`mellin(f,x,s)` — Mellin transform; its fundamental convergence strip is reported with the result.
Example: mellin(exp(-x),x,s)
`invmellin(F,s,x)` — Inverse Mellin transform; pass the convergence strip as two extra arguments to override the inferred one.
Example: invmellin(gamma(s),s,x)
`pdsolve(eq,u(x,y))` — Solve a first-order partial differential equation.
Example: pdsolve(diff(u(x,y),x)+diff(u(x,y),y)=0,u(x,y))
`rsolve(eq,y(n))` — Solve a recurrence relation for the sequence y(n).
Example: rsolve(y(n)=2*y(n-1),y(n))
`rsolve(eq,y(n),conds)` — The same with initial conditions, given as equations.
Example: rsolve(y(n)=y(n-1)+1,y(n),[y(0)=0])

## Vector calculus
`gradient(f,[x,y])` — Gradient vector of a scalar field.
Example: gradient(x^2+y^2,[x,y])
`divergence(f,[x,y])` — Divergence of a vector field.
Example: divergence([x,y],[x,y])
`curl(f,[x,y])` — Curl of a two- or three-dimensional vector field.
Example: curl([-y,x],[x,y])
`hessian(f,[x,y])` — Hessian matrix of second derivatives.
Example: hessian(x^2*y,[x,y])
`jacobian(f,[x,y])` — Jacobian matrix of a vector function.
Example: jacobian([x*y,x+y],[x,y])
`laplacian(f,[x,y])` — Laplacian of a scalar field.
Example: laplacian(x^2+y^2,[x,y])

## Matrix & vector
`det(A)` — Determinant.
Example: det([[1,2],[3,4]])
`inverse(A)` — Matrix inverse.
Example: inverse([[1,2],[3,4]])
`transpose(A)` — Transpose.
Example: transpose([[1,2],[3,4]])
`rank(A)` — Rank.
Example: rank([[1,2],[2,4]])
`trace(A)` — Trace, the sum of the diagonal entries.
Example: trace([[1,2],[3,4]])
`ref(A)` — Row echelon form.
Example: ref([[1,2],[3,4]])
`rref(A)` — Reduced row echelon form.
Example: rref([[1,2],[3,4]])
`lu(A)` — LU decomposition with row permutations.
Example: lu([[2,1],[1,3]])
`linsolve(A,b)` — Solve the linear system A·x = b.
Example: linsolve([[2,1],[1,3]],[1,2])
`eigenvalues(A)` — Eigenvalues with algebraic multiplicities, returned as [eigenvalue,multiplicity] pairs.
Example: eigenvalues([[2,0],[0,3]])
`eigenvectors(A)` — Eigenvectors.
Example: eigenvectors([[2,0],[0,3]])
`dot(u,v)` — Dot product.
Example: dot([1,2,3],[4,5,6])
`cross(u,v)` — Cross product of two three-dimensional vectors.
Example: cross([1,0,0],[0,1,0])
`norm(v)` — Euclidean norm (length) of a vector.
Example: norm([3,4])
`normalize(v)` — Unit vector in the direction of v.
Example: normalize([3,4])
`angle(u,v)` — Angle between two vectors.
Example: angle([1,0],[0,1])
`projection(u,v)` — Projection of u onto v.
Example: projection([1,1],[1,0])
`charpoly(A,x)` — Characteristic polynomial in x.
Example: charpoly([[1,2],[3,4]],x)
`identity(n)` — n×n identity matrix.
Example: identity(3)
`diag(list)` — Diagonal matrix built from a list.
Example: diag([1,2,3])
`qr(A)` — QR decomposition.
Example: qr([[1,2],[3,4]])
`cholesky(A)` — Cholesky decomposition, A = L·Lᵀ.
Example: cholesky([[4,2],[2,3]])
`nullspace(A)` — Basis of the null space.
Example: nullspace([[1,2],[2,4]])
`cofactor(A)` — Matrix of cofactors.
Example: cofactor([[1,2],[3,4]])
`adjugate(A)` — Adjugate (classical adjoint) matrix.
Example: adjugate([[1,2],[3,4]])
`rowspace(A)` — Basis of the row space.
Example: rowspace([[1,2],[3,4]])
`singularvalues(A)` — Singular values.
Example: singularvalues([[1,0],[0,2]])
`frob(A)` — Frobenius norm.
Example: frob([[1,2],[3,4]])
`jordan(A)` — Jordan canonical form.
Example: jordan([[2,1],[0,2]])
`dim(v)` — Dimension of a vector or length of a list.
Example: dim([1,2,3])
`pinv(A)` — Moore-Penrose pseudoinverse.
Example: pinv([[1,2],[3,4]])
`ctranspose(A)` — Conjugate (Hermitian) transpose.
Example: ctranspose([[1,2],[3,4]])
`svd(A)` — Singular value decomposition as [U, S, V]; the symbolic result can be large.
Example: svd([[1,0],[0,2]])

## Stats — choosing a test

```text
What do you want to compare?
├─ Numeric values
│  ├─ One sample vs a target mean → One-sample t test
│  ├─ Two independent groups → Welch t test
│  ├─ Before/after on the same subjects → Paired t test
│  ├─ 3+ independent groups → Welch ANOVA → Games–Howell
│  │  └─ Equal-variance ANOVA selected → Tukey–Kramer
│  ├─ Same subjects in several conditions → Repeated-measures ANOVA / Friedman
│  ├─ Two independent factors → Two-way ANOVA
│  ├─ 3+ factors / numeric covariates → Factorial linear model
│  └─ Groups with covariates to adjust → ANCOVA
├─ Categories / counts
│  ├─ Independent categories → χ² independence
│  │  └─ Sparse 2×2 table → Fisher exact
│  ├─ One proportion vs a target / two independent proportions → Proportion z test
│  ├─ Paired binary outcomes → McNemar
│  └─ Counts vs expected frequencies → χ² goodness of fit
├─ Time until an event, with censoring → Survival analysis
└─ Predict a response from variables → Regression & models

Review shape, outliers and study design:
  Mean analysis → Shapiro–Wilk + Q–Q plot
  Equal-variance assumption → Brown–Forsythe / Levene
  Independent rank comparisons → Mann–Whitney (2), Kruskal–Wallis (3+)
  Symmetric paired differences → Wilcoxon signed-rank
```

### Independent and paired samples at a glance

| Data structure | Parametric comparison | Nonparametric comparison |
| --- | --- | --- |
| Two independent groups | Student / Welch t-test | Mann–Whitney U |
| Two paired groups | Paired t-test | Wilcoxon signed-rank |
| 3+ independent groups | ANOVA / Welch ANOVA | Kruskal–Wallis |
| 3+ repeated conditions | Repeated-measures ANOVA | Friedman test |

Select by the data structure and target quantity. Rank-based location comparisons require appropriate distribution shapes or symmetry. Repeated conditions are measurements of the same subjects.

### Choosing a post-hoc test

```text
Compare differences between groups
├─ Parametric tests
│  ├─ All pairs of groups → Tukey
│  ├─ Each treatment vs a control → Dunnett
│  ├─ Complex mean contrasts → Scheffé
│  └─ Unequal variances → Games–Howell
├─ Nonparametric tests
│  └─ After Kruskal–Wallis → Dunn / Conover
│     ├─ Conservative approach → Dunn + Holm
│     └─ Emphasis on power → Conover + Holm
└─ Repeated-measures data
   └─ After Friedman → Separate paired post-hoc tests
```

Tukey, Dunnett and Scheffé assume equal variances across independent groups. Interpret Conover after a significant Kruskal–Wallis test. Scheffé protects all linear contrasts; this app reports pairwise mean differences. After Friedman, this app provides paired Wilcoxon comparisons with Holm adjustment.

Raw-data mean analyses include summaries, Q–Q plots and distributions. t tests add effect sizes and intervals; ANOVA adds post-hoc comparisons. Paired t tests check differences; ANCOVA and factorial models check residuals.

Group/value layouts can analyze several value columns at once. mean is the group mean, diff is the first group minus the comparison group, and n counts valid observations (pairs for paired data). Significant means p<.05; normality is yes when both groups have Shapiro p≥.05; equal var is yes when Brown–Forsythe p≥.05. Column p values are individual tests; use padjust for a family of hypotheses. Categorical tables report counts, within-group percentages, percentage-point differences and observed/expected counts. Use Fisher exact for sparse 2×2 tables.

### Normal-model methods (parametric)
- One-sample t / t intervals: normal population for exact small-sample inference. Paired t: normally distributed within-pair differences. Inspect Q–Q plots, skewness and outliers.
- Welch t / Welch ANOVA / Games–Howell: independent group means with unequal variances. Student t / classic ANOVA / Tukey: equal variances.
- ANCOVA / factorial linear models: normal independent errors, common residual variance and a full-rank design. ANCOVA uses linear covariate effects and common slopes. Review interactions before main effects; Type II respects marginality and Type III uses sum contrasts.
- Repeated-measures ANOVA: complete within-subject measurements; review sphericity and Greenhouse–Geisser corrected p values.
- Gaussian mixed models: normal conditional errors and random effects. Bayesian mean / two-sample models: normal likelihood with the selected priors.
- Bartlett: normally distributed groups. For uncertain normality, use median-centered Levene / Brown–Forsythe.

### Distribution assumptions by model
- Mean z tests / z intervals: enter known population SDs; the mean sampling distribution is normal or adequately approximated.
- Logistic / multinomial / ordinal: categorical outcomes. Poisson / negative binomial: count outcomes. Check the family, link, dispersion and model diagnostics.
- GEE: cluster mean/variance model and working correlation. Review cluster count, mean specification and robust standard errors.
- GLMM: selected response family and random effects. Bayesian proportion / rate: binomial / Poisson likelihoods.

### Rank, distribution and resampling methods (nonparametric)
- Mann–Whitney / Kruskal–Wallis: independent distributions. Comparable distribution shapes are needed for location interpretations.
- Wilcoxon signed-rank: paired or one-sample differences; symmetry is needed for a location interpretation.
- Friedman: three or more repeated conditions; complete matched rows, ranks within subjects and tie correction.
- Kolmogorov–Smirnov: continuous distributions. Specify one-sample reference parameters independently of the tested sample.
- Kaplan–Meier / log-rank: censored event times. Review independent subjects and censoring; Cox uses proportional hazards.
- IID bootstrap: independent, representative observations. Match paired, clustered or time-dependent sampling to the data structure.

### Categorical tests
- χ²: independent counts and adequate expected frequencies. Fisher exact: independent 2×2 counts. McNemar: paired binary outcomes.

### Choosing a method
Choose the outcome and question first: means, distributions, association, prediction or survival. Then select independent groups, paired observations or clusters. Assess assumptions using Q–Q plots, p values, sample sizes and study design. For skewed or dependent data, review transformations and a model that matches the distribution and sampling structure.

## Data & units
Histogram: enable KDE to show density-normalized bars and a Gaussian density curve. Each series has area 1; KDE needs at least two finite values with variation.

Row filtering: combine column conditions with AND/OR, preview the retained rows, then save under a new dataset name. Names start with a letter and use letters, digits or underscores; blank selects a new D number. Editing data or conditions requires a new preview. The source stays intact.

Wide → Long: choose ID and measurement columns; measurement headers become variable labels. Long → Wide: choose ID, variable and value columns. For duplicate pairs, select first/last/sum/mean; missing combinations become blanks.

Recode: enter old,new mappings (<missing> for blanks) or lower-inclusive, upper-exclusive numeric intervals. Derived variable: use column letters or valid headers in a formula, e.g. weight/(height/100)^2 or if(condition,a,b). Missing or invalid results become blanks. Preview, apply to the draft, then save.

Add group column: enter increasing cut points, group labels and a new header. A cut point of 10 creates <10 and ≥10 groups. Review group counts, add the column, then save; missing/nonnumeric cells yield blank groups.

Scatter: select separate X and Y columns; add a group column for colors and sample-count legends. Regression lines appear on the fitted predictor/response axes.

Bar: List data shows value frequencies; multi-column data uses the first column as labels and numeric columns as heights. A group column separates series. Negative heights extend below zero.

`stats(list)` — Summary statistics; values with fewer than 10 distinct numbers also show counts/percentages. Use stats(list,categorical) for categorical counts, or stats(columns,overall,flags) for all columns (0=numeric, 1=categorical). Binary 0/1 columns are categorical.
Example: stats([1,2,3,4])

`mode(list)` — All values with the highest frequency, returned as a sorted list. Ties include every matching value; if all values occur once, all are returned.
Example: mode([1,1,2,2,3]) → [1,2]
`skewness(list[,correction])` — Adjusted Fisher–Pearson sample skewness by default (correction=1), requiring at least three finite real values with variation. correction=0 uses the uncorrected central-moment coefficient. Positive values indicate a longer/heavier right tail.
Example: skewness([1,2,3,4,5]) → 0
`kurtosis(list[,correction])` — Sample-corrected excess kurtosis by default (correction=1), requiring at least four finite real values with variation. The normal reference is 0. correction=0 uses the uncorrected fourth standardized moment minus 3.
Example: kurtosis([1,2,3,4,5]) → -6/5
Summary statistics also shows mode(s), sample-corrected skewness and sample-corrected excess kurtosis. Undefined shape statistics for constant data or insufficient sample sizes are displayed as NaN.

`mean(list)` — Arithmetic mean.
Example: mean([1,2,3,4])
`median(list)` — Median.
Example: median([3,1,2])
`variance(list)` — Sample variance by default (division by n−1; ddof=1), requiring at least two values. An optional second argument selects ddof=0 or 1.
Example: variance([1,2,3,4])
`variance(list,0)` — Population variance (division by n).
Example: variance([1,2,3],0) → 2/3
`stdev(list)` — Sample standard deviation by default (ddof=1), requiring at least two values. stats(list) shows both population and sample values.
Example: stdev([1,2,3]) → 1
`stdev(list,0)` — Population standard deviation (ddof=0).
Example: stdev([2,4,4,4,5,5,7,9],0) → 2
`quartiles(list)` — Q1, median and Q3 using inclusive interpolation.
Example: quartiles([1,2,3,4,5])
`sumdata(list)` — Sum of the data values.
Example: sumdata([1,2,3,4])
`regression(data,model)` — Fit linear, quadratic, logarithmic, exponential or power regression. Custom form: regression(data,custom,expression,variable[,starts]); other symbols are parameters. Starts: [[parameter,value,lower,upper],...].
Example: regression([[1,2],[2,4],[3,6]],linear)
Example (y = S(b)/S₀): regression([[0,1],[100,0.9],[200,0.81]],custom,exp(-b*ADC),b)
Example (exponential decay): regression([[0,4],[1,2.8],[2,2.1],[3,1.6]],custom,A*exp(-k*x)+C,x)
`covariance(x,y)` — Sample covariance by default (division by n−1; ddof=1), requiring at least two pairs. An optional third argument selects ddof=0 or 1.
Example: covariance([1,2,3],[2,4,6])
`covariance(x,y,0)` — Population covariance (division by n).
Example: covariance([1,2,3],[2,4,6],0) → 4/3
`correlation(x,y)` — Correlation coefficient of two paired lists.
Example: correlation([1,2,3],[2,4,6])
`qty(value,unit)` — Quantity with a unit, for example qty(2,m).
Example: qty(2,m)+qty(30,cm)
`convert(value,from,to)` — Unit conversion, for example convert(2,m,cm).
Example: convert(32,degF,degC)

### Plots and column layout
- Auto columns detects the widest CSV/TSV row, including headers and blanks (1–100 columns).
- Heat map: raw values, row/column z scores or Pearson/Spearman/Kendall correlations; optional hierarchical ordering and dendrograms.
- Violin + points and Raincloud: density, quartiles and raw observations. Box/violin plots support horizontal/vertical orientation and grouping.
- Export plots as SVG or PNG.

## Distributions

`normpdf(x)` — Standard normal density at x.
Example: normpdf(0)
`normpdf(x,μ,σ)` — Normal density with mean μ and standard deviation σ.
Example: normpdf(70,70,10)
`normcdf(x)` — Standard normal cumulative probability P(Z ≤ x).
Example: normcdf(1.96)
`normcdf(low,high)` — P(low < Z < high) for the standard normal; -oo and oo are accepted bounds.
Example: normcdf(-1.96,1.96)
`normcdf(low,high,μ,σ)` — Normal probability for the interval with mean μ and standard deviation σ.
Example: normcdf(-oo,60,70,10)
`invnorm(p)` — Standard normal quantile: the x with P(Z ≤ x) = p.
Example: invnorm(0.975)
`invnorm(p,μ,σ)` — Quantile of the normal distribution with mean μ and standard deviation σ.
Example: invnorm(0.9,70,10)
`tpdf(x,df)` — Student t density.
Example: tpdf(0,10)
`tcdf(x,df)` — P(T ≤ x) for the t distribution with df degrees of freedom.
Example: tcdf(2.228,10)
`tcdf(low,high,df)` — P(low < T < high).
Example: tcdf(-2.228,2.228,10)
`invt(p,df)` — Student t quantile: the x with P(T ≤ x) = p.
Example: invt(0.975,10)
`chi2pdf(x,df)` — χ² density.
Example: chi2pdf(2,2)
`chi2cdf(x,df)` — P(X ≤ x) for the χ² distribution with df degrees of freedom.
Example: chi2cdf(3.8415,1)
`chi2cdf(low,high,df)` — P(low < X < high).
Example: chi2cdf(2,4,3)
`fpdf(x,df1,df2)` — F density with the two degrees of freedom.
Example: fpdf(1,2,4)
`fcdf(x,df1,df2)` — P(F ≤ x).
Example: fcdf(3,2,4)
`fcdf(low,high,df1,df2)` — P(low < F < high).
Example: fcdf(1,3,2,4)
`binompdf(n,p,k)` — Binomial probability P(X = k) for n trials with success probability p.
Example: binompdf(10,1/2,5)
`binompdf(n,p)` — List of the binomial probabilities for k = 0 to n (n ≤ 100).
Example: binompdf(4,1/2)
`binomcdf(n,p,k)` — Binomial cumulative probability P(X ≤ k).
Example: binomcdf(10,1/2,5)
`poissonpdf(μ,k)` — Poisson probability P(X = k) with mean μ.
Example: poissonpdf(2,3)
`poissoncdf(μ,k)` — Poisson cumulative probability P(X ≤ k).
Example: poissoncdf(2,3)
`geometpdf(p,k)` — Geometric probability P(X = k) = (1−p)^(k−1)·p.
Example: geometpdf(1/2,3)
`geometcdf(p,k)` — Geometric cumulative probability P(X ≤ k) = 1 − (1−p)^k.
Example: geometcdf(1/2,3)
`exppdf(x,λ)` — Exponential density with rate λ; λ defaults to 1.
Example: exppdf(1)
`expcdf(x,λ)` — Exponential cumulative probability P(X ≤ x).
Example: expcdf(1)
`unifpdf(x,a,b)` — Uniform density on [a,b]; the default interval is [0,1].
Example: unifpdf(0.5)
`unifcdf(x,a,b)` — Uniform cumulative probability P(X ≤ x).
Example: unifcdf(0.5)
`gammapdf(x,k,θ)` — Gamma density with shape k and scale θ; θ defaults to 1.
Example: gammapdf(1,1)
`gammacdf(x,k,θ)` — Gamma cumulative probability P(X ≤ x).
Example: gammacdf(1,1)
`betapdf(x,α,β)` — Beta density on 0 ≤ x ≤ 1.
Example: betapdf(0.5,2,3)
`betacdf(x,α,β)` — Beta cumulative probability P(X ≤ x).
Example: betacdf(0.5,2,3)
`lognormpdf(x,μ,σ)` — Log-normal density; μ and σ default to 0 and 1.
Example: lognormpdf(1)
`lognormcdf(x,μ,σ)` — Log-normal cumulative probability P(X ≤ x).
Example: lognormcdf(1)

`hgeompdf(N,K,n,k)` — Hypergeometric probability mass. Use integers N ≤ 10000 and 0 ≤ K,n ≤ N.
Example: hgeompdf(10,2,2,2)
`hgeomcdf(N,K,n,k)` — Cumulative probability of at most k successes in draws without replacement.
Example: hgeomcdf(10,2,2,1)
`nbinompdf(r,p,k)` — Mass for k failures before the r-th success. Failures start at 0; total trials = k+r. Use 1 ≤ r ≤ 100000 and 0 < p ≤ 1.
Example: nbinompdf(3,0.5,2)
`nbinomcdf(r,p,k)` — Cumulative probability of at most k failures before the r-th success.
Example: nbinomcdf(3,0.5,2)
`weibullpdf(x,k,λ)` — Weibull density: positive shape k and scale λ (default 1).
Example: weibullpdf(3,2,3)
`weibullcdf(x,k,λ)` — Weibull cumulative probability P(X ≤ x).
Example: weibullcdf(3,2,3)

`cauchypdf(x)` / `cauchypdf(x,x₀,γ)` — Cauchy density, with default location 0 and scale 1. Require finite x₀ and positive finite γ. The mean and variance are undefined.
Example: cauchypdf(0,0,1)
`cauchycdf(x)` / `cauchycdf(x,x₀,γ)` — Cauchy cumulative probability P(X ≤ x).
Example: cauchycdf(1,0,1)
`cauchycdf(low,high)` / `cauchycdf(low,high,x₀,γ)` — Cauchy interval probability. Infinite bounds are allowed.
Example: cauchycdf(-1,1,0,1)
`invcauchy(q)` / `invcauchy(q,x₀,γ)` — Cauchy quantile for 0 ≤ q ≤ 1. Endpoints return −∞ and ∞; q=0.5 returns the location (median).
Example: invcauchy(0.75,0,1)

## Statistical tests

`ttest(μ0,[...])` — One-sample t test of the mean against μ0, using raw observations.
Example: ttest(0,[1,2,3,4])
`ttest(μ0,x̄,s,n)` — One-sample t test from sample mean x̄, sample SD s and size n.
Example: ttest(0,2.5,1.291,4)
`ztest(μ0,σ,[...])` — One-sample mean z test with known population SD σ.
Example: ztest(0,2,[1,2,3,4])
`ztest(μ0,σ,x̄,n)` — Mean z test from known population SD σ, sample mean x̄ and size n.
Example: ztest(0,2,2.5,4)
`chi2test(observed,expected)` — χ² goodness-of-fit test. Enter nonnegative integer observed counts and positive expected counts with the same total.
Example: chi2test([10,20,30],[15,20,25])
`anova([...],[...],...)` — One-way ANOVA for independent group means under normality and equal variances.
Example: anova([1,2,3],[4,5,6])
`ttest2(delta, A, B, student)` — Pooled-variance Student t test of two independent means against difference delta.

`welchanova(A, B, ...)` — Unequal-variance one-way ANOVA with Games–Howell post-hoc comparisons.

`gameshowell(A, B, ...)` — Pairwise comparisons of independent means allowing unequal variances; adjusted p values and simultaneous 95% intervals.

`tukey([...],[...],...)` — Tukey–Kramer post-hoc comparisons under equal variances; adjusted p values and simultaneous 95% intervals.
Example: tukey([1,2,3],[4,5,6],[7,8,9])
`ttest2(Δ0,x,y)` — Welch t test of two independent means against difference Δ0.
Example: ttest2(0,[1,2,3],[2,4,5])
`ttestpaired(Δ0,x,y)` — Paired t test of mean within-pair differences x−y against Δ0.
Example: ttestpaired(0,[1,2,3],[2,3,5])
`ztest2(Δ0,σx,σy,x,y)` — Independent two-mean z test with known population SDs σx and σy.
Example: ztest2(0,1,1,[1,2,3],[2,4,5])
`chi2independence(x,y[,correction])` — χ² association test for two independent categorical columns. For 2×2 tables, Yates correction defaults to 1; use 0 for Pearson χ².
Example: chi2independence([1,1,2,2],[1,2,1,2])
`fisherexact(x,y)` — Fisher exact association test for two binary category columns; suitable for sparse 2×2 tables.
Example: fisherexact([1,1,1,1,1,1,2,2],[1,1,1,2,2,2,1,2])
`shapiro(list)` — Shapiro–Wilk normality test for 3–5000 observations; interpret with the Q–Q plot.
Example: shapiro([1,2,3,4,5])
`tinterval(level,[...])` — Mean confidence interval using sample SD and Student t. Enter level as .95 or 95.
Example: tinterval(0.95,[1,2,3,4])
`tinterval(level,x̄,s,n)` — Mean t interval from sample mean x̄, sample SD s and size n.
Example: tinterval(95,2.5,1.291,4)
`zinterval(level,σ,[...])` — Mean confidence interval with known population SD σ.
Example: zinterval(0.95,2,[1,2,3,4])
`zinterval(level,σ,x̄,n)` — Mean z interval from known population SD σ, sample mean x̄ and size n.
Example: zinterval(95,2,2.5,4)
- One-sample tests return two-tailed p values by default; append left or right for a one-sided test.

## Finance

`tvmfv(n,i,pv,pmt)` — Future value after n periods with the rate i per period.
Example: tvmfv(12,0.05/12,-1000,-100)
`tvmpv(n,i,pmt,fv)` — Present value of n payments and a final value.
Example: tvmpv(10,0.05,100,0)
`tvmpmt(n,i,pv,fv)` — Payment per period that clears pv against fv.
Example: tvmpmt(360,0.05/12,250000,0)
`tvmn(i,pv,pmt,fv)` — Number of periods.
Example: tvmn(0.05,0,100,-1000)
`tvmrate(n,pv,pmt,fv)` — Interest rate per period, found numerically.
Example: tvmrate(10,1000,-150,0)
`npv(rate,[...])` — Net present value of a cash-flow list; the first flow is at time 0.
Example: npv(0.1,[-1000,300,400,500])
`npv(rate,cf0,[...])` — The same with the initial flow given separately.
Example: npv(0.1,-1000,[300,400,500])
`irr([...])` — Internal rate of return that makes the net present value zero.
Example: irr([-1000,300,400,500])
`irr(cf0,[...])` — The same with the initial flow given separately.
Example: irr(-1000,[500,500,500])
`amort(i,pv,n)` — Payment and totals of a fully amortized loan; add k to stop after k payments.
Example: amort(0.005,200000,360)
`cagr(start,end,n)` — Compound annual growth rate from a starting value to an ending value over n periods.
Example: cagr(1000,2000,5)
- TVM values follow the cash-flow convention: money received is positive and money paid is negative. Add begin as the last argument for payments at the beginning of each period; the default is end. Rates are per payment period.

## Distribution functions matching Probability mode

Discrete CDFs include integer masses up to the real threshold; discrete PDFs return 0 for nonintegers.

**Normal parameter solver** finds μ or σ from P(X≤x)=q or P(X≥x)=q and the other parameter. Enter 0<q<1 and σ>0; solving for σ requires q≠0.5.

## Regression and rank tests

Columns end with the response by default; select another response column in Statistics. Numeric coefficients use the original units. Evaluate prediction with cross-validation or validation data.

`regression(data,polynomial,degree)` — Polynomial least squares, degrees 1–10.
Example: regression([[0,1],[1,3],[2,9],[3,25],[4,57]],polynomial,3)
`regression(data,multiple)` — Multiple regression with an intercept and up to eight predictors; last column is the response.
Example: regression([[0,0,1],[1,0,3],[0,1,4],[1,1,7],[2,1,8]],multiple)
`regression(data,logistic)` — Binary 0/1 logistic regression: coefficients, odds ratios, ROC/AUC and diagnostics. Separation automatically uses Firth; add firth to select it directly.
Example: regression([[-3,0],[-2,0],[-1,1],[0,0],[0,1],[1,0],[2,1],[3,1]],logistic)
`wilcoxon(differences)` — Signed-rank test for symmetric one-sample or paired differences; use wilcoxon(A,B) for pairs. Add left/right for a one-sided test.
Example: wilcoxon([1,2,3,4,5])
`mannwhitney(x,y)` — Rank comparison of two independent distributions. A location interpretation requires similar shapes. Add left/right for a one-sided test.
Example: mannwhitney([1,2,3],[4,5,6])
`kruskal(group1,group2,...)` — Rank comparison of independent group distributions; tie-corrected H and approximate χ² p value.
Example: kruskal([1,2,3,4,5],[4,5,6,7,8],[7,8,9,10,11])

### Bayesian regression

`regression(data,bayeslinear,[priorSD,level,shape,scale])` — Normal-inverse-gamma prior, Student-t posterior and predictive intervals. Defaults: [2.5,0.95,2,1].
`regression(data,bayeslogistic,[priorSD,level])` — Normal coefficient prior and Laplace posterior approximation for 0/1 responses. Defaults: [2.5,0.95]. Reports credible intervals, P(beta>0), odds ratios and ROC/AUC.

NUTS: append sampler options to the prior, e.g. [2.5,0.95,2,1,[nuts,500,500,8,0,2]] for linear or [2.5,0.95,[nuts,500,500,8,0,2]] for logistic. Order: draws, warmup, tree depth, seed, chains. Review R-hat, ESS, MCSE and divergences.

### Regularized regression

`regression(data,ridge,alpha)` — L2 penalty; default alpha=.1. Predictors are standardized and coefficients reported in original units.
`regression(data,lasso,alpha)` — L1 penalty for coefficient shrinkage and variable selection.
Example: regression([[0,1],[1,3],[2,5],[3,7]],lasso,0.1)
`regression(data,elasticnet,[alpha,l1_ratio])` — Combined L1/L2 penalty; default ratio=.5. Binary versions: logisticridge, logisticlasso, logisticelasticnet. cv selects alpha by five-fold validation.
Example: regression([[-2,0],[-1,0],[1,1],[2,1]],logisticelasticnet,[0.1,0.5])

### SVM

`regression(data,svm,[kernel,C,gamma,epsilon])` — Auto selects SVC for 0/1 responses, SVR otherwise. Defaults: [rbf,1,auto,0.1]. Kernel: linear/rbf; C>0, gamma>0 or auto, epsilon≥0 in response units. Predictors are standardized.
`regression(data,svc,[kernel,C,gamma,epsilon])` — Binary classification; decision score ≥0 predicts class 1. Reports training ROC/AUC, confusion matrix and stratified CV accuracy. Decision plots mark support vectors and margins.
Example: regression([[-2,0],[-1,0],[1,1],[2,1]],svc,[linear,1,auto,0.1])
`regression(data,svr,[kernel,C,gamma,epsilon])` — Regression with training and five-fold CV R²/RMSE/MAE, prediction errors and an epsilon-tube plot for one predictor.
Example: regression([[-2,4],[-1,1],[0,0],[1,1],[2,4]],svr,[rbf,10,auto,0.1])

### Random forest

`regression(data,randomforest,[trees,max_depth,seed])` — Auto selects classification for 0/1 responses, regression otherwise. Defaults: [100,10,0]; trees 1–200, depth 1–20. Reports training/OOB performance and variable importance.
Example: regression([[0,0],[1,1],[2,4],[3,9],[4,16]],randomforest,[100,10,0])
`regression(data,randomforestclassifier,[trees,depth,seed])` — Binary classification; probability ≥.5 predicts class 1. Reports ROC/AUC and confusion matrices. Use randomforestregressor to force regression.
Example: regression([[-3,0],[-2,0],[-1,0],[1,1],[2,1],[3,1]],randomforestclassifier,[100,10,0])

Python: `calc.regression_report(data,"linear")` returns a report dictionary for these models. CSV and copied reports include all observations; expand residual diagnostics to inspect outliers, leverage and Cook’s distance.

## Advanced statistics

Analyze current data, examples or an expression. Use complete subject data for paired and repeated measurements.

### Correlation

`pearson` — Pearson linear correlation r and p value. Enter at least three variable numeric pairs; alternative: both / left / right.
Example: pearson([1,2,3,4,5],[2,1,3,4,5],both)

`spearman` — Spearman rank correlation and p value for paired observations. Ties use average ranks; alternative: both / left / right.
Example: spearman([1,2,2,4,5],[2,1,3,4,5],both)

`kendall` — Kendall tau-b rank correlation and p value for paired observations, with tie correction. Alternative: both / left / right.
Example: kendall([1,2,2,4,5],[2,1,3,4,5],both)

### Data preparation

`impute` — Fill missing numeric values (NA) by mean, median, mode, regression or knn. The default neighbor count is 5; preview before applying.
Example: impute([[1,NA],[2,4],[NA,6],[4,8]],mean)

### Categorical data

`propztest` — Compare a success proportion with p0. Input: 0/1 values or success/trial counts; alternative: both / left / right. Uses a normal approximation.
Example: propztest(0.5,[[60,100]])

`propztest2` — Compare two independent success proportions. Input: two 0/1 lists or success/trial counts for A and B. Alternatives refer to A−B.
Example: propztest2(60,100,45,100)

`mcnemar` — Compare paired binary outcomes from a 2×2 count table. Method: exact / corrected / asymptotic.
Example: mcnemar([[20,8],[2,15]],exact)

### Reliability & agreement

`cronbach` — Internal consistency using raw and standardized Cronbach α, item-total correlations and α after item deletion. Rows: subjects; columns: items. Reverse-code items first.
Example: cronbach([[1.987,2.255,1.895,1.448,2.702,2.043],[3.103,3.653,2.588,3.608,3.265,3.866],[5.16,4.181,6.042,4.848,4.128,5.317],[1.995,2.767,1.417,-0.304,-1.529,-0.2],[1.802,1.7,2.56,2.591,4.452,3.681],[5.242,3.886,4.375,5.082,5.152,4.701],[3.057,2.704,2.315,2.034,0.528,0.659],[4.576,5.304,4.688,5.573,4.66,5.626],[5.08,3.257,4.251,3.415,3.076,4.508],[2.502,2.733,2.919,3.058,3.403,2.427],[4.23,3.357,4.235,4.595,5.16,5.999],[2.86,3.515,2.619,0.955,1.766,0.26],[3.16,2.893,2.37,2.341,1.676,2.201],[1.101,3.477,2.018,2.67,2.235,3.664],[3.503,4.223,4.268,2.178,3.518,1.656],[3.623,3.309,4.28,2.605,3.676,3.647],[4.285,5.139,6.064,4.069,4.097,4.629],[3.301,2.767,3.271,2.832,3.249,3.621],[2.857,2.677,2.348,3.272,2.696,3.272],[0.449,1.323,0.652,3.013,3.114,1.652],[3.447,3.14,2.42,2.311,3.202,2.063],[2.401,2.196,3.998,1.025,2.349,1.691],[3.54,5.121,3.878,2.99,2.849,3.135],[3.67,4.081,4.264,3.472,3.458,4.419]],raw)

`omega` — McDonald ω for a single-factor model. Enter complete rows for at least three variable items; reverse-code first. Reports ω, α, loadings and model fit.
Example: omega([[3.43582,4.49591,2.54665,3.76818],[0.61851,0.78834,0.42096,1.14719],[4.22409,3.35794,5.3267,3.95336],[2.67555,2.82063,3.16122,2.63647],[3.51589,3.74102,2.70456,4.9756],[2.07478,1.79972,2.47725,2.86268],[2.09434,2.88069,3.03493,2.52493],[4.04367,3.86703,3.51913,4.17903],[2.13129,2.31026,1.36417,2.71804],[3.52832,4.2775,2.82035,3.37795],[4.62115,3.40845,3.55532,3.42753],[2.12611,1.59532,0.23784,2.06462],[2.14818,1.86724,2.42271,3.69048],[0.794,1.3783,1.83058,2.46812],[4.18647,3.12699,4.07329,3.60101],[1.94823,2.34854,1.01613,2.73867],[1.27848,0.28949,1.0973,0.94459],[2.0746,1.74297,2.89237,2.50345],[3.69408,2.68011,3.00642,4.30645],[1.82953,2.13442,1.70152,2.59832],[4.21257,3.38311,3.45071,3.53796],[1.64389,3.29193,2.445,2.34095],[3.49262,2.45121,4.40837,3.21754],[2.33436,3.75566,3.59283,3.81898],[1.72403,1.6016,2.25337,2.35726],[3.10404,3.53899,3.72024,3.1812],[5.07729,4.17883,4.86563,4.5112],[2.59101,2.69799,3.12035,3.37647],[2.53705,2.94556,1.85212,2.05705],[1.32768,1.17533,2.26744,2.11484],[3.78672,2.84197,2.62053,3.39477],[1.40463,3.31083,2.38463,2.29464],[3.41373,4.03173,2.7824,2.71733],[0.99401,2.58225,2.59379,2.58271],[2.01909,2.50153,2.36557,2.87494],[2.75136,3.49678,4.24712,4.34985],[3.22501,2.65474,1.93046,4.17127],[2.32053,3.50725,3.75916,2.81773],[3.41988,3.73964,2.05347,3.55495],[2.19,2.55877,1.83753,2.52337],[1.7709,3.55151,2.82001,2.93103],[2.60927,3.6987,4.13095,2.83299],[2.37246,1.39507,2.90697,3.8639],[3.36583,3.2387,4.42416,4.63447],[3.30813,3.44148,2.53864,3.14448],[1.56278,1.82084,2.48868,1.21165],[2.89557,1.97945,3.64156,1.49968],[2.96559,3.14118,2.71473,4.26585]],raw)

`icc` — Intraclass correlation from a subject × rater matrix. oneway=ICC(1), random=absolute-agreement ICC(2), mixed=consistency ICC(3); single or average ratings, with confidence intervals.
Example: icc([[9,10,9],[6,7,6],[8,8,9],[5,6,5],[10,9,10],[7,7,8]],random,single,0.95)

`cohenkappa` — Agreement between two raters from a square category-count table. Choose unweighted, linear or quadratic weights; weighted categories follow their specified order.
Example: cohenkappa([[6,1,0],[1,5,1],[0,1,5]],unweighted)

`blandaltman` — Agreement of two measurements per independent subject: bias, limits of agreement and proportional-bias trend. Uses A−B; log mode accepts positive measurements and reports ratios.
Example: blandaltman([[10,10.5],[12,11.8],[8,8.6],[15,14.7],[11,11.3],[9,9.1]],0.95,difference)

### Distribution & variance

`shapiro` — Shapiro–Wilk normality test for 3–5000 observations. Read the p value alongside the Q–Q plot.
Example: shapiro([1,2,3,4,5])

`kstest` — Compare continuous distributions: two sample lists, or data with normal(mean,SD) / uniform(lower,width). Specify reference parameters independently of the sample.
Example: kstest([1,2,4,5],[2,3,5,8])

`levene` — Compare group variances using median-centered Brown–Forsythe. Input: one list per independent group.
Example: levene([1,2,4,5],[2,3,5,8])

`bartlett` — Compare variances of normally distributed independent groups. Input: one list per group.
Example: bartlett([1,2,4,5],[2,3,5,8])

### Post-hoc comparisons

`tukey` — Tukey–Kramer comparisons of all independent group means under equal variances, with adjusted p values and simultaneous 95% intervals.
Example: tukey([1,2,4,5],[2,3,5,8])

`gameshowell` — Compare all independent group means allowing unequal variances, with adjusted p values and simultaneous 95% intervals.
Example: gameshowell([1,2,4,5],[2,3,5,8])

`scheffe` — Pairwise mean comparisons with Scheffé protection for all linear contrasts. Input: independent group lists; assumes normality and equal variances.
Example: scheffe([[1,2,4,5],[2,3,5,8],[4,6,7,9]])

`dunnett` — Compare each treatment mean with a control under normality and equal variances. Input: group lists and control number (1-based, default 1). Difference: treatment−control.
Example: dunnett([[1,2,4,5],[2,3,5,8],[4,6,7,9]],1)

`dunn` — Pairwise rank comparisons after Kruskal–Wallis. Input: independent group lists; adjustment: holm (default) / bonferroni / fdr / none.
Example: dunn([[1,2,4],[2,3,6],[3,5,8],[4,7,9]],holm)

`conover` — Pairwise rank comparisons after a significant Kruskal–Wallis test. Input: independent group lists; adjustment: holm (default) / bonferroni / fdr / none.
Example: conover([[1,2,4,5],[2,3,5,8],[4,6,7,9]],holm)

### Group comparisons

`twowayanova` — Test two categorical factors and their interaction in independent numeric observations. Type III tests; interaction 1 (default) or additive model 0.
Example: twowayanova([[1,1,2],[1,1,4],[1,2,5],[1,2,6],[2,1,4],[2,1,5],[2,2,8],[2,2,10]],1)

`ancova` — Compare covariate-adjusted group means. Columns: group, covariates, response. Confidence level defaults to .95; slope-homogeneity check defaults to 1.
Example: ancova([[1,1,3],[1,2,5],[1,3,4],[1,4,8],[2,2,6],[2,3,7],[2,4,9],[2,5,8],[3,1,5],[3,3,8],[3,4,10],[3,6,11]],0.95,1)

`manova` — Compare several responses jointly. Input: group then response columns; factorial mode adds factors, repeated mode uses subject rows with equal response blocks per time point. Reports Pillai, Wilks, Hotelling–Lawley and Roy.
Example: manova([[1,1.987,1.448],[1,3.103,3.608],[1,5.16,4.848],[1,1.995,-0.304],[1,1.802,2.591],[1,5.242,5.082],[1,3.057,2.034],[1,4.576,5.573],[2,5.08,3.415],[2,2.502,3.058],[2,4.23,4.595],[2,2.86,0.955],[2,3.16,2.341],[2,1.101,2.67],[2,3.503,2.178],[2,3.623,2.605],[3,4.285,4.069],[3,3.301,2.832],[3,2.857,3.272],[3,0.449,3.013],[3,3.447,2.311],[3,2.401,1.025],[3,3.54,2.99],[3,3.67,3.472]])

`repeatedanova` — Compare repeated conditions in complete subject rows. Rows: subjects; columns: conditions. Supports one or two factors, sphericity corrections and paired post-hoc comparisons with Holm-adjusted p values.
Example: repeatedanova([[2,4,5],[3,4,7],[4,7,8],[2,3,6],[5,6,7]],1)

`friedman` — Rank comparison of three or more repeated conditions in complete subject rows. Uses a tie-corrected χ² approximation and reports Kendall W.
Example: friedman([[2,4,5],[3,4,7],[4,7,8],[2,3,6],[5,6,7]])

### Effect Size

`cohend` — Standardized mean difference between two samples. independent uses pooled SD; paired uses the SD of within-pair differences.
Example: cohend([1,2,4,5],[2,3,5,8],independent)

`eta2` — Proportion of total variation associated with group differences. Input: one list per independent group.
Example: eta2([1,2,4,5],[2,3,5,8])

`cramerv` — Strength of categorical association from a count table. Reports Cramér’s V and, for 2×2 tables, signed phi.
Example: cramerv([[20,5],[7,18]])

`phi` — Signed association for a 2×2 count table. Reversing one variable’s category order reverses the sign.
Example: phi([[20,5],[7,18]])

### Multiple testing

`padjust` — Adjust a family of p values for multiple testing. Method: bonferroni / holm / fdr (BH) / by; choose a significance level.
Example: padjust([0.01,0.04,0.03,0.2],holm,0.05)

### Confidence intervals

`tinterval` — Mean confidence interval using sample SD and Student t. Input: level and observations, or level, mean, SD and n.
Example: tinterval(95,[1,2,3,4,5])

`zinterval` — Mean confidence interval using known population SD. Input: level, population SD and observations, or level, population SD, mean and n.
Example: zinterval(95,2,[1,2,3,4,5])

### Equivalence tests (TOST)

`tost` — Test whether mean−target is within prespecified equivalence bounds in the original units. Input: data, lower, upper, target (default 0), alpha (default .05). Both one-sided p values must be below alpha.
Example: tost([9.8,10.1,10.2,9.9,10,10.1,9.9,10.2],-0.5,0.5,10,0.05)

`tost2` — Equivalence of two independent means, A−B. Input: A, B, bounds in original units, welch / student, alpha (default .05). Both one-sided p values must be below alpha.
Example: tost2([9.8,10.1,10.2,9.9,10,10.1,9.9,10.2],[10,10.2,10.1,9.8,10.1,10,9.9,10.1],-0.5,0.5,welch,0.05)

`tostpaired` — Equivalence of paired mean differences, A−B. Input: complete pairs, bounds in original units and alpha (default .05). Both one-sided p values must be below alpha.
Example: tostpaired([9.8,10.1,10.2,9.9,10,10.1,9.9,10.2],[10,10.2,10.1,9.8,10.1,10,9.9,10.1],-0.5,0.5,0.05)

### Robust statistics

`yuen` — Compare two independent trimmed means, A−B. Set trimming per tail (default .20) and confidence level; each group needs at least two retained values and positive Winsorized variance.
Example: yuen([1,2,2,3,4,5,6,7,8,25],[2,3,4,4,5,6,7,8,9,12],0.2,0.95)

`trimmedanova` — Welch-type comparison of independent group trimmed means. Set trimming per tail in [0,.5), default .20.
Example: trimmedanova([[1,2,2,3,4,5,6,7,8,25],[2,3,4,4,5,6,7,8,9,12],[4,5,6,6,7,8,9,10,11,15]],0.2,0.95)

`winsorcor` — Robust correlation of complete paired observations after Winsorizing each variable. Reports an approximate t-test p value.
Example: winsorcor([1,2,3,4,5,6,7,8,9,30],[2,1,4,3,6,5,8,7,9,12],0.2)

### Generalized regression

`linearmodel` — OLS with numeric and categorical predictors. Specify categorical predictor positions (1-based), interaction order, Type II/III tests and sum/treatment coding.
Example: linearmodel([[1,1,2],[1,1,4],[1,2,5],[1,2,6],[2,1,4],[2,1,5],[2,2,8],[2,2,10]],[1,2],2,3,sum)

`glm` — Generalized linear model. Columns: predictors, response. Family: gaussian / binomial (0/1) / poisson / gamma / inversegaussian / nbinom. Choose a link; NB2 alpha is fixed or estimate. Optional offset/exposure.
Example: glm([[0,2],[1,4],[2,4],[3,7],[4,8],[5,9]],gaussian,auto,1)

`poissonreg` — Poisson count regression with a log link. Columns: predictors, count response. Optional row-wise offset or positive exposure.
Example: poissonreg([[0,1],[0,0],[1,3],[1,1],[2,2],[2,5],[3,4],[3,8],[4,6],[4,10]])

`nbreg` — NB2 count regression with estimated overdispersion. Columns: predictors, count response. Optional offset or positive exposure.
Example: nbreg([[0,0],[0,0],[0,1],[0,8],[1,0],[1,1],[1,3],[1,15],[2,0],[2,2],[2,5],[2,23],[3,1],[3,3],[3,10],[3,35]])

`zeroinflated` — Model counts with extra zeros using Poisson or NB2 and a logit zero component. Columns: predictors, count response; zero component: intercept or the same predictors.
Example: zeroinflated([[0,0],[0,0],[0,0],[0,1],[0,2],[0,3],[1,0],[1,0],[1,1],[1,2],[1,3],[1,5],[2,0],[2,0],[2,1],[2,3],[2,5],[2,8],[3,0],[3,0],[3,2],[3,4],[3,7],[3,10]],poisson,intercept)

`tobit` — Normal censored regression. Columns: predictors, observed response; lower bound defaults to 0, upper to none. Coefficients describe the latent response.
Example: tobit([[0,0],[1,0],[2,1],[3,3],[4,3],[5,6],[6,5],[7,8],[8,9],[9,8],[10,11],[11,12]],0,none)

`quantreg` — Predict a response quantile. Columns: predictors, response; choose a quantile strictly between 0 and 1.
Example: quantreg([[0,2],[1,4],[2,3],[3,8],[4,7],[5,9],[6,10],[7,12],[8,11],[9,15],[10,17],[11,16]],0.5)

`robustreg` — Huber regression reduces the influence of response outliers. Columns: numeric predictors, response. Tuning defaults to 1.345; inspect high-leverage observations.
Example: robustreg([[0,1],[1,2.5],[2,5],[3,6.5],[4,9],[5,10.5],[6,13],[7,14.5],[8,17],[9,35],[10,21],[11,22.5]],1.345)

`multinomial` — Predict unordered numeric categories. Columns: predictors, category response; the smallest category is the reference.
Example: multinomial([[-2,0],[-2,1],[-1,0],[-1,2],[0,0],[0,1],[0,2],[1,1],[1,2],[2,1],[2,2],[2,0]])

`ordinal` — Proportional-odds regression for ordered numeric categories. Columns: predictors, response; category order follows numeric order.
Example: ordinal([[-2,0],[-2,1],[-1,0],[-1,2],[0,0],[0,1],[0,2],[1,1],[1,2],[2,1],[2,2],[2,0]])

### Mediation & moderation

`mediation` — Direct, indirect and total effects for one continuous mediator. Columns: X, M, optional covariates, Y. Reports bootstrap intervals and a Sobel approximation.
Example: mediation([[-2.191,-1.014,-0.857],[-0.662,0.471,0.662],[1.567,1.183,3.061],[2.013,1.591,3.248],[-1.857,-0.593,-0.9],[-0.348,1.302,0.7],[2.702,1.566,3.688],[-0.934,-0.125,-1.06],[-1.674,-0.681,-1.092],[-0.145,-0.168,1.046],[0.818,0.995,2.032],[0.809,1.054,1.548],[1.027,-0.185,-0.448],[-0.783,-0.785,0.117],[-1.612,-1.911,-1.425],[0.26,0.246,-0.084],[1.802,2.034,2.866],[-0.316,-0.156,0.409],[-0.667,-1.464,-1.077],[-0.268,-0.145,-0.343],[0.58,1.473,1.633],[2.444,1.513,2.462],[0.308,0.001,0.363],[1.209,0.904,0.926]],2000,0)

`moderation` — Test X×W interaction and conditional slopes at mean W ± SD. Columns: X, continuous W, optional covariates, Y; X and W are centered.
Example: moderation([[-2.191,-1.014,-0.857],[-0.662,0.471,0.662],[1.567,1.183,3.061],[2.013,1.591,3.248],[-1.857,-0.593,-0.9],[-0.348,1.302,0.7],[2.702,1.566,3.688],[-0.934,-0.125,-1.06],[-1.674,-0.681,-1.092],[-0.145,-0.168,1.046],[0.818,0.995,2.032],[0.809,1.054,1.548],[1.027,-0.185,-0.448],[-0.783,-0.785,0.117],[-1.612,-1.911,-1.425],[0.26,0.246,-0.084],[1.802,2.034,2.866],[-0.316,-0.156,0.409],[-0.667,-1.464,-1.077],[-0.268,-0.145,-0.343],[0.58,1.473,1.633],[2.444,1.513,2.462],[0.308,0.001,0.363],[1.209,0.904,0.926]])

### Repeated & clustered data

`mixedmodel` — Gaussian mixed model for repeated or clustered responses. Columns: subject ID, predictors, response. Random intercept plus up to three slopes; REML (default) / ML. Interval: Wald, profile or bootstrap.
Example: mixedmodel([[1,0,2],[1,1,4],[1,2,4],[2,0,3],[2,1,4],[2,2,6],[3,0,1],[3,1,3],[3,2,4],[4,0,4],[4,1,5],[4,2,8]],0,reml)

`glmm` — Mixed model for binomial or Poisson/NB2 counts. Columns: subject ID, predictors, response. Random intercept; one correlated random slope uses Laplace. Optional offset/exposure.
Example: glmm([[1,0,0],[1,1,0],[1,2,1],[2,0,0],[2,1,1],[2,2,1],[3,0,0],[3,1,0],[3,2,0],[4,0,1],[4,1,1],[4,2,1],[5,0,1],[5,1,0],[5,2,1],[6,0,0],[6,1,1],[6,2,0]],binomial,15)

`gee` — Population-average effects for clustered gaussian/binomial/poisson responses. Columns: cluster ID, predictors, response. Correlation: independence / exchangeable / ar1; small enables a small-cluster correction.
Example: gee([[1,0,2],[1,1,4],[1,2,4],[2,0,3],[2,1,4],[2,2,6],[3,0,1],[3,1,3],[3,2,4],[4,0,4],[4,1,5],[4,2,8]],gaussian,independence)

### Model validation

`crossvalidate` — Evaluate held-out predictions. Columns: predictors, response. Set folds and seed; split: random / blocked / stratified; model: linear / ridge / lasso / elasticnet / logistic.
Example: crossvalidate([[0,1],[1,3],[2,4],[3,7],[4,8],[5,11],[6,12],[7,15],[8,16]],3,0)

`modelcompare` — Compare baseline and expanded models on the same observations. Choose family, existing and added predictors; review fit tests and paired validation performance. CFA/SEM compares measurement/path additions.
Example: modelcompare([[0.0,0.0,2.0],[0.1,0.3333333333333333,3.691664810452469],[0.2,0.6666666666666666,3.144458897973169],[0.3,1.0,3.174185317672267],[0.4,1.3333333333333333,5.294113351138608],[0.5,1.6666666666666667,6.298487112623491],[0.6,2.0,5.500125312406458],[0.7,0.0,2.7818628877629665],[0.8,0.3333333333333333,4.959161814856495],[0.9,0.6666666666666666,5.196740573130613],[1.0,1.0,4.5386025081204435],[1.1,1.3333333333333333,6.0510009741858015],[1.2,1.6666666666666667,7.899792900142669],[1.3,2.0,7.491363404575924],[1.4,0.0,3.8282015542561365],[1.5,0.3333333333333333,5.859058354022168],[1.6,0.6666666666666666,7.079273061650724],[1.7,1.0,6.314362660025703],[1.8,1.3333333333333333,6.871639232168404],[1.9,1.6666666666666667,9.07332788956622],[2.0,2.0,9.529082686120024],[2.1,0.0,5.290333328166475],[2.2,0.3333333333333333,6.605328398499743],[2.3,0.6666666666666666,8.585600298790633],[2.4,1.0,8.340693257349866],[2.5,1.3333333333333333,8.003913496880406],[2.6,1.6666666666666667,9.915987266188216],[2.7,2.0,11.340428962947007],[2.8,0.0,7.141674545508234],[2.9,0.3333333333333333,7.477676459866509],[3.0,0.6666666666666666,9.670229175843374],[3.1,1.0,10.3496128616862],[3.2,1.3333333333333333,9.562372742852972],[3.3,1.6666666666666667,10.666234459024317],[3.4,2.0,12.749403860686702],[3.5,0.0,9.18911462035089],[3.6,0.3333333333333333,8.701863384067297],[3.7,0.6666666666666666,10.468094194684499],[3.8,1.0,12.080589491775534],[3.9,1.3333333333333333,11.479218690956856],[4.0,1.6666666666666667,11.60207231931071],[4.1,2.0,13.75216738490788],[4.2,0.0,11.155640225739422],[4.3,0.3333333333333333,10.353112449582623],[4.4,0.6666666666666666,11.236824471718883],[4.5,1.0,13.392011682699371],[4.6,1.3333333333333333,13.53331393995491],[4.7,1.6666666666666667,12.922096985230352]],1,linear,crossvalidation,5,0.95,100,0,[[excludedrows,0]],0)

`logisticcompare` — Compare added predictors in binary logistic models A and B. Choose saved validation data, stratified holdout or CV; reports fit, AUC, accuracy, log loss and Brier score. Difference: B−A.
Example: logisticcompare([[-2,0,0],[-2,1,0],[-1,0,0],[-1,1,1],[0,0,0],[0,1,1],[1,0,1],[1,1,1],[2,0,1],[2,1,1],[-1,1,0],[1,0,0],[0,1,0],[0,0,1],[2,0,0],[-2,1,1],[-2,0,0],[-2,1,0],[-1,0,0],[-1,1,1],[0,0,0],[0,1,1],[1,0,1],[1,1,1],[2,0,1],[2,1,1],[-1,1,0],[1,0,0],[0,1,0],[0,0,1],[2,0,0],[-2,1,1],[-2,0,0],[-2,1,0],[-1,0,0],[-1,1,1],[0,0,0],[0,1,1],[1,0,1],[1,1,1],[2,0,1],[2,1,1],[-1,1,0],[1,0,0],[0,1,0],[0,0,1],[2,0,0],[-2,1,1]],1,crossvalidation,5,0.5,0.95,200,0,[48,0])

### Bayesian inference

`bayesmean` — Bayesian normal mean and next-observation prediction. Input: sample, normal-inverse-gamma prior mu0,kappa0,alpha0,beta0, level and target. Set the prior in your data units.
Example: bayesmean([1,2,3,4,5],0,1,2,1,0.95,0)

`bayescompare` — Compare two independent normal means, B−A. Choose equal/unequal variances, NIG prior, level, draws and seed. Reports posterior difference, credible interval and Bayes factors; set priors in data units.
Example: bayescompare([10,11,9,10,12],[13,14,12,15,13],equal,0,0.01,2,1,0.95,20000,0)

`bayesttest` — Bayesian one-sample, paired or equal-variance independent t test. Cauchy prior on standardized effect; reports Bayes factors and posterior effect intervals. Direction: A−B or A−target.
Example: bayesttest([10,11,9,10,12],[13,14,12,15,13],independent,0,0.7071067811865476,0.95,10000,0,1)

`bayesanova` — Bayesian comparison of independent normal group means with a common residual variance and a g prior. Reports Bayes factors and posterior group effects.
Example: bayesanova([[1,2,2,3,4,5,6,7,8,25],[2,3,4,4,5,6,7,8,9,12],[4,5,6,6,7,8,9,10,11,15]],0.5,0.95,10000,0,1)

`bayesproportion` — Estimate a success proportion with a Beta prior (default 1,1). Input: 0/1 values or success/trial rows; reports a credible interval, P(p>p0) and BF10.
Example: bayesproportion([1,1,0,1,0,1,1,1,0,1],1,1,0.95,0.5)

`bayesrate` — Estimate a Poisson rate with a Gamma shape/rate prior (default 1,1). Input: counts or count/exposure rows. Rate is the inverse scale; reports rate intervals and count prediction.
Example: bayesrate([0,2,1,3,2],1,1,0.95,1)

### Resampling

`bootstrapci` — IID percentile-bootstrap interval for mean / median / stdev. Set confidence level, resamples and seed.
Example: bootstrapci([1,2,3,4,5,8],mean,0.95,2000,0)

`bayesbootstrap` — Bayesian bootstrap with Dirichlet weights for mean/median/variance/stdev. Analyze one sample or statistic(B)−statistic(A); choose independent/paired, level, draws and seed.
Example: bayesbootstrap([1,2,3,4,5,8],mean,0.95,10000,0)

### Research synthesis

`metaanalysis` — Pool independent study effects. Input: effect and SE, binary arm events/totals for OR/RR, or arm mean/SD/n for MD/Hedges g. Choose fixed / dl / pm and z / hksj inference; reports forest plot and heterogeneity.
Example: metaanalysis([[0.2,0.1],[0.45,0.15],[-0.1,0.12],[0.6,0.2],[0.3,0.11]],pm,0.95,z,1)

`metaregression` — Relate independent study effects to numeric study moderators. Rows: effect, positive SE, moderators. Use log effects and SEs for ratios; reports moderator tests and residual heterogeneity.
Example: metaregression([[0.1,0.12,2012],[0.25,0.15,2014],[0.18,0.11,2016],[0.5,0.18,2018],[0.4,0.13,2020],[0.7,0.2,2022],[0.55,0.16,2024],[0.31,0.14,2019]],pm,0.95,hksj)

`metasubgroup` — Compare study subgroups using a common residual heterogeneity. Rows: effect, SE, group; at least two studies per group. Reports pooled subgroup effects and a joint between-group test.
Example: metasubgroup([[0.1,0.12,1],[0.25,0.15,1],[0.18,0.11,1],[0.5,0.18,2],[0.4,0.13,2],[0.7,0.2,2],[0.55,0.16,2],[0.31,0.14,1]],pm,0.95,hksj)

### Measurement & structural models

`efa` — Explore factors in numeric items. Extraction: pa / ml / pca; enter a factor count or parallel. Rotation: oblimin / varimax / promax. Reports loadings, communalities and factor correlations.
Example: efa([[1.987,2.255,1.895,1.448,2.702,2.043],[3.103,3.653,2.588,3.608,3.265,3.866],[5.16,4.181,6.042,4.848,4.128,5.317],[1.995,2.767,1.417,-0.304,-1.529,-0.2],[1.802,1.7,2.56,2.591,4.452,3.681],[5.242,3.886,4.375,5.082,5.152,4.701],[3.057,2.704,2.315,2.034,0.528,0.659],[4.576,5.304,4.688,5.573,4.66,5.626],[5.08,3.257,4.251,3.415,3.076,4.508],[2.502,2.733,2.919,3.058,3.403,2.427],[4.23,3.357,4.235,4.595,5.16,5.999],[2.86,3.515,2.619,0.955,1.766,0.26],[3.16,2.893,2.37,2.341,1.676,2.201],[1.101,3.477,2.018,2.67,2.235,3.664],[3.503,4.223,4.268,2.178,3.518,1.656],[3.623,3.309,4.28,2.605,3.676,3.647],[4.285,5.139,6.064,4.069,4.097,4.629],[3.301,2.767,3.271,2.832,3.249,3.621],[2.857,2.677,2.348,3.272,2.696,3.272],[0.449,1.323,0.652,3.013,3.114,1.652],[3.447,3.14,2.42,2.311,3.202,2.063],[2.401,2.196,3.998,1.025,2.349,1.691],[3.54,5.121,3.878,2.99,2.849,3.135],[3.67,4.081,4.264,3.472,3.458,4.419],[3.341,3.341,2.722,2.088,2.846,3.371],[2.491,2.816,1.44,1.192,2.551,1.975],[3.002,2.66,3.754,3.345,5.413,3.962],[2.893,3.409,3.316,3.336,3.614,4.426],[1.843,1.939,2.024,5.012,4.963,5.395],[4.404,3.051,4.195,4.157,2.983,3.546],[3.252,2.804,3.346,2.695,4.096,3.254],[3.384,3.477,4.064,1.625,1.051,0.949],[3.04,2.869,2.962,2.556,1.997,0.53],[2.398,2.777,2.227,3.809,3.915,4.636],[3.253,3.538,4.357,3.697,3.035,3.881],[2.896,2.958,0.826,0.678,1.802,0.825],[1.423,1.154,1.884,3.063,3.992,3.001],[3.389,3.692,2.134,3.7,4.094,4.75],[2.75,3.546,3.742,3.853,3.204,5.14],[3.966,2.911,2.755,2.152,3.222,1.657],[2.267,1.875,2.087,1.343,3.21,3.064],[4.436,4.095,5.016,4.363,3.93,4.141],[-0.224,1.681,0.508,1.922,1.822,2.534],[2.844,2.896,3.813,4.436,2.472,3.68],[2.548,3.279,1.79,2.175,1.88,1.092],[2.624,2.491,2.819,3.493,3.617,2.98],[3.027,3.869,2.073,2.693,2.873,3.391],[2.524,3.183,1.987,3.333,2.888,3.225]],2,oblimin,pa,0,0,0.95)

`cfa` — Fit a specified measurement model. Select indicator factors and cross-loadings; ML for continuous data, WLSMV for ordered categories. ML supports FIML. Includes group invariance, standardized loadings, fit indices and a path diagram.
Example: cfa([[1.987,2.255,1.895,1.448,2.702,2.043],[3.103,3.653,2.588,3.608,3.265,3.866],[5.16,4.181,6.042,4.848,4.128,5.317],[1.995,2.767,1.417,-0.304,-1.529,-0.2],[1.802,1.7,2.56,2.591,4.452,3.681],[5.242,3.886,4.375,5.082,5.152,4.701],[3.057,2.704,2.315,2.034,0.528,0.659],[4.576,5.304,4.688,5.573,4.66,5.626],[5.08,3.257,4.251,3.415,3.076,4.508],[2.502,2.733,2.919,3.058,3.403,2.427],[4.23,3.357,4.235,4.595,5.16,5.999],[2.86,3.515,2.619,0.955,1.766,0.26],[3.16,2.893,2.37,2.341,1.676,2.201],[1.101,3.477,2.018,2.67,2.235,3.664],[3.503,4.223,4.268,2.178,3.518,1.656],[3.623,3.309,4.28,2.605,3.676,3.647],[4.285,5.139,6.064,4.069,4.097,4.629],[3.301,2.767,3.271,2.832,3.249,3.621],[2.857,2.677,2.348,3.272,2.696,3.272],[0.449,1.323,0.652,3.013,3.114,1.652],[3.447,3.14,2.42,2.311,3.202,2.063],[2.401,2.196,3.998,1.025,2.349,1.691],[3.54,5.121,3.878,2.99,2.849,3.135],[3.67,4.081,4.264,3.472,3.458,4.419],[3.341,3.341,2.722,2.088,2.846,3.371],[2.491,2.816,1.44,1.192,2.551,1.975],[3.002,2.66,3.754,3.345,5.413,3.962],[2.893,3.409,3.316,3.336,3.614,4.426],[1.843,1.939,2.024,5.012,4.963,5.395],[4.404,3.051,4.195,4.157,2.983,3.546],[3.252,2.804,3.346,2.695,4.096,3.254],[3.384,3.477,4.064,1.625,1.051,0.949],[3.04,2.869,2.962,2.556,1.997,0.53],[2.398,2.777,2.227,3.809,3.915,4.636],[3.253,3.538,4.357,3.697,3.035,3.881],[2.896,2.958,0.826,0.678,1.802,0.825],[1.423,1.154,1.884,3.063,3.992,3.001],[3.389,3.692,2.134,3.7,4.094,4.75],[2.75,3.546,3.742,3.853,3.204,5.14],[3.966,2.911,2.755,2.152,3.222,1.657],[2.267,1.875,2.087,1.343,3.21,3.064],[4.436,4.095,5.016,4.363,3.93,4.141],[-0.224,1.681,0.508,1.922,1.822,2.534],[2.844,2.896,3.813,4.436,2.472,3.68],[2.548,3.279,1.79,2.175,1.88,1.092],[2.624,2.491,2.819,3.493,3.617,2.98],[3.027,3.869,2.073,2.693,2.873,3.391],[2.524,3.183,1.987,3.333,2.888,3.225]],[1,1,1,2,2,2])

`sem` — Fit a measurement model with acyclic latent paths [from,to]. ML for continuous or WLSMV for ordered indicators. Reports standardized paths, direct/indirect/total effects, fit and diagrams; optional bootstrap intervals.
Example: sem([[1.987,2.255,1.895,1.448,2.702,2.043],[3.103,3.653,2.588,3.608,3.265,3.866],[5.16,4.181,6.042,4.848,4.128,5.317],[1.995,2.767,1.417,-0.304,-1.529,-0.2],[1.802,1.7,2.56,2.591,4.452,3.681],[5.242,3.886,4.375,5.082,5.152,4.701],[3.057,2.704,2.315,2.034,0.528,0.659],[4.576,5.304,4.688,5.573,4.66,5.626],[5.08,3.257,4.251,3.415,3.076,4.508],[2.502,2.733,2.919,3.058,3.403,2.427],[4.23,3.357,4.235,4.595,5.16,5.999],[2.86,3.515,2.619,0.955,1.766,0.26],[3.16,2.893,2.37,2.341,1.676,2.201],[1.101,3.477,2.018,2.67,2.235,3.664],[3.503,4.223,4.268,2.178,3.518,1.656],[3.623,3.309,4.28,2.605,3.676,3.647],[4.285,5.139,6.064,4.069,4.097,4.629],[3.301,2.767,3.271,2.832,3.249,3.621],[2.857,2.677,2.348,3.272,2.696,3.272],[0.449,1.323,0.652,3.013,3.114,1.652],[3.447,3.14,2.42,2.311,3.202,2.063],[2.401,2.196,3.998,1.025,2.349,1.691],[3.54,5.121,3.878,2.99,2.849,3.135],[3.67,4.081,4.264,3.472,3.458,4.419],[3.341,3.341,2.722,2.088,2.846,3.371],[2.491,2.816,1.44,1.192,2.551,1.975],[3.002,2.66,3.754,3.345,5.413,3.962],[2.893,3.409,3.316,3.336,3.614,4.426],[1.843,1.939,2.024,5.012,4.963,5.395],[4.404,3.051,4.195,4.157,2.983,3.546],[3.252,2.804,3.346,2.695,4.096,3.254],[3.384,3.477,4.064,1.625,1.051,0.949],[3.04,2.869,2.962,2.556,1.997,0.53],[2.398,2.777,2.227,3.809,3.915,4.636],[3.253,3.538,4.357,3.697,3.035,3.881],[2.896,2.958,0.826,0.678,1.802,0.825],[1.423,1.154,1.884,3.063,3.992,3.001],[3.389,3.692,2.134,3.7,4.094,4.75],[2.75,3.546,3.742,3.853,3.204,5.14],[3.966,2.911,2.755,2.152,3.222,1.657],[2.267,1.875,2.087,1.343,3.21,3.064],[4.436,4.095,5.016,4.363,3.93,4.141],[-0.224,1.681,0.508,1.922,1.822,2.534],[2.844,2.896,3.813,4.436,2.472,3.68],[2.548,3.279,1.79,2.175,1.88,1.092],[2.624,2.491,2.819,3.493,3.617,2.98],[3.027,3.869,2.073,2.693,2.873,3.391],[2.524,3.183,1.987,3.333,2.888,3.225]],[1,1,1,2,2,2],[[1,2]])

### Multivariate analysis

`pca` — Reduce numeric variables to principal components. Rows: observations; columns: variables. Set component count and standardization 1/0; reports variance, scores and loadings.
Example: pca([[1,2],[2,1],[3,4],[4,3],[5,7]],2,1)

`discriminantanalysis` — Classify using LDA pooled or QDA group-specific covariance. Columns: features, class; priors: empirical/equal. Optional fourth argument supplies new feature rows.
Example: discriminantanalysis([[1,2,1],[2,1,1],[1,1,1],[2,3,1],[4,5,2],[5,4,2],[4,4,2],[5,6,2]],lda,empirical)

`kmeans` — Group observations by numeric-feature similarity. Input: feature rows, k and seed. Euclidean distance on original scales; standardize features as needed.
Example: kmeans([[1,1],[1,2],[2,1],[8,8],[8,9],[9,8]],2,0)

`hcluster` — Agglomerative hierarchical clustering. Set group count, single/complete/average/ward linkage and standardization 1/0. Reports a dendrogram and group assignments.
Example: hcluster([[1,1],[1,2],[2,1],[8,8],[8,9],[9,8]],2,ward,1)

### Time series & forecasting

`arima` — Forecast a complete, equally spaced series in time order. Set [p,d,q], horizon and level. auto selects intercept/drift by AICc at fixed orders. Optional dates; reports forecasts, conditional prediction intervals and residual checks.
Example: arima([12,15,14,18,13,17,16,21,15,19,18,24,17,22,20,27,19,24,23,30,21,27,25,33,24,29,28,36,26,32,30,39],[1,1,0],12,0.95,auto)

`sarima` — Seasonal ARIMA forecast. Enter a complete, equally spaced series spanning at least two seasons; set [p,d,q], seasonal [P,D,Q,s], horizon and level. Optional dates; reports conditional prediction intervals and residual checks.
Example: sarima([12,15,14,18,13,17,16,21,15,19,18,24,17,22,20,27,19,24,23,30,21,27,25,33,24,29,28,36,26,32,30,39],[1,0,0],[0,1,1,4],8,0.95,auto)

### Survival analysis

`survivalanalysis` — Kaplan–Meier curves, log-rank and optional Cox regression. Columns: time, event (1=event, 0=censored), group, optional predictors; Cox 0/1.
Example: survivalanalysis([[1,1,1],[2,1,2],[3,0,1],[4,1,2],[5,1,1],[6,0,2],[7,1,2],[8,1,1]],0,efron,-1,1)

`kaplanmeier` — Estimate survival with censoring. Columns: time, event (1=event, 0=censored); set confidence level.
Example: kaplanmeier([[1,1],[2,0],[3,1],[4,1],[5,0],[6,1]],0.95)

`logrank` — Compare survival between two groups. Input: two time/event tables, or current-data columns time, event, group.
Example: logrank([[1,1],[3,1],[4,0],[6,1]],[[2,0],[4,1],[5,1],[7,0]])

`cox` — Relate predictors to event hazard under proportional hazards. Columns: time, event 0/1, predictors. Ties: efron / breslow; optional entry-time column and PH check.
Example: cox([[1,1,0],[2,1,1],[3,0,0],[4,1,1],[5,1,0],[6,0,1],[7,1,1],[8,1,0]],efron,-1,1)

`parametricsurvival` — Weibull, exponential or lognormal AFT survival model. Rows: positive time, event 0/1, optional predictors and delayed entry. Reports time ratios, event-time quantiles and survival probabilities.
Example: parametricsurvival([[1,1,0],[2,1,1],[3,0,0],[4,1,1],[5,1,0],[6,0,1],[7,1,0],[8,1,1],[10,0,0],[12,1,1],[14,1,0],[17,0,1]],weibull,0.95,-1,6)

### Power & sample size

`testpower` — Power for a t-test design. Input: Cohen d, n, alpha, independent / paired / onesample and two / greater / less. n is per group or the number of pairs.
Example: testpower(0.5,64,0.05,independent)

`samplesize` — Sample size for a target t-test power. Input: Cohen d, target power, alpha, design and alternative. Returns n per group or the number of pairs.
Example: samplesize(0.5,0.8,0.05,independent)

`designpower` — Power for fixed-sample z, proportion, two-proportion or variance-ratio designs. Set design, effect, n, alpha, direction and reference proportion; two-group n is per group.
Example: designpower(z,0.5,64,0.05,two,0.5)

`designsize` — Sample size for the same designs as designpower. Replace n with target power; reports minimum n, total n and achieved power.
Example: designsize(z,0.5,0.8,0.05,two,0.5)
