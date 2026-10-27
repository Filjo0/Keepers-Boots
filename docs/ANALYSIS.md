# Geometry models v0.1 and v0.2

## Purpose
A reproducible demonstration of option trade-offs. This model is not fitted to professional football, and does not estimate pass success or coaching optimality.

## Implemented calculation
For each ground pass from keeper K to target T:

- Route length L = Euclidean distance(K, T).
- At fraction f of the route: P(f) = K + f(T - K).
- Ball arrival = release_delay + preparation_delay + f * L / ball_speed. Preparation defaults to zero; nonzero preparation requires point-arrival-v0.2.
- Defender arrival = reaction_delay + distance(defender, P(f)) / defender_speed.
- Margin = defender arrival - ball arrival.
- Take the minimum margin over all opponents and sampled route points.
- Evaluate the endpoint combinations of declared ball speed, defender speed and reaction-delay ranges.

A negative margin indicates a reachable interception opportunity under a tested assumption set. It does not mean the defender will intercept.
A positive sampled margin describes the sampled model only; it does not guarantee completion.

The monotonic timing terms make parameter endpoints useful bounds within this simplified model. Spatial sampling is still approximate: test sensitivity to finer sampling before making stronger claims.

## Scenario 1 assumptions
- Release delay: 0.3 s.
- Short pass: 12-16 m/s.
- Wide pass: 16-20 m/s.
- Defender speed: 4.5-6.5 m/s after 0.15-0.35 s response delay.
- 1,001 equally spaced route samples.
- Players are points; routes are straight; constant speeds follow the delay.

A prior design calculation gave the short route negative margins and the wide route positive margins. The CLI recomputes all values from the complete generated fixture; treat its current output as the reproducible prototype evidence.

## Deliberate limitations
- No reach radius, acceleration limits, kicking execution uncertainty, collisions or ball friction.
- Aerial ball flight, jumping and duels are not modelled. Long clearance is returned as not_modelled.
- Global capability ranges are fictional assumptions, not estimates from player age, height, weight or reputation.
- This version declines when observations are stale.
- No direction-aware defender response or claimed true visual awareness.
- Numerical geometric separation is not an overall tactical score.

## Next modelling step
Before presenting an option as better supported, add reach/acceleration treatment or display those limitations prominently and limit the conclusion to this model.
Use parameter sensitivity and held-out scenario variations. Do not tune parameters to force a preferred story after seeing outcomes.

## Ranking policy
No universal ranking in v0.1. The UI may compare supported ground-route evidence and explain what each objective favours. An aerial option cannot be silently ranked last because it is unsupported.
Version and review any subsequent preference policy separately from geometry.

## Implementation
Owner: keepers_boots/analysis.py.
Boundary: analyse_snapshot accepts an immutable DecisionSnapshot, never a scenario package.

## Pressure and observation age

analyse_pressure uses the same frozen snapshot. It computes each defender's reaction plus distance to the keeper divided by declared speed, takes the earliest arrival per parameter combination, and compares this range with each action's release delay plus preparation. Scenario 2 adds a declared extra-touch delay; it does not simulate touch technique or control. Release before pressure is not pass completion.

Scenario 3's old opponent observation causes abstention. Its displayed uncertainty radius is age in seconds times the declared maximum defender speed, in any direction. This is an illustrative reachable region, not a calibrated confidence distribution or proof that route order reverses. Hidden continuations do not change the available observation, region or assessment. Scenario 1 retains its v0.1 frozen definition.

## Deterministic comparison facts

Signed margin ordering is computed in code, not inferred by an agent. For identical ground routes and ball-speed grids, preparation delay shifts every tested margin by the same amount; matched cases remain comparable even when the aggregate uncertainty ranges overlap. Scenario 2 therefore gives release-short a larger signed margin than take-touch by the declared preparation difference.

For different routes, a relation is reported only when their computed parameter-extrema ranges are separated. Otherwise the extrema comparison remains unresolved. These facts carry evidence IDs, their basis and explicit larger/smaller option IDs. They are timing relations, not pass-success probabilities or overall action rankings. A narrow claim guard additionally rejects explicit reversed comparisons using option IDs; semantic review remains necessary for other wording.
