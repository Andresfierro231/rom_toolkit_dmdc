# Ethan Weekend Queue

This directory records the weekend queue I submitted on `2026-06-05`.

## Submitted jobs

- `3211196` `jadyn_salt2_cont`: dependent Salt 2 follow-on chunk after `3202708`
- `3211197` `ethan_s1j_cont`: dependent Salt 1 Jin follow-on chunk after `3210761`
- `3211199` `ethan_s1k_cont`: dependent Salt 1 Kirst follow-on chunk after `3210760`
- `3211200` `ethan_s4j_cont`: dependent Salt 4 Jin follow-on chunk after `3210231`
- `3211198` `render_salt3_jin`: independent static Salt 3 Jin render job
- `3211201` `render_water1_lam`: independent static Water 1 laminar render job
- `3211208` `zeroadv_pilot3`: dependent pilot transport refresh after the Salt 1 and Salt 4 follow-on chunks

## Why these and not more

- These follow the latest Ethan runtime policy: keep Salt 2 primary, continue targeted Salt 1 tests, and avoid a blanket continuation campaign.
- I did not queue Salt 3 continuation, Salt 4 Kirst continuation, or water continuations because the current runtime notes still classify those as lower-value than the active/targeted lanes.
- I staged but did not submit additional dynamic read/write analysis against live running cases beyond the queued zero-advance refresh, because the latest active salt writes can still alternate between readable and malformed reconstructed `T` states.
