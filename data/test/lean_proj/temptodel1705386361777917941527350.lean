import data.real.basic
import data.nat.factorial.basic

theorem n_less_2_pow_n
(n : ℕ)
(h₀ : 1 ≤ n) :
n < 2^n :=
begin
induction n with d hd,
exact one_pos,
apply nat.lt_of_succ_lt_succ,
apply nat.succ_lt_succ,
apply nat.lt_of_succ_le,
end