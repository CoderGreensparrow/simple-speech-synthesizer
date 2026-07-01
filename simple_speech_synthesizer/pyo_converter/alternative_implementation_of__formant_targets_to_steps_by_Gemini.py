"""
This may never be used, but just in case I need to switch out my sketchy code
"""


def _formant_targets_to_steps(formant_targets: FormantTargets, input_duration: float) -> tuple[
    list[pyo.Linseg], list[pyo.Linseg]]:
    """
    Converts the FormantTargets to step function control signal lists.
    Specifically, 2 control signal lists: a formant_freq list and a formant_importance_list.
    """
    if not formant_targets.ts:
        return [], []

    # 1. Dynamically find the maximum number of formants
    max_num_formants = max(len(points) for points in formant_targets.vs)

    freq_steps = [[] for _ in range(max_num_formants)]
    amp_steps = [[] for _ in range(max_num_formants)]

    PLACEHOLDER_FREQ = 500.0  # Standard neutral fallback if F5 never existed before fading in

    # 2. Sequentially build the timelines
    for i in range(len(formant_targets.ts)):
        t = formant_targets.ts[i]
        current_vs = formant_targets.vs[i]

        # Calculate the boundary for this specific step
        next_t = formant_targets.ts[i + 1] if i + 1 < len(formant_targets.ts) else input_duration
        mid_t = t + ((next_t - t) / 2.0)

        for f_idx in range(max_num_formants):
            is_active_now = f_idx < len(current_vs)

            if is_active_now:
                # NORMAL BEHAVIOR: Hold target frequency and full importance up to next_t
                target_freq = current_vs[f_idx]
                freq_steps[f_idx].extend([(t, target_freq), (next_t, target_freq)])
                amp_steps[f_idx].extend([(t, 1.0), (next_t, 1.0)])
            else:
                # GHOST BEHAVIOR: Importance is 0.
                prev_freq = freq_steps[f_idx][-1][1] if freq_steps[f_idx] else PLACEHOLDER_FREQ

                # Check if it phases back into existence in the next cycle
                is_active_next = (i + 1 < len(formant_targets.ts)) and (f_idx < len(formant_targets.vs[i + 1]))

                if is_active_next:
                    future_freq = formant_targets.vs[i + 1][f_idx]
                    # Hold old freq until mid, snap to new freq, hold to next_t
                    freq_steps[f_idx].extend(
                        [(t, prev_freq), (mid_t, prev_freq), (mid_t, future_freq), (next_t, future_freq)])
                    amp_steps[f_idx].extend([(t, 0.0), (next_t, 0.0)])
                else:
                    # Stays dead. Hold previous frequency flat.
                    freq_steps[f_idx].extend([(t, prev_freq), (next_t, prev_freq)])
                    amp_steps[f_idx].extend([(t, 0.0), (next_t, 0.0)])

    _DEBUG_RETURN = True
    if _DEBUG_RETURN:
        return freq_steps, amp_steps

    return ([pyo.Linseg(pts) for pts in freq_steps], [pyo.Linseg(pts) for pts in amp_steps])