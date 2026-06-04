from problemform.models import ProblemState


def render_markdown(state: ProblemState) -> str:
    sections: list[str] = []

    if state.final_prompt:
        sections.append("## Final prompt\n\n```\n" + state.final_prompt + "\n```")

    if state.stated_objective or state.inferred_objective:
        lines = ["## Objective"]
        if state.stated_objective:
            lines.append(f"- **Stated:** {state.stated_objective}")
        if state.inferred_objective:
            lines.append(f"- **Inferred:** {state.inferred_objective}")
        sections.append("\n".join(lines))

    if state.assumptions:
        lines = ["## Assumptions"]
        for a in state.assumptions:
            lines.append(f"- _({a.assumption_type}, {a.importance})_ {a.assumption}")
        sections.append("\n".join(lines))

    if state.information_gaps:
        lines = ["## Information gaps"]
        for g in state.information_gaps:
            lines.append(
                f"- _({g.importance}, {g.acquisition_method})_ {g.gap}"
            )
        sections.append("\n".join(lines))

    if state.expert_panel_perspectives:
        lines = ["## Expert panel"]
        for p in state.expert_panel_perspectives:
            lines.append(f"- **{p.perspective_name}:** {p.question}")
        sections.append("\n".join(lines))

    if state.alternative_framings:
        lines = ["## Alternative framings"]
        for i, f in enumerate(state.alternative_framings, start=1):
            lines.append(f"{i}. {f.framing}")
        sections.append("\n".join(lines))

    if state.meta_questions:
        lines = ["## Meta questions"]
        for i, m in enumerate(state.meta_questions, start=1):
            lines.append(f"{i}. {m.question}")
        sections.append("\n".join(lines))

    if state.prompt_versions:
        lines = ["## Prompt history"]
        for pv in state.prompt_versions[-3:]:
            desc = pv.revision.description if pv.revision else "initial input"
            lines.append(f"- **v{pv.version}** — {desc}")
        sections.append("\n".join(lines))

    lines = [f"## Convergence", "", f"**Status:** {state.convergence_status}"]
    lc = state.last_convergence
    if lc is not None:
        if lc.prompt_delta_assessment:
            lines.append("")
            lines.append(f"**Prompt delta:** {lc.prompt_delta_assessment}")
        if lc.rationale:
            lines.append("")
            lines.append(f"**Rationale:** {lc.rationale}")
        if lc.remaining_opportunities:
            lines.append("")
            lines.append("_Remaining opportunities (informational only):_")
            for op in lc.remaining_opportunities:
                lines.append(f"- {op}")
    sections.append("\n".join(lines))

    return "\n\n".join(sections) + "\n"
